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

    def test_percentual_padrao_eh_um_porcento(self):
        # Mata mutmut_1: default percentual=0.01 → 1.01 faria len=10000, não 100
        mapa = criar_mapa_influenciadores(100, 100)  # usa default percentual
        assert len(mapa) == 100

    def test_semente_padrao_eh_123(self):
        # Mata mutmut_2: default semente=123 → 124 daria resultado diferente
        m_padrao = criar_mapa_influenciadores(20, 20)
        m_explicito = criar_mapa_influenciadores(20, 20, semente_influenciadores=123)
        assert m_padrao == m_explicito


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

    def test_offsets_sao_inteiros(self):
        # Mata mutmut_2: // → / faria tamanho_base float → offsets com float
        offsets = calcular_offsets(7, 3)  # 7/3 = 2.333... como float
        assert all(isinstance(o, int) for o in offsets)


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

    def test_elapsed_estavel_apos_parar(self):
        # Mata mutmut parar: _fim = time.perf_counter() → None faz elapsed crescer
        crono = Cronometro()
        crono.iniciar()
        time.sleep(0.01)
        crono.parar()
        e1 = crono.elapsed
        time.sleep(0.01)
        e2 = crono.elapsed
        assert e1 == e2  # após parar, elapsed é fixo


# ---------------------------------------------------------------------------
# imprimir_grade
# ---------------------------------------------------------------------------

class TestImprimirGrade:
    def test_nao_levanta_excecao(self):
        m = [[IGNORANTE, ESPALHADOR], [INATIVO, IGNORANTE]]
        imprimir_grade(m)

    def test_simbolo_ignorante(self, capsys):
        imprimir_grade([[IGNORANTE]])
        assert "." in capsys.readouterr().out

    def test_simbolo_espalhador(self, capsys):
        imprimir_grade([[ESPALHADOR]])
        assert "E" in capsys.readouterr().out

    def test_simbolo_inativo(self, capsys):
        imprimir_grade([[INATIVO]])
        assert "N" in capsys.readouterr().out

    def test_celulas_separadas_por_espaco(self, capsys):
        # Mata mutmut_23: " ".join → "".join não teria espaço
        imprimir_grade([[IGNORANTE, ESPALHADOR]])
        out = capsys.readouterr().out
        assert ". E" in out  # separador espaço entre IGNORANTE e ESPALHADOR

    def test_influenciador_espalhador_usa_e_asterisco(self, capsys):
        # Mata mutmut_21: + "*" → + "" não teria asterisco
        imprimir_grade([[ESPALHADOR]], mapa_influenciadores={(0, 0)})
        out = capsys.readouterr().out
        assert "e*" in out

    def test_influenciador_ignorante_usa_ponto_asterisco(self, capsys):
        imprimir_grade([[IGNORANTE]], mapa_influenciadores={(0, 0)})
        out = capsys.readouterr().out
        assert ".*" in out

    def test_influenciador_usa_letra_minuscula(self, capsys):
        # Mata mutmut_20: simbolo.lower() → seria "E*" ao invés de "e*"
        imprimir_grade([[ESPALHADOR]], mapa_influenciadores={(0, 0)})
        out = capsys.readouterr().out
        assert "E*" not in out  # maiúscula não deve aparecer para influenciador
        assert "e*" in out

    def test_linha_em_branco_ao_final(self, capsys):
        # Mata mutmut_25: print() final ausente
        imprimir_grade([[IGNORANTE]])
        out = capsys.readouterr().out
        assert out.endswith("\n\n")  # linha do símbolo + linha em branco

    def test_grade_multiplas_linhas(self, capsys):
        m = [[IGNORANTE, ESPALHADOR], [INATIVO, IGNORANTE]]
        imprimir_grade(m)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert len(lines) == 2


# ---------------------------------------------------------------------------
# imprimir_estatisticas
# ---------------------------------------------------------------------------

class TestImprimirEstatisticas:
    def test_contem_rotulo_ignorantes(self, capsys):
        imprimir_estatisticas({IGNORANTE: 5, ESPALHADOR: 3, INATIVO: 2})
        assert "Ignorantes" in capsys.readouterr().out

    def test_contem_rotulo_espalhadores(self, capsys):
        imprimir_estatisticas({IGNORANTE: 5, ESPALHADOR: 3, INATIVO: 2})
        assert "Espalhadores" in capsys.readouterr().out

    def test_contem_rotulo_inativos(self, capsys):
        imprimir_estatisticas({IGNORANTE: 5, ESPALHADOR: 3, INATIVO: 2})
        assert "Inativos" in capsys.readouterr().out

    def test_contem_valor_ignorantes(self, capsys):
        imprimir_estatisticas({IGNORANTE: 50, ESPALHADOR: 30, INATIVO: 20})
        assert "50" in capsys.readouterr().out

    def test_contem_valor_espalhadores(self, capsys):
        imprimir_estatisticas({IGNORANTE: 50, ESPALHADOR: 30, INATIVO: 20})
        assert "30" in capsys.readouterr().out

    def test_contem_valor_inativos(self, capsys):
        imprimir_estatisticas({IGNORANTE: 50, ESPALHADOR: 30, INATIVO: 20})
        assert "20" in capsys.readouterr().out

    def test_geracao_formatada_3_digitos(self, capsys):
        # Mata mutmut_3: :03d → outros formatos
        imprimir_estatisticas({IGNORANTE: 0, ESPALHADOR: 0, INATIVO: 0}, geracao=7)
        assert "007" in capsys.readouterr().out

    def test_geracao_grande_nao_truncada(self, capsys):
        imprimir_estatisticas({IGNORANTE: 0, ESPALHADOR: 0, INATIVO: 0}, geracao=100)
        assert "100" in capsys.readouterr().out

    def test_sem_geracao_nao_tem_prefixo_geracao(self, capsys):
        imprimir_estatisticas({IGNORANTE: 10, ESPALHADOR: 0, INATIVO: 0})
        assert "Geração" not in capsys.readouterr().out

    def test_percentual_ignorantes(self, capsys):
        # Mata mutmut_9/10: / total_celulas * 100 → pct errada
        imprimir_estatisticas({IGNORANTE: 50, ESPALHADOR: 30, INATIVO: 20}, total_celulas=100)
        assert "50.0%" in capsys.readouterr().out

    def test_percentual_espalhadores(self, capsys):
        imprimir_estatisticas({IGNORANTE: 50, ESPALHADOR: 30, INATIVO: 20}, total_celulas=100)
        assert "30.0%" in capsys.readouterr().out

    def test_percentual_inativos(self, capsys):
        imprimir_estatisticas({IGNORANTE: 50, ESPALHADOR: 30, INATIVO: 20}, total_celulas=100)
        assert "20.0%" in capsys.readouterr().out

    def test_sem_geracao_prefixo_vazio(self, capsys):
        # Mata mutmut_3: else "" → else "XXXX" faz o prefixo aparecer indevidamente
        imprimir_estatisticas({IGNORANTE: 10, ESPALHADOR: 0, INATIVO: 0})
        out = capsys.readouterr().out
        assert out.startswith("Ignorantes:")

    def test_abreviacao_ig_formato_exato(self, capsys):
        # "Ig: " distingue da substring em "Ignorantes:" (que contém "Ig" mas não "Ig: ")
        # Mata mutmut_6 (XXIgXX), mutmut_7 (ig), mutmut_8 (IG)
        imprimir_estatisticas({IGNORANTE: 50, ESPALHADOR: 30, INATIVO: 20}, total_celulas=100)
        assert "Ig: " in capsys.readouterr().out

    def test_abreviacao_es_formato_exato(self, capsys):
        # Mata mutmut_9 (XXEsXX), mutmut_10 (es), mutmut_11 (ES)
        imprimir_estatisticas({IGNORANTE: 50, ESPALHADOR: 30, INATIVO: 20}, total_celulas=100)
        assert "Es: " in capsys.readouterr().out

    def test_abreviacao_in_formato_exato(self, capsys):
        # Mata mutmut_12 (XXInXX), mutmut_13 (in), mutmut_14 (IN)
        imprimir_estatisticas({IGNORANTE: 50, ESPALHADOR: 30, INATIVO: 20}, total_celulas=100)
        assert "In: " in capsys.readouterr().out

    def test_parentese_abre_antes_da_abreviacao(self, capsys):
        # Mata mutmut_23: "XX(XX" em vez de "(" como abertura da seção de %
        imprimir_estatisticas({IGNORANTE: 50, ESPALHADOR: 30, INATIVO: 20}, total_celulas=100)
        assert "(Ig" in capsys.readouterr().out

    def test_separador_interno_porcento_pipe(self, capsys):
        # Mata mutmut_25: "XX | XX".join em vez de " | ".join para partes_pct
        imprimir_estatisticas({IGNORANTE: 50, ESPALHADOR: 30, INATIVO: 20}, total_celulas=100)
        assert "% | " in capsys.readouterr().out

    def test_parentese_fecha_apos_porcento(self, capsys):
        # Mata mutmut_26: "XX)XX" em vez de ")" ao fechar a seção de %
        imprimir_estatisticas({IGNORANTE: 50, ESPALHADOR: 30, INATIVO: 20}, total_celulas=100)
        assert "%)" in capsys.readouterr().out

    def test_separador_externo_entre_secoes(self, capsys):
        # Mata mutmut_30: "XX | XX".join(partes) → "| Es" não aparece
        imprimir_estatisticas({IGNORANTE: 50, ESPALHADOR: 30, INATIVO: 20})
        assert "| Es" in capsys.readouterr().out

    def test_sem_total_celulas_sem_percentuais(self, capsys):
        imprimir_estatisticas({IGNORANTE: 50, ESPALHADOR: 30, INATIVO: 20})
        out = capsys.readouterr().out
        assert "%" not in out

    def test_geracao_com_total_exibe_ambos(self, capsys):
        imprimir_estatisticas(
            {IGNORANTE: 5, ESPALHADOR: 3, INATIVO: 2},
            geracao=1, total_celulas=10
        )
        out = capsys.readouterr().out
        assert "001" in out
        assert "%" in out
