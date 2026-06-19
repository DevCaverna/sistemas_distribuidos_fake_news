import sys
import threading

from core.utils import (
    criar_matriz, criar_mapa_influenciadores,
    fatiar_matriz, remontar_matriz, calcular_offsets,
)


class MestreParalelo:

    def __init__(
        self,
        linhas,
        colunas,
        geracoes,
        percentual_espalhadores,
        limiar,
        semente,
        num_workers,
        usar_influenciadores=True,
        usar_midia=True,
        geracao_midia=5,
        prob_sensacionalista=0.08,
    ):
        self.linhas = linhas
        self.colunas = colunas
        self.geracoes = geracoes
        self.limiar = limiar
        self.num_workers = num_workers
        self.usar_midia = usar_midia
        self.geracao_midia = geracao_midia
        self.prob_sensacionalista = prob_sensacionalista

        self.matriz = criar_matriz(linhas, colunas, percentual_espalhadores, semente)
        self.fatias = fatiar_matriz(self.matriz, num_workers)
        self._offsets = calcular_offsets(linhas, num_workers)

        self.mapa_influenciadores = None
        if usar_influenciadores:
            self.mapa_influenciadores = criar_mapa_influenciadores(linhas, colunas)

        self._cond = threading.Condition()
        self._bordas = {}
        self._esp_por_worker = {}
        self._ghosts = {}
        self._geracao_pronta = -1
        self._leitores = 0
        self._terminar = False

        self._fatias_finais = [None] * num_workers
        self._lock_resultado = threading.Lock()
        self._evento_resultado = threading.Event()

        self.bytes_trafegados = 0
        self._lock_bytes = threading.Lock()

    def iniciar_workers(self):
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
        from core.automato import (
            ESPALHADOR,
            aplicar_midia,
            calcular_geracao,
            contar_estados,
        )

        ghost_topo = None
        ghost_base = None
        offset_global = self._offsets[worker_id]
        mapa_influenciadores = self.mapa_influenciadores

        for g in range(1, geracoes + 1):
            fatia = calcular_geracao(
                fatia,
                borda_topo=ghost_topo,
                borda_base=ghost_base,
                limiar=limiar,
                mapa_influenciadores=mapa_influenciadores,
                offset_global=offset_global,
            )

            if self.usar_midia:
                fatia = aplicar_midia(fatia, media_ativa=g >= self.geracao_midia,
                                        prob_sensacionalista=self.prob_sensacionalista)

            borda_topo = fatia[0]
            borda_base = fatia[-1]

            contagem = contar_estados(fatia)
            espalhadores = contagem[ESPALHADOR]

            self.enviar_bordas(worker_id, g, borda_topo, borda_base, espalhadores)

            resposta = self.obter_ghosts(worker_id, g)

            ghost_topo = resposta["ghost_topo"]
            ghost_base = resposta["ghost_base"]

            if resposta.get("terminar"):
                break

        self.enviar_resultado(worker_id, fatia)

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
                self._bordas.clear()
                self._esp_por_worker.clear()
                self._ghosts.clear()
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
