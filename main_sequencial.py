"""
main_sequencial.py — Entry point da versão sequencial refatorada.

Reutiliza a lógica do ``core/`` para validar que a base compartilhada
produz resultados idênticos ao código original do professor.
"""

from core.automato import calcular_geracao, contar_estados, ESPALHADOR
from core.utils import (
    criar_matriz, criar_mapa_influenciadores,
    imprimir_grade, imprimir_estatisticas, Cronometro,
)


def executar_sequencial(
    linhas=100,
    colunas=100,
    geracoes=50,
    percentual_espalhadores=0.02,
    limiar=2,
    semente=42,
    mostrar_grade=False,
    usar_influenciadores=True,
):
    """Executa a simulação sequencial completa usando o módulo core.

    Parâmetros
    ----------
    linhas, colunas : int
        Dimensões da matriz.
    geracoes : int
        Quantidade máxima de gerações a simular.
    percentual_espalhadores : float
        Fração inicial de espalhadores.
    limiar : int
        Vizinhos espalhadores necessários para convencer um ignorante.
    semente : int
        Seed para reprodutibilidade.
    mostrar_grade : bool
        Se ``True``, imprime a grade a cada geração (use apenas para
        matrizes pequenas).
    usar_influenciadores : bool
        Se ``True``, ativa a mecânica de Influenciadores Digitais (1%
        da população com vizinhança 5x5 e transmissão probabilística).

    Retorna
    -------
    tuple[list[list[int]], float]
        (matriz_final, tempo_total_segundos)
    """
    matriz = criar_matriz(linhas, colunas, percentual_espalhadores, semente)

    mapa_influenciadores = None
    if usar_influenciadores:
        mapa_influenciadores = criar_mapa_influenciadores(linhas, colunas)

    total_celulas = linhas * colunas

    print("=" * 60)
    print("  SIMULAÇÃO SEQUENCIAL — PROPAGAÇÃO DE FAKE NEWS")
    print("=" * 60)

    contagem = contar_estados(matriz)
    print(f"  Matriz:       {linhas} × {colunas} ({total_celulas:,} células)")
    print(f"  Gerações:     {geracoes}")
    print(f"  Espalhadores: {contagem[ESPALHADOR]:,} "
          f"({percentual_espalhadores * 100:.2f}%)")
    print(f"  Limiar:       {limiar} vizinhos")
    print(f"  Semente:      {semente}")

    if mapa_influenciadores:
        print(f"  Influenciadores: {len(mapa_influenciadores):,} "
              f"(1% da população, vizinhança 5x5, prob. 45-60%)")

    print("=" * 60)
    print()

    crono = Cronometro()
    crono.iniciar()

    for g in range(1, geracoes + 1):
        matriz = calcular_geracao(
            matriz,
            borda_topo=None,
            borda_base=None,
            limiar=limiar,
            mapa_influenciadores=mapa_influenciadores,
            offset_global=0,
        )

        contagem = contar_estados(matriz)
        imprimir_estatisticas(contagem, geracao=g, total_celulas=total_celulas)

        if mostrar_grade:
            imprimir_grade(matriz, mapa_influenciadores=mapa_influenciadores)

        if contagem[ESPALHADOR] == 0:
            print("\n✔ Propagação encerrada: não há mais espalhadores.")
            break

    crono.parar()

    print()
    print("=" * 60)
    print("  RESULTADO FINAL")
    print("=" * 60)
    print(f"  Tempo total: {crono.elapsed:.4f} s")

    contagem_final = contar_estados(matriz)
    for estado, nome in [(0, "Ignorantes"), (1, "Espalhadores"), (2, "Inativos")]:
        qtd = contagem_final[estado]
        pct = qtd / total_celulas * 100
        print(f"  {nome:>13}: {qtd:>10,}  ({pct:.2f}%)")

    print("=" * 60)

    return matriz, crono.elapsed


if __name__ == "__main__":
    executar_sequencial(
        linhas=100,
        colunas=100,
        geracoes=50,
        percentual_espalhadores=0.05,
        limiar=3,
        semente=42,
        mostrar_grade=False,
        usar_influenciadores=True,
    )
