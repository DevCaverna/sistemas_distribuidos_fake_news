import sys
import threading

from core.utils import criar_matriz, fatiar_matriz, remontar_matriz


class MestreParalelo:
    """Mestre que coordena workers executando em threads na mesma JVM.

    A API e comportamento seguem a versão distribuída, mas todas as chamadas
    são métodos locais e a comunicação é feita por estruturas de sincronização
    (Condition / Lock) em memória.
    """

    def __init__(
        self,
        linhas,
        colunas,
        geracoes,
        percentual_espalhadores,
        limiar,
        semente,
        num_workers,
    ):
        self.linhas = linhas
        self.colunas = colunas
        self.geracoes = geracoes
        self.limiar = limiar
        self.num_workers = num_workers

        self.matriz = criar_matriz(linhas, colunas, percentual_espalhadores, semente)
        self.fatias = fatiar_matriz(self.matriz, num_workers)

        # sincronização da barreira
        self._cond = threading.Condition()
        self._bordas = {}
        self._esp_por_worker = {}
        self._ghosts = {}
        self._geracao_pronta = -1
        self._leitores = 0
        self._terminar = False

        # resultado final
        self._fatias_finais = [None] * num_workers
        self._lock_resultado = threading.Lock()
        self._evento_resultado = threading.Event()

        # métricas
        self.bytes_trafegados = 0
        self._lock_bytes = threading.Lock()

    def iniciar_workers(self):
        """Cria e inicia as threads workers. Retorna a lista de threads."""
        threads = []
        for wid in range(self.num_workers):
            fatia = self.fatias[wid]
            t = threading.Thread(
                target=self._worker_thread,
                args=(wid, fatia, self.geracoes, self.limiar),
                daemon=False,
            )
            threads.append(t)
            t.start()

        return threads

    def _worker_thread(self, worker_id, fatia, geracoes, limiar):
        # Lazy import to keep module-level dependencies small
        from core.automato import ESPALHADOR, calcular_geracao, contar_estados

        ghost_topo = None
        ghost_base = None

        for g in range(1, geracoes + 1):
            fatia = calcular_geracao(
                fatia, borda_topo=ghost_topo, borda_base=ghost_base, limiar=limiar
            )

            borda_topo = fatia[0]
            borda_base = fatia[-1]

            contagem = contar_estados(fatia)
            espalhadores = contagem[ESPALHADOR]

            # enviar bordas para o mestre (síncrono local)
            self.enviar_bordas(worker_id, g, borda_topo, borda_base, espalhadores)

            # obter ghosts (bloqueante até mestre calcular)
            resposta = self.obter_ghosts(worker_id, g)

            ghost_topo = resposta["ghost_topo"]
            ghost_base = resposta["ghost_base"]

            if resposta.get("terminar"):
                break

        # enviar resultado final
        self.enviar_resultado(worker_id, fatia)

    # --- API usada pelos workers (métodos sincronizados) -----------------
    def enviar_bordas(
        self, worker_id, geracao, borda_topo, borda_base, contagem_espalhadores
    ):
        tamanho = sys.getsizeof(borda_topo) + sys.getsizeof(borda_base)
        with self._lock_bytes:
            self.bytes_trafegados += tamanho

        with self._cond:
            self._bordas[worker_id] = (borda_topo, borda_base)
            self._esp_por_worker[worker_id] = contagem_espalhadores

            if len(self._bordas) == self.num_workers:
                self._calcular_ghosts()

                if sum(self._esp_por_worker.values()) == 0:
                    self._terminar = True

                # marca a geração pronta e libera leitores
                self._geracao_pronta = geracao
                self._leitores = self.num_workers
                self._cond.notify_all()

    def obter_ghosts(self, worker_id, geracao):
        with self._cond:
            while self._geracao_pronta < geracao:
                self._cond.wait()

            ghost_topo, ghost_base = self._ghosts.get(worker_id, (None, None))

            tamanho = sum(
                sys.getsizeof(g) for g in (ghost_topo, ghost_base) if g is not None
            )
            with self._lock_bytes:
                self.bytes_trafegados += tamanho

            self._leitores -= 1

            if self._leitores == 0:
                # limpar mapas para próxima geração
                self._bordas.clear()
                self._esp_por_worker.clear()
                self._ghosts.clear()
                # permitir que quem bloqueou em enviar_bordas siga
                self._cond.notify_all()

            return {
                "ghost_topo": ghost_topo,
                "ghost_base": ghost_base,
                "terminar": self._terminar,
            }

    def _calcular_ghosts(self):
        self._ghosts.clear()
        for wid in range(self.num_workers):
            ghost_topo = self._bordas[wid - 1][1] if wid > 0 else None
            ghost_base = (
                self._bordas[wid + 1][0] if wid < self.num_workers - 1 else None
            )
            self._ghosts[wid] = (ghost_topo, ghost_base)

    def enviar_resultado(self, worker_id, fatia_final):
        with self._lock_resultado:
            self._fatias_finais[worker_id] = fatia_final
            if all(f is not None for f in self._fatias_finais):
                self._evento_resultado.set()

    def aguardar_resultado(self):
        self._evento_resultado.wait()

    def obter_matriz_final(self):
        return remontar_matriz(self._fatias_finais)
