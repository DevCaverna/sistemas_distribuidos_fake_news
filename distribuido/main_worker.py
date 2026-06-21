"""
distribuido/main_worker.py — Entry point do worker distribuido (Pyro5).

Conecta-se ao NameServer, encontra o Mestre e executa o loop de simulação.
"""

import argparse

from distribuido.worker import executar_worker


def main():
    """Conecta-se ao NameServer e executa o worker."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--porta-ns", type=int, default=9090)
    args = parser.parse_args()

    executar_worker(host_ns=args.host, porta_ns=args.porta_ns)


if __name__ == "__main__":
    main()
