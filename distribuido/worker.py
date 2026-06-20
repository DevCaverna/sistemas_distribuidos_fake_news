"""
distribuido/worker.py — Cliente worker da versao distribuida (Pyro5).

Conecta-se ao Mestre via Pyro5, recebe sua fatia da matriz, processa
cada geração, troca bordas (ghost rows) e coleta métricas de CPU/rede.
"""

import Pyro5.api

from core.automato import ESPALHADOR, aplicar_midia, calcular_geracao, contar_estados
from core.metricas import MetricasWorker


def executar_worker(host_ns="localhost", porta_ns=9090):
    """Executa o loop de simulação de um worker remoto.

    Etapas:
    1. Conecta-se ao Mestre via NameServer (PYRONAME)
    2. Registra-se e obtem configuração (fatia, ghosts iniciais, etc.)
    3. Aguarda sinal do Mestre para comecar
    4. Para cada geração: processa a fatia, troca bordas via Mestre
    5. Envia resultado final e métricas ao Mestre
    """
    mestre = Pyro5.api.Proxy(f"PYRONAME:mestre.fakenews@{host_ns}:{porta_ns}")

    config = mestre.registrar_worker()

    mestre.aguardar_workers()

    worker_id = config["worker_id"]
    fatia = config["fatia"]
    geracoes = config["geracoes"]
    limiar = config["limiar"]
    ghost_topo = config["ghost_topo_inicial"]
    ghost_base = config["ghost_base_inicial"]
    offset_global = config["offset_global"]
    usar_midia = config["usar_midia"]
    geracao_midia = config["geracao_midia"]
    prob_sensacionalista = config["prob_sensacionalista"]

    mapa_raw = config["mapa_influenciadores"]
    mapa_influenciadores = None
    if mapa_raw is not None:
        mapa_influenciadores = set(tuple(coord) for coord in mapa_raw)

    metricas = MetricasWorker(worker_id)

    for g in range(1, geracoes + 1):
        metricas.iniciar_processamento()
        fatia = calcular_geracao(
            fatia,
            borda_topo=ghost_topo,
            borda_base=ghost_base,
            limiar=limiar,
            mapa_influenciadores=mapa_influenciadores,
            offset_global=offset_global,
        )
        metricas.finalizar_processamento()

        if usar_midia:
            fatia = aplicar_midia(fatia, media_ativa=g >= geracao_midia,
                                   prob_sensacionalista=prob_sensacionalista)

        borda_topo = fatia[0]
        borda_base = fatia[-1]

        contagem = contar_estados(fatia)
        espalhadores = contagem[ESPALHADOR]

        metricas.iniciar_comunicacao()
        mestre.enviar_bordas(worker_id, g, borda_topo, borda_base, espalhadores)
        resposta = mestre.obter_ghosts(worker_id, g)
        metricas.finalizar_comunicacao()

        ghost_topo = resposta["ghost_topo"]
        ghost_base = resposta["ghost_base"]

        if resposta["terminar"]:
            break

    mestre.enviar_resultado(worker_id, fatia)
    mestre.enviar_metricas(worker_id, metricas.exportar())
