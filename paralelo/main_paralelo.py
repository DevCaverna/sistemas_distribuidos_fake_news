import argparse

from core.automato import contar_estados, IGNORANTE, ESPALHADOR, INATIVO
from core.utils import Cronometro
from paralelo.mestre import MestreParalelo


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--linhas", type=int, default=100)
    parser.add_argument("--colunas", type=int, default=100)
    parser.add_argument("--geracoes", type=int, default=50)
    parser.add_argument("--espalhadores", type=float, default=0.05)
    parser.add_argument("--limiar", type=int, default=3)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()

    mestre = MestreParalelo(
        linhas=args.linhas,
        colunas=args.colunas,
        geracoes=args.geracoes,
        percentual_espalhadores=args.espalhadores,
        limiar=args.limiar,
        semente=args.semente,
        num_workers=args.workers,
    )

    threads = mestre.iniciar_workers()

    crono = Cronometro()
    crono.iniciar()

    mestre.aguardar_resultado()
    crono.parar()

    matriz_final = mestre.obter_matriz_final()
    contagem = contar_estados(matriz_final)
    total = args.linhas * args.colunas

    print(f"Tempo: {crono.elapsed:.4f}s")
    print(f"Ignorantes: {contagem[IGNORANTE]} ({contagem[IGNORANTE]/total*100:.2f}%)")
    print(f"Espalhadores: {contagem[ESPALHADOR]} ({contagem[ESPALHADOR]/total*100:.2f}%)")
    print(f"Inativos: {contagem[INATIVO]} ({contagem[INATIVO]/total*100:.2f}%)")


if __name__ == "__main__":
    main()
