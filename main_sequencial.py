"""
main_sequencial.py — Entry point da versão sequencial refatorada.

Reutiliza a lógica do ``core/`` para validar que a base compartilhada
produz resultados idênticos ao código original do professor.
"""

import argparse

from core.automato import aplicar_midia, calcular_geracao, contar_estados, ESPALHADOR
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
    usar_midia=True,
    geracao_midia=5,
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
    usar_midia : bool
        Se ``True``, ativa o efeito da mídia.
    geracao_midia : int
        Geração a partir da qual a mídia começa a atuar (padrão: 5).

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

    if usar_midia:
        print(f"  Mídia:         ativa a partir da geração {geracao_midia}"
              f" (8% dissemina / 92% combate)")

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

        if usar_midia:
            matriz = aplicar_midia(matriz, media_ativa=g >= geracao_midia)

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--linhas", type=int, default=100)
    parser.add_argument("--colunas", type=int, default=100)
    parser.add_argument("--geracoes", type=int, default=50)
    parser.add_argument("--espalhadores", type=float, default=0.05)
    parser.add_argument("--limiar", type=int, default=3)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--mostrar-grade", action="store_true")
    parser.add_argument("--influenciadores", type=bool, default=True)
    parser.add_argument("--usar-midia", type=bool, default=True)
    parser.add_argument("--geracao-midia", type=int, default=5)
    args = parser.parse_args()

    executar_sequencial(
        linhas=args.linhas,
        colunas=args.colunas,
        geracoes=args.geracoes,
        percentual_espalhadores=args.espalhadores,
        limiar=args.limiar,
        semente=args.semente,
        mostrar_grade=args.mostrar_grade,
        usar_influenciadores=args.influenciadores,
        usar_midia=args.usar_midia,
        geracao_midia=args.geracao_midia,
    )
