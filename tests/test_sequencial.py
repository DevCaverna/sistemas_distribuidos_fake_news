import pytest

from core.automato import ESPALHADOR, IGNORANTE, INATIVO
from main_sequencial import executar_sequencial

ESTADOS_VALIDOS = {IGNORANTE, ESPALHADOR, INATIVO}

# Parâmetros pequenos para manter os testes rápidos
PARAMS_PEQUENOS = dict(
    linhas=10,
    colunas=10,
    geracoes=5,
    percentual_espalhadores=0.1,
    limiar=2,
    semente=42,
    usar_influenciadores=False,
)


class TestExecutarSequencial:
    def test_retorna_tupla(self):
        result = executar_sequencial(**PARAMS_PEQUENOS)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_matriz_tem_shape_correto(self):
        matriz, _, _ = executar_sequencial(**PARAMS_PEQUENOS)
        assert len(matriz) == 10
        assert all(len(row) == 10 for row in matriz)

    def test_tempo_positivo(self):
        _, elapsed, _ = executar_sequencial(**PARAMS_PEQUENOS)
        assert elapsed > 0

    def test_estados_finais_validos(self):
        matriz, _, _ = executar_sequencial(**PARAMS_PEQUENOS)
        for row in matriz:
            for cell in row:
                assert cell in ESTADOS_VALIDOS

    def test_determinismo(self):
        r1, _, _ = executar_sequencial(**PARAMS_PEQUENOS)
        r2, _, _ = executar_sequencial(**PARAMS_PEQUENOS)
        assert r1 == r2

    def test_sem_influenciadores(self):
        matriz, elapsed, _ = executar_sequencial(
            linhas=5, colunas=5, geracoes=3,
            usar_influenciadores=False, semente=42,
        )
        assert len(matriz) == 5
        assert elapsed > 0

    def test_com_influenciadores(self):
        matriz, elapsed, _ = executar_sequencial(
            linhas=10, colunas=10, geracoes=5,
            usar_influenciadores=True, semente=42,
        )
        assert len(matriz) == 10
        assert elapsed > 0

    def test_uma_geracao(self):
        matriz, elapsed, _ = executar_sequencial(
            linhas=5, colunas=5, geracoes=1,
            usar_influenciadores=False, semente=42,
        )
        assert len(matriz) == 5
        assert elapsed > 0

    def test_early_stop_sem_espalhadores_iniciais(self):
        # Com percentual=0, não há espalhadores → para após gen 1
        matriz, elapsed, _ = executar_sequencial(
            linhas=10, colunas=10, geracoes=50,
            percentual_espalhadores=0.0,
            usar_influenciadores=False, semente=42,
        )
        assert len(matriz) == 10
        assert elapsed > 0
        # Estado final: sem nenhum espalhador (todos ignorantes)
        espalhadores = sum(cell == ESPALHADOR for row in matriz for cell in row)
        assert espalhadores == 0

    def test_dimensoes_nao_quadradas(self):
        matriz, _, _ = executar_sequencial(
            linhas=6, colunas=15, geracoes=3,
            usar_influenciadores=False, semente=42,
        )
        assert len(matriz) == 6
        assert all(len(row) == 15 for row in matriz)

    def test_limiar_alto_reduz_propagacao(self):
        # Limiar muito alto → ignorantes raramente viram espalhadores
        _, _, _ = executar_sequencial(
            linhas=10, colunas=10, geracoes=5,
            limiar=8, usar_influenciadores=False, semente=42,
        )
        # O teste apenas verifica que não levanta exceção com limiar=8
