"""
core/utils.py — Utilitários compartilhados por todas as versões do projeto.

Contém funções para:
  - Geração da matriz inicial (com seed fixa para reprodutibilidade).
  - Medição de tempo via ``time.perf_counter``.
  - Impressão visual da grade no terminal.
  - Fatiamento da matriz global em submatrizes para N nós.
"""

import random
import time

from core.automato import IGNORANTE, ESPALHADOR, INATIVO


# ---------------------------------------------------------------------------
# Geração da matriz inicial
# ---------------------------------------------------------------------------

def criar_matriz(linhas, colunas, percentual_espalhadores=0.02, semente=42):
    """Gera a matriz inicial da população.

    Todos os indivíduos começam como IGNORANTE. Em seguida, posições
    aleatórias são convertidas em ESPALHADOR conforme o percentual desejado.

    Parâmetros
    ----------
    linhas : int
        Número de linhas da matriz.
    colunas : int
        Número de colunas da matriz.
    percentual_espalhadores : float
        Fração (0 a 1) da população que inicia como espalhadora.
    semente : int
        Seed do gerador aleatório para reprodutibilidade.

    Retorna
    -------
    list[list[int]]
        Matriz ``linhas × colunas`` com os estados iniciais.
    """
    random.seed(semente)

    matriz = [[IGNORANTE] * colunas for _ in range(linhas)]

    total_espalhadores = int(linhas * colunas * percentual_espalhadores)

    for _ in range(total_espalhadores):
        i = random.randint(0, linhas - 1)
        j = random.randint(0, colunas - 1)
        matriz[i][j] = ESPALHADOR

    return matriz


# ---------------------------------------------------------------------------
# Fatiamento da matriz em submatrizes para N nós
# ---------------------------------------------------------------------------

def fatiar_matriz(matriz, num_fatias):
    """Divide a matriz global horizontalmente em ``num_fatias`` submatrizes.

    Se a divisão não for exata, o último nó absorve as linhas restantes.

    Parâmetros
    ----------
    matriz : list[list[int]]
        Matriz global completa.
    num_fatias : int
        Quantidade de partes desejadas (número de nós).

    Retorna
    -------
    list[list[list[int]]]
        Lista de submatrizes (fatias), uma por nó.
    """
    total_linhas = len(matriz)
    tamanho_base = total_linhas // num_fatias

    fatias = []
    inicio = 0

    for i in range(num_fatias):
        # O último nó absorve o resto caso a divisão não seja exata
        if i == num_fatias - 1:
            fim = total_linhas
        else:
            fim = inicio + tamanho_base

        fatias.append(matriz[inicio:fim])
        inicio = fim

    return fatias


def remontar_matriz(fatias):
    """Recombina uma lista de fatias em uma única matriz global.

    Parâmetros
    ----------
    fatias : list[list[list[int]]]
        Lista de submatrizes.

    Retorna
    -------
    list[list[int]]
        Matriz global reconstruída.
    """
    matriz = []
    for fatia in fatias:
        matriz.extend(fatia)
    return matriz


# ---------------------------------------------------------------------------
# Medição de tempo
# ---------------------------------------------------------------------------

class Cronometro:
    """Wrapper simples sobre ``time.perf_counter`` para medições de desempenho.

    Uso::

        crono = Cronometro()
        crono.iniciar()
        # ... operação ...
        crono.parar()
        print(crono.elapsed)   # tempo em segundos (float)
    """

    def __init__(self):
        self._inicio = None
        self._fim = None

    def iniciar(self):
        """Marca o início da medição."""
        self._inicio = time.perf_counter()
        self._fim = None

    def parar(self):
        """Marca o fim da medição."""
        self._fim = time.perf_counter()

    @property
    def elapsed(self):
        """Retorna o tempo decorrido em segundos. ``None`` se não finalizado."""
        if self._inicio is None:
            return None
        fim = self._fim if self._fim is not None else time.perf_counter()
        return fim - self._inicio


# ---------------------------------------------------------------------------
# Impressão da grade no terminal
# ---------------------------------------------------------------------------

_SIMBOLOS = {
    IGNORANTE: ".",
    ESPALHADOR: "E",
    INATIVO: "N",
}


def imprimir_grade(grade, limite=30):
    """Imprime a grade (ou parte dela) no terminal com símbolos legíveis.

    Parâmetros
    ----------
    grade : list[list[int]]
        Matriz a ser impressa.
    limite : int
        Número máximo de linhas e colunas a exibir.
    """
    linhas = min(len(grade), limite)
    colunas = min(len(grade[0]), limite)

    for i in range(linhas):
        print(" ".join(_SIMBOLOS[grade[i][j]] for j in range(colunas)))
    print()


def imprimir_estatisticas(contagem, geracao=None, total_celulas=None):
    """Imprime as estatísticas de uma geração de forma formatada.

    Parâmetros
    ----------
    contagem : dict[int, int]
        Mapa ``{estado: quantidade}``.
    geracao : int | None
        Número da geração (para exibição). Se ``None``, omite o prefixo.
    total_celulas : int | None
        Total de células para cálculo de percentuais. Se ``None``, não
        exibe percentuais.
    """
    prefixo = f"Geração {geracao:03d} | " if geracao is not None else ""

    partes = [
        f"Ignorantes: {contagem[IGNORANTE]:>10,}",
        f"Espalhadores: {contagem[ESPALHADOR]:>10,}",
        f"Inativos: {contagem[INATIVO]:>10,}",
    ]

    if total_celulas:
        partes_pct = []
        for estado, nome in [(IGNORANTE, "Ig"), (ESPALHADOR, "Es"), (INATIVO, "In")]:
            pct = contagem[estado] / total_celulas * 100
            partes_pct.append(f"{nome}: {pct:.1f}%")
        partes.append("(" + " | ".join(partes_pct) + ")")

    print(prefixo + " | ".join(partes))
