"""
paralelo/main_paralelo.py — Entry point da versao paralela (multiprocessing).

Executa a simulação com pool de processos (paralelismo REAL, sem GIL),
coleta métricas (CPU, tempo) e gera graficos de telemetria.
"""

import argparse

from core.automato import ESPALHADOR, IGNORANTE, INATIVO, contar_estados
from core.metricas import RelatorioMetricas
from core.utils import Cronometro
from paralelo.mestre import MestreParalelo


def main():
    """Parser de argumentos e ponto de entrada da versao paralela.

    Aceita os mesmos parametros de simulação da versao sequencial,
    acrescido de --workers para definir o numero de processos.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--linhas", type=int, default=100)
    parser.add_argument("--colunas", type=int, default=100)
    parser.add_argument("--geracoes", type=int, default=50)
    parser.add_argument("--espalhadores", type=float, default=0.05)
    parser.add_argument("--limiar", type=int, default=3)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--influenciadores", type=bool, default=True)
    parser.add_argument("--usar-midia", type=bool, default=True)
    parser.add_argument("--geracao-midia", type=int, default=5)
    parser.add_argument("--prob-sensacionalista", type=float, default=0.08)
    args = parser.parse_args()

    mestre = MestreParalelo(
        linhas=args.linhas,
        colunas=args.colunas,
        geracoes=args.geracoes,
        percentual_espalhadores=args.espalhadores,
        limiar=args.limiar,
        semente=args.semente,
        num_workers=args.workers,
        usar_influenciadores=args.influenciadores,
        usar_midia=args.usar_midia,
        geracao_midia=args.geracao_midia,
        prob_sensacionalista=args.prob_sensacionalista,
    )

    mestre.iniciar_workers()

    crono = Cronometro()
    crono.iniciar()

    mestre.aguardar_resultado()
    mestre.aguardar_processos()
    crono.parar()

    matriz_final = mestre.obter_matriz_final()
    contagem = contar_estados(matriz_final)
    total = args.linhas * args.colunas

    print(f"Tempo: {crono.elapsed:.4f}s")
    print(
        f"Ignorantes: {contagem[IGNORANTE]} ({contagem[IGNORANTE] / total * 100:.2f}%)"
    )
    print(
        f"Espalhadores: {contagem[ESPALHADOR]} ({contagem[ESPALHADOR] / total * 100:.2f}%)"
    )
    print(f"Inativos: {contagem[INATIVO]} ({contagem[INATIVO] / total * 100:.2f}%)")

    metricas_raw = mestre.aguardar_metricas()
    relatorio = RelatorioMetricas(args.workers, diretorio_saida="metricas")
    for mw in metricas_raw:
        relatorio.adicionar_metricas_worker(mw)
    relatorio.imprimir_resumo(crono.elapsed, rotulo="PARALELO (MULTIPROCESSING)")
    relatorio.exportar_csv()
    relatorio.gerar_graficos()


if __name__ == "__main__":
    main()
