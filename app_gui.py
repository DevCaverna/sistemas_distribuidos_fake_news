"""
app_gui.py — Interface Grafica Integrada para o Simulador de Fake News.

Utiliza CustomTkinter e matplotlib (FigureCanvasTkAgg) para exibir graficos
de telemetria inline. Executa workers distribuidos em background localmente
e gera metricas para todas as modalidades (sequencial, paralela, distribuida).
"""

import os
import subprocess
import sys
import threading

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

METRICAS_DIR = "metricas"

CORES_ESTADOS = {
    0: (46, 204, 113),
    1: (231, 76, 60),
    2: (149, 165, 166),
}


class RedirectorConsole:
    """Redireciona o sys.stdout para um widget Textbox do CustomTkinter."""

    def __init__(self, textbox, app):
        self.textbox = textbox
        self.app = app
        self.original_stdout = sys.stdout

    def write(self, texto):
        self.original_stdout.write(texto)
        self.app.after(0, self._escrever_na_gui, texto)

    def _escrever_na_gui(self, texto):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", texto)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def flush(self):
        self.original_stdout.flush()


class FakeNewsApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Fake News Simulator — Telemetria e Execucao")
        self.geometry("1100x700")
        self.minsize(950, 600)

        self.is_running = False
        self._processos_worker = []
        self.tempos_execucao = {
            "Sequencial": None,
            "Paralela": None,
            "Distribuida": None,
        }

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.construir_sidebar()
        self.construir_painel_principal()

        self.redirector = RedirectorConsole(self.text_console, self)
        sys.stdout = self.redirector

        self.mostrar_boas_vindas()

    def construir_sidebar(self):
        """Constroi o painel lateral com configuracoes do simulador."""
        self.sidebar = ctk.CTkScrollableFrame(
            self, width=260, corner_radius=0, fg_color="#212121"
        )
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.sidebar, text="Parametros",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.entradas = {}
        campos = [
            ("Linhas", "linhas", "100"),
            ("Colunas", "colunas", "100"),
            ("Geracoes", "geracoes", "50"),
            ("% Espalhadores", "espalhadores", "0.05"),
            ("Limiar", "limiar", "3"),
            ("Semente", "semente", "42"),
            ("N Workers", "workers", "2"),
        ]

        row_idx = 1
        for rotulo, chave, padrao in campos:
            ctk.CTkLabel(
                self.sidebar, text=rotulo, font=ctk.CTkFont(size=13)
            ).grid(row=row_idx, column=0, padx=20, pady=(5, 0), sticky="w")
            row_idx += 1
            var = ctk.StringVar(value=padrao)
            ctk.CTkEntry(
                self.sidebar, textvariable=var, height=30
            ).grid(row=row_idx, column=0, padx=20, pady=(2, 5), sticky="ew")
            self.entradas[chave] = var
            row_idx += 1

        ctk.CTkFrame(
            self.sidebar, height=2, fg_color="gray30"
        ).grid(row=row_idx, column=0, padx=20, pady=15, sticky="ew")
        row_idx += 1

        ctk.CTkLabel(
            self.sidebar, text="Comparativo de Desempenho",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=row_idx, column=0, padx=20, pady=(0, 5), sticky="w")
        row_idx += 1

        self.label_speedup_seq = ctk.CTkLabel(
            self.sidebar, text="Seq: -- s",
            text_color="gray60", font=ctk.CTkFont(size=12),
        )
        self.label_speedup_seq.grid(row=row_idx, column=0, padx=20, pady=2, sticky="w")
        row_idx += 1

        self.label_speedup_par = ctk.CTkLabel(
            self.sidebar, text="Par: -- s (Speedup: --x)",
            text_color="gray60", font=ctk.CTkFont(size=12),
        )
        self.label_speedup_par.grid(row=row_idx, column=0, padx=20, pady=2, sticky="w")
        row_idx += 1

        self.label_speedup_dist = ctk.CTkLabel(
            self.sidebar, text="Dist: -- s (Speedup: --x)",
            text_color="gray60", font=ctk.CTkFont(size=12),
        )
        self.label_speedup_dist.grid(
            row=row_idx, column=0, padx=20, pady=2, sticky="w"
        )
        row_idx += 1

        self.label_status = ctk.CTkLabel(
            self.sidebar, text="Ocioso",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4CAF50",
        )
        self.label_status.grid(row=row_idx, column=0, padx=20, pady=(20, 10), sticky="w")

    def construir_painel_principal(self):
        """Constroi a area principal com botoes de execucao e abas."""
        self.main_frame = ctk.CTkFrame(
            self, corner_radius=0, fg_color="transparent"
        )
        self.main_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
        self.main_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        self.btn_seq = ctk.CTkButton(
            self.main_frame, text="Executar Sequencial", height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.btn_action_sequencial,
        )
        self.btn_seq.grid(row=0, column=0, padx=5, pady=(0, 10), sticky="ew")

        self.btn_par = ctk.CTkButton(
            self.main_frame, text="Executar Paralelo", height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#8E44AD", hover_color="#732D91",
            command=self.btn_action_paralelo,
        )
        self.btn_par.grid(row=0, column=1, padx=5, pady=(0, 10), sticky="ew")

        self.btn_dist = ctk.CTkButton(
            self.main_frame, text="Executar Distribuido", height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#27AE60", hover_color="#1E8449",
            command=self.btn_action_distribuido,
        )
        self.btn_dist.grid(row=0, column=2, padx=5, pady=(0, 10), sticky="ew")

        self.progressbar = ctk.CTkProgressBar(self.main_frame, height=8)
        self.progressbar.grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10)
        )
        self.progressbar.set(0)

        self.tabs = ctk.CTkTabview(self.main_frame)
        self.tabs.grid(row=2, column=0, columnspan=3, sticky="nswe")

        self.tab_console = self.tabs.add("Console / Logs")
        self.tab_metricas = self.tabs.add("Metricas e Telemetria")

        self.construir_aba_console()
        self.construir_aba_metricas()

    def construir_aba_console(self):
        self.tab_console.grid_columnconfigure(0, weight=1)
        self.tab_console.grid_rowconfigure(0, weight=1)
        self.text_console = ctk.CTkTextbox(
            self.tab_console, state="disabled",
            font=ctk.CTkFont(family="Courier", size=12),
            wrap="word",
        )
        self.text_console.grid(row=0, column=0, sticky="nswe", padx=5, pady=5)

    def construir_aba_metricas(self):
        self.tab_metricas.grid_columnconfigure(0, weight=1)
        self.tab_metricas.grid_rowconfigure(0, weight=1)

        self.scroll_metricas = ctk.CTkScrollableFrame(
            self.tab_metricas, fg_color="transparent"
        )
        self.scroll_metricas.grid(row=0, column=0, sticky="nswe", padx=5, pady=5)
        self.scroll_metricas.grid_columnconfigure(0, weight=1)

        self.lbl_placeholder_metricas = ctk.CTkLabel(
            self.scroll_metricas,
            text="Execute uma simulacao para visualizar os graficos de telemetria.",
            font=ctk.CTkFont(size=14),
            text_color="gray50",
        )
        self.lbl_placeholder_metricas.pack(pady=50)

        self.container_graficos = ctk.CTkFrame(
            self.scroll_metricas, fg_color="transparent"
        )
        self.container_graficos.pack(fill="both", expand=True)
        for col in range(2):
            self.container_graficos.grid_columnconfigure(col, weight=1)

    def mostrar_boas_vindas(self):
        print("=" * 60)
        print(" FAKE NEWS SIMULATOR - Painel Integrado de Controle")
        print("=" * 60)
        print(" Selecione os parametros na barra lateral.")
        print(" Para o modo Distribuido a GUI inicia workers localmente.")
        print("=" * 60 + "\n")

    def alterar_estado_botoes(self, ativo: bool):
        estado = "normal" if ativo else "disabled"
        self.btn_seq.configure(state=estado)
        self.btn_par.configure(state=estado)
        self.btn_dist.configure(state=estado)
        self.is_running = not ativo
        if not ativo:
            self.progressbar.set(0)
            self.label_status.configure(
                text="Processando...", text_color="#F39C12"
            )
        else:
            self.progressbar.set(1.0)
            self.label_status.configure(
                text="Concluido", text_color="#4CAF50"
            )

    def ler_parametros(self):
        try:
            return {
                "linhas": int(self.entradas["linhas"].get()),
                "colunas": int(self.entradas["colunas"].get()),
                "geracoes": int(self.entradas["geracoes"].get()),
                "espalhadores": float(self.entradas["espalhadores"].get()),
                "limiar": int(self.entradas["limiar"].get()),
                "semente": int(self.entradas["semente"].get()),
                "workers": int(self.entradas["workers"].get()),
            }
        except ValueError as e:
            print(f"[Erro] Verifique os valores: {e}")
            return None

    def atualizar_speedup(self, modalidade, tempo_total):
        self.tempos_execucao[modalidade] = tempo_total

        t_seq = self.tempos_execucao["Sequencial"]
        t_par = self.tempos_execucao["Paralela"]
        t_dist = self.tempos_execucao["Distribuida"]

        if t_seq:
            self.label_speedup_seq.configure(
                text=f"Seq: {t_seq:.4f} s", text_color="white"
            )

        if t_par:
            if t_seq:
                sp = t_seq / t_par
                self.label_speedup_par.configure(
                    text=f"Par: {t_par:.4f} s (Speedup: {sp:.2f}x)",
                    text_color="#3498DB",
                )
            else:
                self.label_speedup_par.configure(
                    text=f"Par: {t_par:.4f} s", text_color="white"
                )

        if t_dist:
            if t_seq:
                sp = t_seq / t_dist
                self.label_speedup_dist.configure(
                    text=f"Dist: {t_dist:.4f} s (Speedup: {sp:.2f}x)",
                    text_color="#3498DB",
                )
            else:
                self.label_speedup_dist.configure(
                    text=f"Dist: {t_dist:.4f} s", text_color="white"
                )

    def _exibir_imagem_grafico(self, caminho, idx=0):
        """Carrega PNG em FigureCanvasTkAgg — mantem aspect ratio ao redimensionar."""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            img = plt.imread(caminho)
            h, w = img.shape[:2]
            ratio = h / w

            fig = plt.Figure(figsize=(5, 5 * ratio), dpi=100, facecolor="none")
            ax = fig.add_subplot(111)
            ax.imshow(img, aspect="equal")
            ax.axis("off")
            fig.subplots_adjust(0, 0, 1, 1)

            col = idx % 2
            row = idx // 2
            figura_ref = {"fig": fig, "ratio": ratio}

            canvas = FigureCanvasTkAgg(fig, self.container_graficos)
            canvas.draw()
            widget = canvas.get_tk_widget()

            def _ajustar(e=None):
                larg = widget.winfo_width()
                if larg > 10:
                    alt = int(larg * figura_ref["ratio"])
                    if widget.winfo_height() != alt:
                        widget.configure(height=alt)
                    fig.set_size_inches(larg / fig.dpi, alt / fig.dpi)
                    canvas.draw()

            widget.grid(row=row, column=col, padx=6, pady=6, sticky="ew")
            widget.bind("<Configure>", _ajustar, add="+")
            self.after_idle(_ajustar)

            caminho_abs = os.path.abspath(caminho)
            widget.bind(
                "<Button-1>",
                lambda e, p=caminho_abs: self._abrir_imagem_tela_cheia(p),
            )

            if not hasattr(self, "_figuras"):
                self._figuras = []
            self._figuras.append(fig)
        except Exception as e:
            print(f"[Aviso] Nao foi possivel exibir {caminho}: {e}")

    def _abrir_imagem_tela_cheia(self, caminho):
        try:
            from PIL import Image
            janela = ctk.CTkToplevel(self)
            janela.title(os.path.basename(caminho))
            janela.attributes("-fullscreen", True)

            pil_img = Image.open(caminho)
            largura_tela = janela.winfo_screenwidth()
            altura_tela = janela.winfo_screenheight()
            margem = 60
            max_larg = largura_tela - margem
            max_alt = altura_tela - margem
            ratio = pil_img.width / pil_img.height
            if pil_img.width > max_larg or pil_img.height > max_alt:
                if max_larg / ratio <= max_alt:
                    display_w = max_larg
                    display_h = int(max_larg / ratio)
                else:
                    display_h = max_alt
                    display_w = int(max_alt * ratio)
            else:
                display_w = pil_img.width
                display_h = pil_img.height
            pil_red = pil_img.resize((display_w, display_h), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil_red, dark_image=pil_red,
                                   size=(display_w, display_h))
            label = ctk.CTkLabel(janela, image=ctk_img, text="")
            label.pack(expand=True, fill="both")
            def fechar(e=None):
                janela.attributes("-fullscreen", False)
                janela.destroy()
            label.bind("<Button-1>", fechar)
            janela.bind("<Escape>", fechar)
        except Exception as e:
            print(f"[Aviso] Erro ao expandir imagem: {e}")

    def limpar_graficos(self):
        for widget in self.container_graficos.winfo_children():
            widget.destroy()
        if hasattr(self, "_figuras"):
            import matplotlib.pyplot as plt
            for fig in self._figuras:
                plt.close(fig)
            self._figuras.clear()
        self.lbl_placeholder_metricas.pack_forget()

    def _iniciar_leitor_stderr(self, proc, prefixo):
        def ler():
            for linha in iter(proc.stderr.readline, ""):
                if linha:
                    texto = linha.decode(errors="replace").rstrip()
                    if texto:
                        print(f"{prefixo} {texto}")
            proc.stderr.close()
        t = threading.Thread(target=ler, daemon=True)
        t.start()

    def _tentar_exibir_comparativo(self):
        from core.comparativo import todos_executados, gerar_comparativo
        if todos_executados():
            print("\n[Comparativo] Todos os tipos executados. Gerando grafico comparativo...")
            caminhos = gerar_comparativo()
            if caminhos:
                self._exibir_imagem_grafico(caminhos[0])

    def carregar_graficos_telemetria(self, caminhos_adicionais=None):
        """Exibe graficos PNG na aba de metricas."""
        self.limpar_graficos()

        ctk.CTkLabel(
            self.container_graficos,
            text="Graficos de Telemetria",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#2ecc71",
        ).grid(row=0, column=0, columnspan=2, pady=(30, 10))

        padrao = [
            "gargalos_rede_vs_cpu.png",
            "processamento_vs_latencia.png",
            "profiling_tempos_barras.png",
            "profiling_cpu.png",
            "metricas_sequencial.png",
        ]

        exibidos = []
        for nome in padrao:
            caminho = os.path.join(METRICAS_DIR, nome)
            if os.path.exists(caminho):
                self._exibir_imagem_grafico(caminho, idx=len(exibidos))
                exibidos.append(caminho)

        if caminhos_adicionais:
            for caminho in caminhos_adicionais:
                if caminho and os.path.exists(caminho) and caminho not in exibidos:
                    self._exibir_imagem_grafico(caminho, idx=len(exibidos))
                    exibidos.append(caminho)

        if not exibidos:
            ctk.CTkLabel(
                self.container_graficos,
                text="Nenhum grafico encontrado em metricas/",
                font=ctk.CTkFont(size=14),
                text_color="gray50",
            ).pack(pady=20)

    def btn_action_sequencial(self):
        if self.is_running:
            return
        params = self.ler_parametros()
        if not params:
            return

        self.alterar_estado_botoes(False)
        self.tabs.set("Console / Logs")

        threading.Thread(
            target=self._rodar_sequencial_worker, args=(params,), daemon=True
        ).start()

    def _rodar_sequencial_worker(self, params):
        try:
            from main_sequencial import (
                executar_sequencial,
                exportar_metricas_sequencial,
                gerar_graficos_sequencial,
            )
            from core.comparativo import registrar_resultado, todos_executados, gerar_comparativo

            matriz, tempo_total, metricas = executar_sequencial(
                linhas=params["linhas"],
                colunas=params["colunas"],
                geracoes=params["geracoes"],
                percentual_espalhadores=params["espalhadores"],
                limiar=params["limiar"],
                semente=params["semente"],
                mostrar_grade=False,
            )

            exportar_metricas_sequencial(metricas)
            caminhos = gerar_graficos_sequencial(metricas)

            cpu_medio = (
                sum(m["cpu_percent"] for m in metricas) / len(metricas)
                if metricas else 0
            )
            registrar_resultado("Sequencial", tempo_total, cpu_medio)

            self.after(0, self.atualizar_speedup, "Sequencial", tempo_total)
            self.after(0, self._tentar_exibir_comparativo)
            self.after(0, lambda: self.tabs.set("Metricas e Telemetria"))
            self.after(50, lambda: self.carregar_graficos_telemetria(caminhos))

        except Exception as e:
            print(f"\n[ERRO SEQUENCIAL]: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.after(0, self.alterar_estado_botoes, True)

    def btn_action_paralelo(self):
        if self.is_running:
            return
        params = self.ler_parametros()
        if not params:
            return

        self.alterar_estado_botoes(False)
        self.tabs.set("Console / Logs")

        threading.Thread(
            target=self._rodar_paralelo_hook, args=(params,), daemon=True
        ).start()

    def _rodar_paralelo_hook(self, params):
        try:
            from paralelo.mestre import MestreParalelo
            from core.metricas import RelatorioMetricas
            from core.utils import Cronometro
            from core.comparativo import registrar_resultado

            print("=> Iniciando Mestre Paralelo (Threads Nativas)...")
            mestre = MestreParalelo(
                linhas=params["linhas"],
                colunas=params["colunas"],
                geracoes=params["geracoes"],
                percentual_espalhadores=params["espalhadores"],
                limiar=params["limiar"],
                semente=params["semente"],
                num_workers=params["workers"],
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
            registrar_resultado("Paralela", crono.elapsed, cpu_medio,
                                rede_bytes=mestre.bytes_trafegados)

            self.after(0, self.atualizar_speedup, "Paralela", crono.elapsed)
            self.after(0, self._tentar_exibir_comparativo)
            self.after(0, lambda: self.tabs.set("Metricas e Telemetria"))
            self.after(50, lambda: self.carregar_graficos_telemetria(caminhos))

        except Exception as e:
            print(f"\n[ERRO PARALELO]: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.after(0, self.alterar_estado_botoes, True)

    def btn_action_distribuido(self):
        if self.is_running:
            return
        params = self.ler_parametros()
        if not params:
            return

        self.alterar_estado_botoes(False)
        self.tabs.set("Console / Logs")

        threading.Thread(
            target=self._rodar_distribuido_worker, args=(params,), daemon=True
        ).start()

    def _rodar_distribuido_worker(self, params):
        import Pyro5.api
        import Pyro5.server
        from distribuido.mestre import MestreDistribuido
        from core.metricas import RelatorioMetricas
        from core.utils import Cronometro
        from core.automato import contar_estados, IGNORANTE, ESPALHADOR, INATIVO
        from core.comparativo import registrar_resultado

        import time
        self._processos_worker = []
        python = sys.executable
        raiz = os.path.dirname(os.path.abspath(__file__))

        try:
            print("=> Iniciando Name Server...")
            ns_proc = subprocess.Popen(
                [python, "-m", "Pyro5.nameserver", "--port", "9090"],
                cwd=raiz,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            self._processos_worker.append(ns_proc)
            self._iniciar_leitor_stderr(ns_proc, "[NameServer]")
            time.sleep(1.5)

            print("=> Iniciando Mestre Distribuido...")

            mestre = MestreDistribuido(
                linhas=params["linhas"], colunas=params["colunas"],
                geracoes=params["geracoes"],
                percentual_espalhadores=params["espalhadores"],
                limiar=params["limiar"], semente=params["semente"],
                num_workers=params["workers"],
            )

            daemon = Pyro5.server.Daemon(host="0.0.0.0")
            uri = daemon.register(mestre, objectId="mestre.fakenews.obj")

            try:
                ns = Pyro5.api.locate_ns(port=9090)
                ns.register("mestre.fakenews", uri)
            except Exception as e:
                print(f"[ERRO] Falha no NameServer: {e}")
                return

            thread_daemon = threading.Thread(
                target=daemon.requestLoop, daemon=True
            )
            thread_daemon.start()

            print(f"=> Iniciando {params['workers']} workers...")
            for _ in range(params["workers"]):
                proc = subprocess.Popen(
                    [python, "-m", "distribuido.main_worker",
                     "--host", "localhost", "--porta-ns", "9090"],
                    cwd=raiz,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                self._processos_worker.append(proc)
                self._iniciar_leitor_stderr(proc, f"[Worker]")

            mestre.aguardar_workers()
            print("Todos os workers conectados! Processando...")

            crono = Cronometro()
            crono.iniciar()
            mestre.aguardar_resultado()
            crono.parar()

            matriz_final = mestre.obter_matriz_final()

            print("Processamento concluido. Gerando relatorios...")

            metricas_raw = mestre.aguardar_metricas()
            relatorio = RelatorioMetricas(params["workers"])
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
            registrar_resultado("Distribuida", crono.elapsed, cpu_medio,
                                rede_bytes=mestre.bytes_trafegados)

            self.after(0, self.atualizar_speedup, "Distribuida", crono.elapsed)
            self.after(0, self._tentar_exibir_comparativo)
            self.after(0, lambda: self.tabs.set("Metricas e Telemetria"))
            self.after(50, lambda: self.carregar_graficos_telemetria(caminhos))

        except Exception as e:
            print(f"\n[ERRO DISTRIBUÍDO]: {e}")
            import traceback
            traceback.print_exc()
        finally:
            for proc in self._processos_worker:
                try:
                    proc.terminate()
                except Exception:
                    pass
            self._processos_worker.clear()
            self.after(0, self.alterar_estado_botoes, True)


if __name__ == "__main__":
    app = FakeNewsApp()
    app.mainloop()
