import copy
from unittest.mock import patch

import pytest

from core.automato import (
    ESPALHADOR,
    IGNORANTE,
    INATIVO,
    INFLUENCIADOR_PROB_MIN,
    INFLUENCIADOR_PROB_MAX,
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


# ---------------------------------------------------------------------------
# _tem_influenciador_espalhador_5x5 — limites do raio e condição de skip
# ---------------------------------------------------------------------------

class TestTemInfluenciadorLimites:
    """Testes direcionados para os mutantes que sobreviveram na função
    _tem_influenciador_espalhador_5x5: range do raio e condição di==0 and dj==0."""

    def _matriz(self, linhas=7, colunas=7):
        return [[IGNORANTE] * colunas for _ in range(linhas)]

    # --- Exatamente no limite: di=±2, dj=±2 DEVE detectar ---

    def test_influenciador_exatamente_2_linhas_acima_detectado(self):
        m = self._matriz()
        m[1][3] = ESPALHADOR  # di=-2 em relação ao target (3,3)
        mapa = {(1, 3)}
        assert _tem_influenciador_espalhador_5x5(m, 3, 3, 7, 7, mapa, 0) is True

    def test_influenciador_exatamente_2_linhas_abaixo_detectado(self):
        m = self._matriz()
        m[5][3] = ESPALHADOR  # di=+2 em relação ao target (3,3)
        mapa = {(5, 3)}
        assert _tem_influenciador_espalhador_5x5(m, 3, 3, 7, 7, mapa, 0) is True

    def test_influenciador_exatamente_2_colunas_direita_detectado(self):
        m = self._matriz()
        m[3][5] = ESPALHADOR  # dj=+2 em relação ao target (3,3)
        mapa = {(3, 5)}
        assert _tem_influenciador_espalhador_5x5(m, 3, 3, 7, 7, mapa, 0) is True

    # --- Fora do limite: di=±3, dj=±3 NÃO deve detectar ---
    # Estes matam mutmut_6 (range -3..2), mutmut_7 (-2..3),
    # mutmut_13 (dj: -3..2) e mutmut_14 (dj: -2..3)

    def test_influenciador_3_linhas_acima_nao_detectado(self):
        # 10 linhas para ter espaço: target em (5,5), influenciador em (2,5) → di=-3
        m = [[IGNORANTE] * 10 for _ in range(10)]
        m[2][5] = ESPALHADOR
        mapa = {(2, 5)}
        assert _tem_influenciador_espalhador_5x5(m, 5, 5, 10, 10, mapa, 0) is False

    def test_influenciador_3_linhas_abaixo_nao_detectado(self):
        m = [[IGNORANTE] * 10 for _ in range(10)]
        m[8][5] = ESPALHADOR  # di=+3 de (5,5)
        mapa = {(8, 5)}
        assert _tem_influenciador_espalhador_5x5(m, 5, 5, 10, 10, mapa, 0) is False

    def test_influenciador_3_colunas_esquerda_nao_detectado(self):
        m = [[IGNORANTE] * 10 for _ in range(10)]
        m[5][2] = ESPALHADOR  # dj=-3 de (5,5)
        mapa = {(5, 2)}
        assert _tem_influenciador_espalhador_5x5(m, 5, 5, 10, 10, mapa, 0) is False

    def test_influenciador_3_colunas_direita_nao_detectado(self):
        m = [[IGNORANTE] * 10 for _ in range(10)]
        m[5][8] = ESPALHADOR  # dj=+3 de (5,5)
        mapa = {(5, 8)}
        assert _tem_influenciador_espalhador_5x5(m, 5, 5, 10, 10, mapa, 0) is False

    # --- Condição de skip: células na mesma linha/coluna que o target ---
    # Mata mutmut_15 (or), mutmut_18 (dj!=0), mutmut_19 (dj==1), mutmut_20 (break)

    def test_influenciador_mesma_linha_coluna_adjacente_detectado(self):
        # di=0, dj=+1 → NÃO deve ser pulado (a condição de skip é di==0 AND dj==0)
        m = self._matriz()
        m[3][4] = ESPALHADOR  # di=0, dj=+1 em relação ao target (3,3)
        mapa = {(3, 4)}
        assert _tem_influenciador_espalhador_5x5(m, 3, 3, 7, 7, mapa, 0) is True

    def test_influenciador_diretamente_abaixo_detectado(self):
        # di=+1, dj=0 → NÃO deve ser pulado
        # Mata mutmut_16 (di!=0 in AND) e mutmut_17 (di==1 in AND)
        m = self._matriz()
        m[4][3] = ESPALHADOR  # di=+1, dj=0 em relação ao target (3,3)
        mapa = {(4, 3)}
        assert _tem_influenciador_espalhador_5x5(m, 3, 3, 7, 7, mapa, 0) is True


# ---------------------------------------------------------------------------
# calcular_geracao — limiar padrão, offset padrão, bloco influenciador
# ---------------------------------------------------------------------------

class TestCalcularGeracaoInfluenciador:
    """Testes com mock do random para verificar o bloco de influenciadores.
    Matam mutmut_54-62 (prob=None, args de uniform, < vs <=, append errado)."""

    def _fatia_com_influenciador(self):
        """3x3: ESPALHADOR em (0,0) que é influenciador; único IGNORANTE em (2,2).
        Todos os outros são INATIVO para garantir que só (2,2) entra no caminho
        do influenciador — assim random.uniform é chamado exatamente 1 vez."""
        m = [[INATIVO] * 3 for _ in range(3)]
        m[0][0] = ESPALHADOR  # influenciador (di=-2, dj=-2 de (2,2))
        m[2][2] = IGNORANTE   # único target
        return m

    def test_default_limiar_2_ativa_espalhamento(self):
        # Usa o limiar padrão (sem passar limiar explícito)
        # Se o mutante mudar o default para 3, 2 vizinhos não bastam → permanece IGNORANTE
        fatia = [[ESPALHADOR, IGNORANTE, ESPALHADOR]]
        resultado = calcular_geracao(fatia)  # limiar padrão
        assert resultado[0][1] == ESPALHADOR

    @patch('random.random', return_value=0.0)
    @patch('random.uniform', return_value=0.5)
    def test_default_offset_global_zero(self, mock_uniform, mock_random):
        # Sem passar offset_global: influenciador em (0,1) deve ser encontrado
        # Mutmut_2: default offset_global=1 → linha_global=1 → (1,1) not in mapa → IGNORANTE
        m = [[IGNORANTE, ESPALHADOR]]
        mapa = {(0, 1)}
        resultado = calcular_geracao(m, mapa_influenciadores=mapa, limiar=10)
        assert resultado[0][0] == ESPALHADOR

    @patch('random.random', return_value=0.0)
    @patch('random.uniform', return_value=0.5)
    def test_influenciador_prob_alta_converte_ignorante(self, mock_uniform, mock_random):
        # random() = 0.0 < prob = 0.5 → ESPALHADOR
        # Mata mutmut_54 (prob=None), 60 (append(None) em vez de ESPALHADOR)
        m = self._fatia_com_influenciador()
        mapa = {(0, 0)}
        resultado = calcular_geracao(m, mapa_influenciadores=mapa, limiar=10)
        assert resultado[2][2] == ESPALHADOR

    @patch('random.random', return_value=0.0)
    @patch('random.uniform', return_value=0.5)
    def test_uniform_chamado_com_args_corretos(self, mock_uniform, mock_random):
        # Mata mutmut_55 (uniform(None, MAX)), 56 (uniform(MIN, None)), 57, 58
        # Único target IGNORANTE → uniform chamado exatamente 1 vez
        m = self._fatia_com_influenciador()
        mapa = {(0, 0)}
        calcular_geracao(m, mapa_influenciadores=mapa, limiar=10)
        mock_uniform.assert_called_once_with(INFLUENCIADOR_PROB_MIN, INFLUENCIADOR_PROB_MAX)

    @patch('random.random', return_value=0.9)
    @patch('random.uniform', return_value=0.5)
    def test_influenciador_prob_baixa_permanece_ignorante(self, mock_uniform, mock_random):
        # random() = 0.9 > prob = 0.5 → IGNORANTE
        # Mata mutmut_61 (append(None) no else em vez de IGNORANTE)
        m = self._fatia_com_influenciador()
        mapa = {(0, 0)}
        resultado = calcular_geracao(m, mapa_influenciadores=mapa, limiar=10)
        assert resultado[2][2] == IGNORANTE

    @patch('random.random', return_value=0.5)
    @patch('random.uniform', return_value=0.5)
    def test_influenciador_prob_igual_permanece_ignorante(self, mock_uniform, mock_random):
        # random() = 0.5, prob = 0.5 → 0.5 < 0.5 é False → IGNORANTE
        # Mata mutmut_59 (< vs <=): com <=, 0.5<=0.5 é True → ESPALHADOR (errado)
        m = self._fatia_com_influenciador()
        mapa = {(0, 0)}
        resultado = calcular_geracao(m, mapa_influenciadores=mapa, limiar=10)
        assert resultado[2][2] == IGNORANTE

    @patch('random.random', return_value=0.0)
    @patch('random.uniform', return_value=0.5)
    def test_offset_leitura_correto_com_ghost_topo(self, mock_uniform, mock_random):
        # Mata mutmut_17: offset_global - offset vs offset_global + offset
        # Fatia: 1 linha, 1 coluna, IGNORANTE
        # Ghost topo em global row 0 = ESPALHADOR; influenciador mapeado em (0,0)
        # offset_global=1 (slice começa na linha global 1), offset=1 (ghost existe)
        # Normal: offset_leitura_para_global = 1-1 = 0 → linha_global = 0+0 = 0 → detecta
        # Mutant: offset_leitura_para_global = 1+1 = 2 → linha_global = 0+2 = 2 → não detecta
        mapa = {(0, 0)}
        resultado = calcular_geracao(
            [[IGNORANTE]],
            borda_topo=[ESPALHADOR],
            mapa_influenciadores=mapa,
            limiar=10,
            offset_global=1,
        )
        assert resultado[0][0] == ESPALHADOR
