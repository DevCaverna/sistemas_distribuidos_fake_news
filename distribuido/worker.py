import Pyro5.api

from core.automato import calcular_geracao, contar_estados, ESPALHADOR
from core.metricas import MetricasWorker


def executar_worker(host_ns="localhost", porta_ns=9090):
    mestre = Pyro5.api.Proxy(f"PYRONAME:mestre.fakenews@{host_ns}:{porta_ns}")

    config = mestre.registrar_worker()

    mestre.aguardar_workers()

    worker_id = config["worker_id"]
    fatia = config["fatia"]
    geracoes = config["geracoes"]
    limiar = config["limiar"]
    ghost_topo = config["ghost_topo_inicial"]
    ghost_base = config["ghost_base_inicial"]

    metricas = MetricasWorker(worker_id)

    for g in range(1, geracoes + 1):
        metricas.iniciar_processamento()
        fatia = calcular_geracao(fatia, borda_topo=ghost_topo,
                                 borda_base=ghost_base, limiar=limiar)
        metricas.finalizar_processamento()

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
