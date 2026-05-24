"""
core/automato.py — Lógica pura do autômato celular de propagação de Fake News.

Este módulo contém SOMENTE a regra de transição de estados e funções auxiliares
de contagem. Ele é projetado para operar sobre **fatias** da matriz global,
recebendo bordas fantasma (ghost rows) como parâmetro, de modo que tanto a
versão paralela quanto a distribuída possam importá-lo sem modificações.

Estados:
    0 (IGNORANTE)  — Ainda não recebeu / não acredita na informação.
    1 (ESPALHADOR) — Acredita e compartilha a informação.
    2 (INATIVO)    — Recebeu a informação, mas não compartilha mais.

Regras de transição (por geração):
    - IGNORANTE  → ESPALHADOR se >= `limiar` vizinhos espalhadores (Moore).
    - ESPALHADOR → INATIVO    (sempre, na geração seguinte).
    - INATIVO    → INATIVO    (estado absorvente).

Referência do modelo: Vizinhança de Moore — 8 vizinhos adjacentes.
"""

# ---------------------------------------------------------------------------
# Constantes de estado
# ---------------------------------------------------------------------------
IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def _contar_vizinhos_espalhadores(matriz, i, j, num_linhas, num_colunas):
    """Conta vizinhos espalhadores usando vizinhança de Moore (8 vizinhos).

    Parâmetros
    ----------
    matriz : list[list[int]]
        Matriz (pode incluir ghost rows) de onde se lê o estado.
    i, j : int
        Coordenadas da célula alvo.
    num_linhas, num_colunas : int
        Dimensões válidas para checagem de limites.

    Retorna
    -------
    int
        Quantidade de vizinhos no estado ESPALHADOR.
    """
    total = 0
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ni, nj = i + di, j + dj
            if 0 <= ni < num_linhas and 0 <= nj < num_colunas:
                if matriz[ni][nj] == ESPALHADOR:
                    total += 1
    return total


# ---------------------------------------------------------------------------
# Função principal — cálculo de uma geração
# ---------------------------------------------------------------------------

def calcular_geracao(fatia, borda_topo=None, borda_base=None, limiar=2):
    """Calcula a próxima geração do autômato para uma fatia da matriz.

    Esta função é **pura**: não altera a fatia original. Ela constrói uma
    matriz de trabalho (com ghost rows, se fornecidas) e retorna uma nova
    fatia contendo apenas as linhas reais atualizadas.

    Parâmetros
    ----------
    fatia : list[list[int]]
        Submatriz com as linhas reais que este nó deve processar.
        Cada elemento é um inteiro representando o estado da célula.
    borda_topo : list[int] | None
        Linha fantasma superior (última linha real do nó vizinho acima).
        Se ``None``, a borda superior é tratada como inexistente (fronteira
        da matriz global).
    borda_base : list[int] | None
        Linha fantasma inferior (primeira linha real do nó vizinho abaixo).
        Se ``None``, a borda inferior é tratada como inexistente.
    limiar : int
        Quantidade mínima de vizinhos espalhadores para um IGNORANTE
        se tornar ESPALHADOR. Padrão: 2.

    Retorna
    -------
    list[list[int]]
        Nova fatia (mesma dimensão da entrada) com os estados atualizados.
    """
    num_linhas_reais = len(fatia)
    num_colunas = len(fatia[0])

    # ----- Montagem da matriz de leitura (com ghost rows) -----
    # A ideia é inserir as bordas fantasma como linhas extras para que a
    # contagem de vizinhos funcione naturalmente, sem ifs especiais.
    matriz_leitura = []

    if borda_topo is not None:
        matriz_leitura.append(borda_topo)
    matriz_leitura.extend(fatia)
    if borda_base is not None:
        matriz_leitura.append(borda_base)

    total_linhas_leitura = len(matriz_leitura)

    # Offset: a primeira linha real dentro de `matriz_leitura`.
    offset = 1 if borda_topo is not None else 0

    # ----- Cálculo da próxima geração (double-buffer) -----
    nova_fatia = []

    for idx_real in range(num_linhas_reais):
        idx_leitura = idx_real + offset
        nova_linha = []

        for j in range(num_colunas):
            estado_atual = matriz_leitura[idx_leitura][j]

            if estado_atual == IGNORANTE:
                vizinhos = _contar_vizinhos_espalhadores(
                    matriz_leitura, idx_leitura, j,
                    total_linhas_leitura, num_colunas,
                )
                if vizinhos >= limiar:
                    nova_linha.append(ESPALHADOR)
                else:
                    nova_linha.append(IGNORANTE)

            elif estado_atual == ESPALHADOR:
                nova_linha.append(INATIVO)

            else:  # INATIVO — estado absorvente
                nova_linha.append(INATIVO)

        nova_fatia.append(nova_linha)

    return nova_fatia


def contar_estados(matriz):
    """Conta a quantidade de cada estado em uma (sub)matriz.

    Parâmetros
    ----------
    matriz : list[list[int]]
        Matriz ou fatia a ser contabilizada.

    Retorna
    -------
    dict[int, int]
        Mapa ``{estado: quantidade}`` para IGNORANTE, ESPALHADOR e INATIVO.
    """
    contagem = {IGNORANTE: 0, ESPALHADOR: 0, INATIVO: 0}
    for linha in matriz:
        for celula in linha:
            contagem[celula] += 1
    return contagem
