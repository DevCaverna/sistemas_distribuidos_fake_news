import copy

import pytest

from core.automato import (
    ESPALHADOR,
    IGNORANTE,
    INATIVO,
    _contar_vizinhos_espalhadores,
    _tem_influenciador_espalhador_5x5,
    calcular_geracao,
    contar_estados,
)


# ---------------------------------------------------------------------------
# _contar_vizinhos_espalhadores
# ---------------------------------------------------------------------------

class TestContarVizinhosEspalhadores:
    def test_sem_espalhadores(self):
        m = [[IGNORANTE] * 3 for _ in range(3)]
        assert _contar_vizinhos_espalhadores(m, 1, 1, 3, 3) == 0

    def test_todos_oito_vizinhos_espalhadores(self):
        m = [
            [ESPALHADOR, ESPALHADOR, ESPALHADOR],
            [ESPALHADOR, IGNORANTE,  ESPALHADOR],
            [ESPALHADOR, ESPALHADOR, ESPALHADOR],
        ]
        assert _contar_vizinhos_espalhadores(m, 1, 1, 3, 3) == 8

    def test_celula_no_canto_tem_tres_vizinhos(self):
        # (0,0) com vizinhos (0,1), (1,0) e (1,1) todos ESPALHADOR
        m = [
            [IGNORANTE, ESPALHADOR, IGNORANTE],
            [ESPALHADOR, ESPALHADOR, IGNORANTE],
            [IGNORANTE, IGNORANTE,  IGNORANTE],
        ]
        assert _contar_vizinhos_espalhadores(m, 0, 0, 3, 3) == 3

    def test_celula_na_borda_lateral(self):
        # (1,0): vizinhos possíveis (0,0), (0,1), (1,1), (2,0), (2,1)
        m = [
            [ESPALHADOR, ESPALHADOR, IGNORANTE],
            [IGNORANTE,  IGNORANTE,  IGNORANTE],
            [ESPALHADOR, IGNORANTE,  IGNORANTE],
        ]
        # (0,0)=E, (0,1)=E, (1,1)=0, (2,0)=E, (2,1)=0 → 3
        assert _contar_vizinhos_espalhadores(m, 1, 0, 3, 3) == 3

    def test_nao_conta_celula_propria(self):
        # célula alvo é ESPALHADOR, mas ela não deve se contar
        m = [
            [IGNORANTE, IGNORANTE, IGNORANTE],
            [IGNORANTE, ESPALHADOR, IGNORANTE],
            [IGNORANTE, IGNORANTE, IGNORANTE],
        ]
        assert _contar_vizinhos_espalhadores(m, 1, 1, 3, 3) == 0


# ---------------------------------------------------------------------------
# _tem_influenciador_espalhador_5x5
# ---------------------------------------------------------------------------

class TestTemInfluenciadorEspalhador5x5:
    def test_influenciador_presente(self):
        # 7x7 matrix, influenciador em (0,0) que é ESPALHADOR
        m = [[IGNORANTE] * 7 for _ in range(7)]
        m[0][0] = ESPALHADOR
        mapa = {(0, 0)}  # offset_global=0
        # célula central (3,3): (0,0) está a 3 linhas acima = fora do raio 5x5 (di=-3)
        # Vamos verificar uma célula mais próxima: (2,2)
        # raio 5x5: di in (-2,-1,0,1,2), dj in (-2,-1,0,1,2)
        # (0,0) em relação a (2,2): di=-2, dj=-2 → dentro do raio
        assert _tem_influenciador_espalhador_5x5(m, 2, 2, 7, 7, mapa, 0) is True

    def test_influenciador_ausente_nenhum_mapa(self):
        m = [[ESPALHADOR] * 5 for _ in range(5)]
        mapa = set()  # nenhum influenciador
        assert _tem_influenciador_espalhador_5x5(m, 2, 2, 5, 5, mapa, 0) is False

    def test_influenciador_existe_mas_nao_espalhador(self):
        m = [[IGNORANTE] * 5 for _ in range(5)]
        m[0][0] = INATIVO  # influenciador mas INATIVO, não ESPALHADOR
        mapa = {(0, 0)}
        assert _tem_influenciador_espalhador_5x5(m, 2, 2, 5, 5, mapa, 0) is False

    def test_influenciador_fora_do_raio_5x5(self):
        m = [[IGNORANTE] * 9 for _ in range(9)]
        m[0][0] = ESPALHADOR
        mapa = {(0, 0)}
        # (0,0) em relação a (4,4): di=-4, dj=-4 → fora do raio ±2
        assert _tem_influenciador_espalhador_5x5(m, 4, 4, 9, 9, mapa, 0) is False

    def test_com_offset_global(self):
        # slice começa na linha 5 global; influenciador está em (5, 0) global
        # localmente: linha 0 do slice
        m = [[ESPALHADOR, IGNORANTE], [IGNORANTE, IGNORANTE]]
        mapa = {(5, 0)}  # global
        # célula local (1, 1): em relação local a (0,0): di=-1, dj=-1 → dentro do raio
        # linha global de (0,0) = 0 + offset_global(=5) = 5 → está no mapa
        assert _tem_influenciador_espalhador_5x5(m, 1, 1, 2, 2, mapa, 5) is True


# ---------------------------------------------------------------------------
# calcular_geracao
# ---------------------------------------------------------------------------

class TestCalcularGeracao:
    def test_espalhador_vira_inativo(self):
        fatia = [[ESPALHADOR]]
        resultado = calcular_geracao(fatia)
        assert resultado[0][0] == INATIVO

    def test_inativo_permanece_inativo(self):
        fatia = [[INATIVO]]
        resultado = calcular_geracao(fatia)
        assert resultado[0][0] == INATIVO

    def test_ignorante_sem_vizinhos_permanece_ignorante(self):
        fatia = [[IGNORANTE]]
        resultado = calcular_geracao(fatia)
        assert resultado[0][0] == IGNORANTE

    def test_ignorante_com_vizinhos_suficientes_vira_espalhador(self):
        # Linha: E I E → célula do meio tem 2 vizinhos espalhadores, limiar=2
        fatia = [[ESPALHADOR, IGNORANTE, ESPALHADOR]]
        resultado = calcular_geracao(fatia, limiar=2)
        assert resultado[0][1] == ESPALHADOR

    def test_ignorante_abaixo_do_limiar_permanece_ignorante(self):
        # Linha: E I I → célula do meio tem 1 vizinho, limiar=2
        fatia = [[ESPALHADOR, IGNORANTE, IGNORANTE]]
        resultado = calcular_geracao(fatia, limiar=2)
        assert resultado[0][1] == IGNORANTE

    def test_ghost_rows_influenciam_borda_topo(self):
        # Fatia tem 1 linha: [I, I]
        # Ghost topo: [E, E] — 2 espalhadores acima
        # Ghost base: [E, E] — 2 espalhadores abaixo
        # Célula (0,0) vê: ghost_topo[0]=E, ghost_topo[1]=E, ghost_base[0]=E, ghost_base[1]=E, (0,1)=I
        # Total = 4 espalhadores → limiar=2 → vira ESPALHADOR
        fatia = [[IGNORANTE, IGNORANTE]]
        ghost_topo = [ESPALHADOR, ESPALHADOR]
        ghost_base = [ESPALHADOR, ESPALHADOR]
        resultado = calcular_geracao(fatia, borda_topo=ghost_topo, borda_base=ghost_base, limiar=2)
        assert resultado[0][0] == ESPALHADOR

    def test_sem_espalhadores_nada_muda(self):
        fatia = [[IGNORANTE, IGNORANTE], [IGNORANTE, IGNORANTE]]
        resultado = calcular_geracao(fatia)
        assert resultado == [[IGNORANTE, IGNORANTE], [IGNORANTE, IGNORANTE]]

    def test_funcao_e_pura_nao_muta_entrada(self):
        fatia = [[ESPALHADOR, IGNORANTE], [IGNORANTE, INATIVO]]
        original = copy.deepcopy(fatia)
        calcular_geracao(fatia)
        assert fatia == original

    def test_dimensoes_mantidas(self):
        fatia = [[IGNORANTE] * 5 for _ in range(4)]
        resultado = calcular_geracao(fatia)
        assert len(resultado) == 4
        assert all(len(row) == 5 for row in resultado)


# ---------------------------------------------------------------------------
# contar_estados
# ---------------------------------------------------------------------------

class TestContarEstados:
    def test_todos_ignorantes(self):
        m = [[IGNORANTE] * 3 for _ in range(3)]
        c = contar_estados(m)
        assert c[IGNORANTE] == 9
        assert c[ESPALHADOR] == 0
        assert c[INATIVO] == 0

    def test_contagem_misturada(self):
        m = [[IGNORANTE, ESPALHADOR], [INATIVO, ESPALHADOR]]
        c = contar_estados(m)
        assert c[IGNORANTE] == 1
        assert c[ESPALHADOR] == 2
        assert c[INATIVO] == 1

    def test_todos_espalhadores(self):
        m = [[ESPALHADOR] * 2 for _ in range(2)]
        c = contar_estados(m)
        assert c[ESPALHADOR] == 4
        assert c[IGNORANTE] == 0

    def test_soma_total_igual_celulas(self):
        m = [[IGNORANTE, ESPALHADOR, INATIVO] for _ in range(4)]
        c = contar_estados(m)
        assert c[IGNORANTE] + c[ESPALHADOR] + c[INATIVO] == 12
