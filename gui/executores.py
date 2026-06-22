import os
import subprocess
import sys
import threading
import time


def _iniciar_leitor_stderr(proc, prefixo):
    def ler():
        for linha in iter(proc.stderr.readline, ""):
            if linha:
                texto = linha.decode(errors="replace").rstrip()
                if texto:
                    print(f"{prefixo} {texto}")
        proc.stderr.close()

    t = threading.Thread(target=ler, daemon=True)
    t.start()


def rodar_sequencial(app, params):
    try:
        from main_sequencial import (
            executar_sequencial,
            exportar_metricas_sequencial,
            gerar_graficos_sequencial,
        )
        from core.comparativo import registrar_resultado
        from gui.telemetria import tentar_exibir_comparativo, carregar_graficos_telemetria

        matriz, tempo_total, metricas = executar_sequencial(
            linhas=params["linhas"],
            colunas=params["colunas"],
            geracoes=params["geracoes"],
            percentual_espalhadores=params["espalhadores"],
            limiar=params["limiar"],
            semente=params["semente"],
            mostrar_grade=False,
            usar_influenciadores=params["influenciadores"],
            usar_midia=params["midia"],
        )
        exportar_metricas_sequencial(metricas)
        caminhos = gerar_graficos_sequencial(metricas)

        cpu_medio = (
            sum(m["cpu_percent"] for m in metricas) / len(metricas)
            if metricas
            else 0
        )
        registrar_resultado("Sequencial", tempo_total, cpu_medio)

        app.after(0, app.atualizar_speedup, "Sequencial", tempo_total)
        app.after(0, tentar_exibir_comparativo, app)
        app.after(0, lambda: app.tabs.set("Metricas e Telemetria"))
        app.after(50, lambda: carregar_graficos_telemetria(app, caminhos))
    except Exception as e:
        print(f"\n[ERRO SEQUENCIAL]: {e}")
        import traceback

        traceback.print_exc()
    finally:
        app.after(0, app.alterar_estado_botoes, True)


def rodar_paralelo(app, params):
    try:
        from paralelo.mestre import MestreParalelo
        from core.metricas import RelatorioMetricas
        from core.utils import Cronometro
        from core.comparativo import registrar_resultado
        from gui.telemetria import tentar_exibir_comparativo, carregar_graficos_telemetria

        print("=> Iniciando Mestre Paralelo (multiprocessing)...")
        mestre = MestreParalelo(
            linhas=params["linhas"],
            colunas=params["colunas"],
            geracoes=params["geracoes"],
            percentual_espalhadores=params["espalhadores"],
            limiar=params["limiar"],
            semente=params["semente"],
            num_workers=params["workers"],
            usar_influenciadores=params["influenciadores"],
            usar_midia=params["midia"],
        )
        mestre.iniciar_workers()

        crono = Cronometro()
        crono.iniciar()
        mestre.aguardar_resultado()
        crono.parar()

        print("Processamento paralelo concluido. Gerando metricas...")

        metricas_raw = mestre.aguardar_metricas()
        relatorio = RelatorioMetricas(params["workers"])
        for mw in metricas_raw:
            relatorio.adicionar_metricas_worker(mw)
        relatorio.imprimir_resumo(crono.elapsed)
        relatorio.exportar_csv()
        caminhos = relatorio.gerar_graficos()

        todos_cpus = [r["cpu_percent"] for rw in metricas_raw for r in rw]
        cpu_medio = sum(todos_cpus) / len(todos_cpus) if todos_cpus else 0
        registrar_resultado(
            "Paralela", crono.elapsed, cpu_medio, rede_bytes=mestre.bytes_trafegados.value
        )

        app.after(0, app.atualizar_speedup, "Paralela", crono.elapsed)
        app.after(0, tentar_exibir_comparativo, app)
        app.after(0, lambda: app.tabs.set("Metricas e Telemetria"))
        app.after(50, lambda: carregar_graficos_telemetria(app, caminhos))
    except Exception as e:
        print(f"\n[ERRO PARALELO]: {e}")
        import traceback

        traceback.print_exc()
    finally:
        app.after(0, app.alterar_estado_botoes, True)


def rodar_distribuido(app, params):
    import Pyro5.api
    import Pyro5.server
    from distribuido.mestre import MestreDistribuido
    from core.metricas import RelatorioMetricas
    from core.utils import Cronometro
    from core.comparativo import registrar_resultado
    from gui.telemetria import tentar_exibir_comparativo, carregar_graficos_telemetria

    app._processos_worker.clear()
    python = sys.executable
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    try:
        print("=> Iniciando Name Server...")
        ns_proc = subprocess.Popen(
            [python, "-m", "Pyro5.nameserver", "--port", "9090"],
            cwd=raiz,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        app._processos_worker.append(ns_proc)
        _iniciar_leitor_stderr(ns_proc, "[NameServer]")
        time.sleep(1.5)

        print(f"=> Iniciando {params['workers']} workers...")
        for _ in range(params["workers"]):
            proc = subprocess.Popen(
                [
                    python,
                    "-m",
                    "distribuido.main_worker",
                    "--host",
                    "localhost",
                    "--porta-ns",
                    "9090",
                ],
                cwd=raiz,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            app._processos_worker.append(proc)
            _iniciar_leitor_stderr(proc, "[Worker]")

        print("=> Iniciando Mestre Distribuido...")
        mestre = MestreDistribuido(
            linhas=params["linhas"],
            colunas=params["colunas"],
            geracoes=params["geracoes"],
            percentual_espalhadores=params["espalhadores"],
            limiar=params["limiar"],
            semente=params["semente"],
            usar_influenciadores=params["influenciadores"],
            usar_midia=params["midia"],
        )

        daemon = Pyro5.server.Daemon(host="0.0.0.0")
        uri = daemon.register(mestre, objectId="mestre.fakenews.obj")

        try:
            ns = Pyro5.api.locate_ns(port=9090)
            ns.register("mestre.fakenews", uri)
        except Exception as e:
            print(f"[ERRO] Falha no NameServer: {e}")
            return

        thread_daemon = threading.Thread(target=daemon.requestLoop, daemon=True)
        thread_daemon.start()

        qtd = mestre.inicializar(timeout=10)
        print(f"{qtd} workers encontrados! Processando...")

        crono = Cronometro()
        crono.iniciar()
        mestre.aguardar_resultado()
        crono.parar()

        matriz_final = mestre.obter_matriz_final()

        print("Processamento concluido. Gerando relatorios...")

        metricas_raw = mestre.aguardar_metricas()
        relatorio = RelatorioMetricas(mestre.num_workers)
        for mw in metricas_raw:
            relatorio.adicionar_metricas_worker(mw)
        relatorio.imprimir_resumo(crono.elapsed)
        relatorio.exportar_csv()
        caminhos = relatorio.gerar_graficos()

        try:
            ns.remove("mestre.fakenews")
        except Exception:
            pass
        daemon.shutdown()

        todos_cpus = [r["cpu_percent"] for rw in metricas_raw for r in rw]
        cpu_medio = sum(todos_cpus) / len(todos_cpus) if todos_cpus else 0
        registrar_resultado(
            "Distribuida",
            crono.elapsed,
            cpu_medio,
            rede_bytes=mestre.bytes_trafegados,
        )

        app.after(0, app.atualizar_speedup, "Distribuida", crono.elapsed)
        app.after(0, tentar_exibir_comparativo, app)
        app.after(0, lambda: app.tabs.set("Metricas e Telemetria"))
        app.after(50, lambda: carregar_graficos_telemetria(app, caminhos))

    except Exception as e:
        print(f"\n[ERRO DISTRIBUÍDO]: {e}")
        import traceback

        traceback.print_exc()
    finally:
        for proc in app._processos_worker:
            try:
                proc.terminate()
            except Exception:
                pass
        app._processos_worker.clear()
        app.after(0, app.alterar_estado_botoes, True)
