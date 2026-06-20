import pytest
from core.automato import IGNORANTE, ESPALHADOR, INATIVO


@pytest.fixture
def matriz_pequena():
    return [[IGNORANTE] * 5 for _ in range(5)]


@pytest.fixture
def matriz_com_espalhadores():
    m = [[IGNORANTE] * 5 for _ in range(5)]
    m[2][2] = ESPALHADOR
    return m


@pytest.fixture
def mapa_influenciadores_vazio():
    return set()
