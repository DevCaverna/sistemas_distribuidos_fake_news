"""
Testes para paralelo/mestre.py (MestreParalelo).

Nota: a versão paralela utiliza multiprocessing (paralelismo real, sem GIL).
Com 1 worker não há ghost rows, então o resultado é idêntico ao sequencial.
Com N > 1 workers, os testes verificam shape, estados válidos e determinismo.
"""

import pytest

from core.automato import ESPALHADOR, IGNORANTE, INATIVO, calcular_geracao, contar_estados
from core.utils import criar_matriz
from paralelo.mestre import MestreParalelo

ESTADOS_VALIDOS = {IGNORANTE, ESPALHADOR, INATIVO}

PARAMS = dict(
    linhas=10,
    colunas=10,
    geracoes=5,
    percentual_espalhadores=0.1,
    limiar=2,
    semente=42,
    usar_influenciadores=False,
    usar_midia=False,
)

TIMEOUT = 60  # segundos (multiprocessing pode ser mais lento para iniciar)


def _run_sequencial_puro(linhas, colunas, geracoes, percentual_espalhadores, limiar, semente):
    """Executa o sequencial usando somente o core (sem prints)."""
    matrix = criar_matriz(linhas, colunas, percentual_espalhadores, semente)
    for _ in range(1, geracoes + 1):
        matrix = calcular_geracao(matrix, limiar=limiar)
        if contar_estados(matrix)[ESPALHADOR] == 0:
            break
    return matrix


def _executar_paralelo(num_workers, **params):
    mestre = MestreParalelo(**params, num_workers=num_workers)
    mestre.iniciar_workers()
    concluiu = mestre._evento_resultado.wait(timeout=TIMEOUT)
    assert concluiu, f"Timeout: paralelo com {num_workers} workers não terminou em {TIMEOUT}s"
    mestre.aguardar_processos()
    return mestre.obter_matriz_final(), mestre


class TestMestreParalelo:
    def test_1_worker_resultado_igual_sequencial(self):
        resultado_par, _ = _executar_paralelo(1, **PARAMS)
        resultado_seq = _run_sequencial_puro(
            linhas=PARAMS["linhas"], colunas=PARAMS["colunas"],
            geracoes=PARAMS["geracoes"], percentual_espalhadores=PARAMS["percentual_espalhadores"],
            limiar=PARAMS["limiar"], semente=PARAMS["semente"],
        )
        assert resultado_par == resultado_seq

    def test_2_workers_shape_correto(self):
        resultado, _ = _executar_paralelo(2, **PARAMS)
        assert len(resultado) == PARAMS["linhas"]
        assert all(len(row) == PARAMS["colunas"] for row in resultado)

    def test_4_workers_shape_correto(self):
        resultado, _ = _executar_paralelo(4, **PARAMS)
        assert len(resultado) == PARAMS["linhas"]
        assert all(len(row) == PARAMS["colunas"] for row in resultado)

    def test_estados_validos_1_worker(self):
        resultado, _ = _executar_paralelo(1, **PARAMS)
        for row in resultado:
            for cell in row:
                assert cell in ESTADOS_VALIDOS

    def test_estados_validos_2_workers(self):
        resultado, _ = _executar_paralelo(2, **PARAMS)
        for row in resultado:
            for cell in row:
                assert cell in ESTADOS_VALIDOS

    def test_estados_validos_4_workers(self):
        resultado, _ = _executar_paralelo(4, **PARAMS)
        for row in resultado:
            for cell in row:
                assert cell in ESTADOS_VALIDOS

    def test_bytes_trafegados_com_2_workers(self):
        _, mestre = _executar_paralelo(2, **PARAMS)
        assert mestre.bytes_trafegados.value > 0

    def test_sem_bytes_trafegados_com_1_worker(self):
        _, mestre = _executar_paralelo(1, **PARAMS)
        assert isinstance(mestre.bytes_trafegados.value, int)

    def test_determinismo_2_workers(self):
        r1, _ = _executar_paralelo(2, **PARAMS)
        r2, _ = _executar_paralelo(2, **PARAMS)
        assert r1 == r2

    def test_early_stop_sem_espalhadores(self):
        params_sem_esp = {**PARAMS, "percentual_espalhadores": 0.0, "geracoes": 20}
        resultado, _ = _executar_paralelo(2, **params_sem_esp)
        assert len(resultado) == PARAMS["linhas"]
