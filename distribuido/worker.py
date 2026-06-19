import Pyro5.api

from core.automato import aplicar_midia, calcular_geracao, contar_estados, ESPALHADOR


def executar_worker(host_ns="localhost", porta_ns=9090):
    mestre = Pyro5.api.Proxy(f"PYRONAME:mestre.fakenews@{host_ns}:{porta_ns}")

    config = mestre.registrar_worker()

    worker_id = config["worker_id"]
    fatia = config["fatia"]
    geracoes = config["geracoes"]
    limiar = config["limiar"]
    ghost_topo = config["ghost_topo_inicial"]
    ghost_base = config["ghost_base_inicial"]
    offset_global = config["offset_global"]
    usar_midia = config["usar_midia"]
    geracao_midia = config["geracao_midia"]

    mapa_raw = config["mapa_influenciadores"]
    mapa_influenciadores = None
    if mapa_raw is not None:
        mapa_influenciadores = set(tuple(coord) for coord in mapa_raw)

    for g in range(1, geracoes + 1):
        fatia = calcular_geracao(
            fatia,
            borda_topo=ghost_topo,
            borda_base=ghost_base,
            limiar=limiar,
            mapa_influenciadores=mapa_influenciadores,
            offset_global=offset_global,
        )

        if usar_midia:
            fatia = aplicar_midia(fatia, media_ativa=g >= geracao_midia)

        borda_topo = fatia[0]
        borda_base = fatia[-1]

        contagem = contar_estados(fatia)
        espalhadores = contagem[ESPALHADOR]

        mestre.enviar_bordas(worker_id, g, borda_topo, borda_base, espalhadores)

        resposta = mestre.obter_ghosts(worker_id, g)

        ghost_topo = resposta["ghost_topo"]
        ghost_base = resposta["ghost_base"]

        if resposta["terminar"]:
            break

    mestre.enviar_resultado(worker_id, fatia)
