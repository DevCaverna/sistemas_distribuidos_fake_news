"""
main_sequencial.py — Entry point da versao sequencial refatorada.

Coleta metricas de CPU e tempo por geracao para exportacao em CSV e graficos.
"""

import argparse
import csv
import os
import time

import psutil

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
    prob_sensacionalista=0.08,
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
        Se ``True``, imprime a grade a cada geração.
    usar_influenciadores : bool
        Se ``True``, ativa a mecânica de Influenciadores Digitais (1%
        da população com vizinhança 5x5 e transmissão probabilística).
    usar_midia : bool
        Se ``True``, ativa o efeito da mídia.
    geracao_midia : int
        Geração a partir da qual a mídia começa a atuar (padrão: 5).
    prob_sensacionalista : float
        Probabilidade de a mídia disseminar fake news quando alcança
        um IGNORANTE (padrão: 0.08 = 8%).

    Retorna
    -------
    tuple[list[list[int]], float, list[dict]]
        (matriz_final, tempo_total_segundos, metricas_por_geracao)
    """
    processo = psutil.Process()
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
        pct_sens = prob_sensacionalista * 100
        pct_combate = (1 - prob_sensacionalista) * 100
        print(f"  Mídia:         ativa a partir da geração {geracao_midia}"
              f" ({pct_sens:.0f}% dissemina / {pct_combate:.0f}% combate)")

    print("=" * 60)
    print()

    metricas = []
    crono = Cronometro()
    crono.iniciar()

    for g in range(1, geracoes + 1):
        t0 = time.perf_counter()
        processo.cpu_percent()

        matriz = calcular_geracao(
            matriz,
            borda_topo=None,
            borda_base=None,
            limiar=limiar,
            mapa_influenciadores=mapa_influenciadores,
            offset_global=0,
        )

        if usar_midia:
            matriz = aplicar_midia(matriz, media_ativa=g >= geracao_midia,
                                   prob_sensacionalista=prob_sensacionalista)

        tempo_proc = time.perf_counter() - t0
        cpu_pct = processo.cpu_percent() / psutil.cpu_count()

        metricas.append({
            "geracao": g,
            "tempo_processamento": tempo_proc,
            "latencia_rede": 0.0,
            "cpu_percent": cpu_pct,
        })

        contagem = contar_estados(matriz)
        imprimir_estatisticas(contagem, geracao=g, total_celulas=total_celulas)

        if mostrar_grade:
            imprimir_grade(matriz, mapa_influenciadores=mapa_influenciadores)

        if contagem[ESPALHADOR] == 0:
            print("\nPropagação encerrada: não há mais espalhadores.")
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

    return matriz, crono.elapsed, metricas


def exportar_metricas_sequencial(metricas, diretorio="metricas"):
    """Exporta métricas sequenciais para CSV."""
    os.makedirs(diretorio, exist_ok=True)
    caminho = os.path.join(diretorio, "metricas_sequencial.csv")

    campos = ["geracao", "tempo_processamento", "latencia_rede", "cpu_percent"]
    with open(caminho, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for reg in sorted(metricas, key=lambda r: r["geracao"]):
            reg["latencia_rede"] = 0.0
            writer.writerow(reg)

    return caminho


def gerar_graficos_sequencial(metricas, diretorio="metricas"):
    """Gera gráfico de CPU e tempo para execução sequencial."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[Métricas] matplotlib não instalado. pip install matplotlib")
        return []

    os.makedirs(diretorio, exist_ok=True)

    geracoes = [r["geracao"] for r in metricas]
    tempos = [r["tempo_processamento"] * 1000 for r in metricas]
    cpus = [r["cpu_percent"] for r in metricas]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    ax1.plot(geracoes, tempos, marker="o", color="#3498db", lw=2)
    ax1.set_ylabel("Tempo (ms)")
    ax1.set_title("Tempo de Processamento por Geração (Sequencial)")
    ax1.grid(True, alpha=0.3)

    ax2.plot(geracoes, cpus, marker="s", color="#e74c3c", lw=2)
    ax2.set_xlabel("Geração")
    ax2.set_ylabel("CPU (%)")
    ax2.set_title("Consumo de CPU por Geração (Sequencial)")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    caminho = os.path.join(diretorio, "metricas_sequencial.png")
    fig.savefig(caminho, dpi=150)
    plt.close(fig)
    return [caminho]


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
    parser.add_argument("--prob-sensacionalista", type=float, default=0.08)
    args = parser.parse_args()

    matriz, tempo, metricas = executar_sequencial(
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
        prob_sensacionalista=args.prob_sensacionalista,
    )
    exportar_metricas_sequencial(metricas)
    gerar_graficos_sequencial(metricas)
