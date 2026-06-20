import time

import pytest

from core.automato import ESPALHADOR, IGNORANTE, INATIVO
from core.utils import (
    Cronometro,
    calcular_offsets,
    criar_mapa_influenciadores,
    criar_matriz,
    fatiar_matriz,
    imprimir_estatisticas,
    imprimir_grade,
    remontar_matriz,
)

ESTADOS_VALIDOS = {IGNORANTE, ESPALHADOR, INATIVO}


# ---------------------------------------------------------------------------
# criar_matriz
# ---------------------------------------------------------------------------

class TestCriarMatriz:
    def test_shape_correto(self):
        m = criar_matriz(5, 10)
        assert len(m) == 5
        assert all(len(row) == 10 for row in m)

    def test_estados_validos(self):
        m = criar_matriz(10, 10)
        for row in m:
            for cell in row:
                assert cell in ESTADOS_VALIDOS

    def test_reproducivel_mesma_semente(self):
        m1 = criar_matriz(10, 10, semente=42)
        m2 = criar_matriz(10, 10, semente=42)
        assert m1 == m2

    def test_diferente_com_sementes_diferentes(self):
        m1 = criar_matriz(10, 10, semente=1)
        m2 = criar_matriz(10, 10, semente=999)
        assert m1 != m2

    def test_percentual_zero_nenhum_espalhador(self):
        m = criar_matriz(10, 10, percentual_espalhadores=0.0)
        for row in m:
            for cell in row:
                assert cell == IGNORANTE

    def test_percentual_alto_gera_espalhadores(self):
        m = criar_matriz(10, 10, percentual_espalhadores=0.5)
        espalhadores = sum(cell == ESPALHADOR for row in m for cell in row)
        assert espalhadores > 0


# ---------------------------------------------------------------------------
# criar_mapa_influenciadores
# ---------------------------------------------------------------------------

class TestCriarMapaInfluenciadores:
    def test_retorna_set(self):
        mapa = criar_mapa_influenciadores(10, 10)
        assert isinstance(mapa, set)

    def test_elementos_sao_tuples(self):
        mapa = criar_mapa_influenciadores(10, 10)
        for elem in mapa:
            assert isinstance(elem, tuple)
            assert len(elem) == 2

    def test_count_aproximado(self):
        mapa = criar_mapa_influenciadores(100, 100, percentual=0.01)
        # 100*100*0.01 = 100 exatamente
        assert len(mapa) == 100

    def test_coords_dentro_dos_limites(self):
        linhas, colunas = 10, 15
        mapa = criar_mapa_influenciadores(linhas, colunas)
        for i, j in mapa:
            assert 0 <= i < linhas
            assert 0 <= j < colunas

    def test_reproducivel(self):
        m1 = criar_mapa_influenciadores(20, 20, semente_influenciadores=7)
        m2 = criar_mapa_influenciadores(20, 20, semente_influenciadores=7)
        assert m1 == m2


# ---------------------------------------------------------------------------
# fatiar_matriz
# ---------------------------------------------------------------------------

class TestFatiarMatriz:
    def test_divisao_exata(self):
        m = [[i] * 4 for i in range(6)]  # 6 linhas
        fatias = fatiar_matriz(m, 3)
        assert len(fatias) == 3
        assert all(len(f) == 2 for f in fatias)

    def test_ultima_fatia_absorve_resto(self):
        m = [[i] * 4 for i in range(5)]  # 5 linhas / 2 fatias
        fatias = fatiar_matriz(m, 2)
        assert len(fatias[0]) == 2   # 5 // 2
        assert len(fatias[1]) == 3   # restante

    def test_fatia_unica_igual_original(self):
        m = [[1, 2], [3, 4], [5, 6]]
        fatias = fatiar_matriz(m, 1)
        assert len(fatias) == 1
        assert fatias[0] == m

    def test_numero_de_fatias(self):
        m = [[0] * 3 for _ in range(10)]
        fatias = fatiar_matriz(m, 4)
        assert len(fatias) == 4

    def test_fatias_contiguas_cobrem_toda_a_matriz(self):
        m = [[i] * 3 for i in range(7)]
        fatias = fatiar_matriz(m, 3)
        remontada = [row for f in fatias for row in f]
        assert remontada == m


# ---------------------------------------------------------------------------
# calcular_offsets
# ---------------------------------------------------------------------------

class TestCalcularOffsets:
    def test_dois_workers(self):
        offsets = calcular_offsets(10, 2)
        assert offsets == [0, 5]

    def test_quatro_workers(self):
        offsets = calcular_offsets(12, 4)
        assert offsets == [0, 3, 6, 9]

    def test_um_worker(self):
        offsets = calcular_offsets(10, 1)
        assert offsets == [0]

    def test_primeira_offset_sempre_zero(self):
        for n in [2, 3, 5]:
            assert calcular_offsets(20, n)[0] == 0


# ---------------------------------------------------------------------------
# remontar_matriz
# ---------------------------------------------------------------------------

class TestRemontarMatriz:
    def test_fatiar_e_remontar_identidade(self):
        m = [[i * j for j in range(5)] for i in range(8)]
        fatias = fatiar_matriz(m, 4)
        assert remontar_matriz(fatias) == m

    def test_unica_fatia(self):
        m = [[1, 2], [3, 4]]
        assert remontar_matriz([m]) == m

    def test_numero_de_linhas_preservado(self):
        m = [[0] * 3 for _ in range(9)]
        fatias = fatiar_matriz(m, 3)
        remontada = remontar_matriz(fatias)
        assert len(remontada) == 9


# ---------------------------------------------------------------------------
# Cronometro
# ---------------------------------------------------------------------------

class TestCronometro:
    def test_elapsed_none_antes_de_iniciar(self):
        crono = Cronometro()
        assert crono.elapsed is None

    def test_elapsed_positivo_apos_parar(self):
        crono = Cronometro()
        crono.iniciar()
        time.sleep(0.01)
        crono.parar()
        assert crono.elapsed > 0

    def test_elapsed_disponivel_sem_parar(self):
        crono = Cronometro()
        crono.iniciar()
        # elapsed deve funcionar mesmo sem chamar parar
        assert crono.elapsed >= 0

    def test_reiniciar_reseta_medicao(self):
        crono = Cronometro()
        crono.iniciar()
        time.sleep(0.01)
        crono.parar()
        primeira = crono.elapsed

        crono.iniciar()
        time.sleep(0.005)
        crono.parar()
        segunda = crono.elapsed

        assert segunda < primeira


# ---------------------------------------------------------------------------
# imprimir_grade / imprimir_estatisticas (smoke tests)
# ---------------------------------------------------------------------------

class TestImpressao:
    def test_imprimir_grade_nao_levanta_excecao(self, matriz_pequena):
        imprimir_grade(matriz_pequena)

    def test_imprimir_grade_com_influenciadores(self, matriz_pequena):
        mapa = {(2, 2)}
        imprimir_grade(matriz_pequena, mapa_influenciadores=mapa)

    def test_imprimir_estatisticas_sem_total(self):
        contagem = {IGNORANTE: 5, ESPALHADOR: 3, INATIVO: 2}
        imprimir_estatisticas(contagem)

    def test_imprimir_estatisticas_com_total(self):
        contagem = {IGNORANTE: 5, ESPALHADOR: 3, INATIVO: 2}
        imprimir_estatisticas(contagem, geracao=1, total_celulas=10)

    def test_imprimir_estatisticas_sem_geracao(self):
        contagem = {IGNORANTE: 10, ESPALHADOR: 0, INATIVO: 0}
        imprimir_estatisticas(contagem, total_celulas=10)
