import sys
import threading
import time

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
                 limiar, semente, usar_influenciadores=True,
                 usar_midia=True, geracao_midia=5, prob_sensacionalista=0.08,
                 timeout_descoberta=3):
        self.linhas = linhas
        self.colunas = colunas
        self.geracoes = geracoes
        self.limiar = limiar
        self.timeout_descoberta = timeout_descoberta

        self.matriz = criar_matriz(linhas, colunas, percentual_espalhadores, semente)
        self.num_workers = 0
        self.fatias = None
        self._offsets = None

        self.mapa_influenciadores = None
        if usar_influenciadores:
            self.mapa_influenciadores = criar_mapa_influenciadores(linhas, colunas)

        self.usar_midia = usar_midia
        self.geracao_midia = geracao_midia
        self.prob_sensacionalista = prob_sensacionalista

        self._workers_registrados = 0
        self._lock_registro = threading.Lock()
        self._inicializado = False
        self._evento_inicio = threading.Event()

        self._cond = threading.Condition()
        self._bordas = {}
        self._esp_por_worker = {}
        self._ghosts = {}
        self._geracao_pronta = -1
        self._leitores = 0
        self._terminar = False

        self._fatias_finais = []
        self._lock_resultado = threading.Lock()
        self._evento_resultado = threading.Event()

        self._metricas_workers = []
        self._lock_metricas = threading.Lock()
        self._evento_metricas = threading.Event()

        self.bytes_trafegados = 0
        self._lock_bytes = threading.Lock()

        self._configs = {}

    def registrar_worker(self):
        with self._lock_registro:
            if self._inicializado:
                raise RuntimeError("Registro fechado")
            wid = self._workers_registrados
            self._workers_registrados += 1
            return {"worker_id": wid}

    def aguardar_inicio(self, worker_id):
        self._evento_inicio.wait()
        if worker_id not in self._configs:
            raise RuntimeError(
                f"Worker {worker_id} registrou-se apos a inicializacao"
            )
        return self._configs[worker_id]

    def inicializar(self, timeout=None):
        timeout = timeout if timeout is not None else self.timeout_descoberta
        deadline = time.time() + timeout
        while time.time() < deadline and self._workers_registrados == 0:
            time.sleep(0.1)

        if timeout > 0 and self._workers_registrados > 0:
            time.sleep(0.5)

        with self._lock_registro:
            self.num_workers = self._workers_registrados
            self._inicializado = True

        if self.num_workers == 0:
            raise RuntimeError("Nenhum worker registrado")

        self.fatias = fatiar_matriz(self.matriz, self.num_workers)
        self._offsets = calcular_offsets(self.linhas, self.num_workers)

        self._fatias_finais = [None] * self.num_workers
        self._metricas_workers = [None] * self.num_workers

        for wid in range(self.num_workers):
            fatia = self.fatias[wid]

            ghost_topo = self.fatias[wid - 1][-1] if wid > 0 else None
            ghost_base = self.fatias[wid + 1][0] if wid < self.num_workers - 1 else None

            mapa_serial = None
            if self.mapa_influenciadores is not None:
                mapa_serial = list(self.mapa_influenciadores)

            self._configs[wid] = {
                "worker_id": wid,
                "fatia": fatia,
                "geracoes": self.geracoes,
                "limiar": self.limiar,
                "num_workers": self.num_workers,
                "ghost_topo_inicial": ghost_topo,
                "ghost_base_inicial": ghost_base,
                "offset_global": self._offsets[wid],
                "mapa_influenciadores": mapa_serial,
                "usar_midia": self.usar_midia,
                "geracao_midia": self.geracao_midia,
                "prob_sensacionalista": self.prob_sensacionalista,
            }

        self._evento_inicio.set()
        return self.num_workers

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

    def enviar_metricas(self, worker_id, metricas):
        with self._lock_metricas:
            self._metricas_workers[worker_id] = metricas
            if all(m is not None for m in self._metricas_workers):
                self._evento_metricas.set()

    def aguardar_metricas(self):
        self._evento_metricas.wait()
        return self._metricas_workers
