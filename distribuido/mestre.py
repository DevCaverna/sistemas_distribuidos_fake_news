import sys
import threading

import Pyro5.api
import Pyro5.server

from core.automato import contar_estados, ESPALHADOR
from core.utils import (
    criar_matriz, criar_mapa_influenciadores,
    fatiar_matriz, remontar_matriz, calcular_offsets,
)


@Pyro5.api.expose
class MestreDistribuido:

    def __init__(self, linhas, colunas, geracoes, percentual_espalhadores,
                 limiar, semente, num_workers, usar_influenciadores=True):
        self.linhas = linhas
        self.colunas = colunas
        self.geracoes = geracoes
        self.limiar = limiar
        self.num_workers = num_workers

        self.matriz = criar_matriz(linhas, colunas, percentual_espalhadores, semente)
        self.fatias = fatiar_matriz(self.matriz, num_workers)
        self._offsets = calcular_offsets(linhas, num_workers)

        self.mapa_influenciadores = None
        if usar_influenciadores:
            self.mapa_influenciadores = criar_mapa_influenciadores(linhas, colunas)

        self._workers_registrados = 0
        self._lock_registro = threading.Lock()
        self._evento_todos = threading.Event()

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

    def registrar_worker(self):
        with self._lock_registro:
            wid = self._workers_registrados
            self._workers_registrados += 1

            fatia = self.fatias[wid]

            ghost_topo = self.fatias[wid - 1][-1] if wid > 0 else None
            ghost_base = self.fatias[wid + 1][0] if wid < self.num_workers - 1 else None

            influenciadores_serializavel = None
            if self.mapa_influenciadores is not None:
                influenciadores_serializavel = list(self.mapa_influenciadores)

            config = {
                "worker_id": wid,
                "fatia": fatia,
                "geracoes": self.geracoes,
                "limiar": self.limiar,
                "num_workers": self.num_workers,
                "ghost_topo_inicial": ghost_topo,
                "ghost_base_inicial": ghost_base,
                "offset_global": self._offsets[wid],
                "mapa_influenciadores": influenciadores_serializavel,
            }

            if self._workers_registrados == self.num_workers:
                self._evento_todos.set()

            return config

    def aguardar_workers(self):
        self._evento_todos.wait()

    def enviar_bordas(self, worker_id, geracao, borda_topo, borda_base,
                      contagem_espalhadores):
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

            tamanho = sum(sys.getsizeof(g) for g in (ghost_topo, ghost_base) if g is not None)
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
            ghost_base = self._bordas[wid + 1][0] if wid < self.num_workers - 1 else None
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
