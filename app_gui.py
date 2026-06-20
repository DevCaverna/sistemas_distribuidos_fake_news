"""
app_gui.py — Interface Gráfica Integrada para o Simulador de Fake News

Esta interface gráfica (GUI) utiliza CustomTkinter para prover um painel limpo
e moderno. Ela isola completamente a lógica de interface (Visualização, Métricas, Logs)
da lógica de negócio.

Aqui estão configurados os botões para executar as modalidades:
- Sequencial
- Paralela (A ser implementada/plugada)
- Distribuída

COMO PLUGAR A LÓGICA PARALELA:
Procure pelo método `_rodar_paralelo_hook` na classe `FakeNewsApp`. É lá que você
deverá instanciar e executar a sua lógica de processamento paralelo. Após a
conclusão, você pode alimentar a interface com os resultados (tempo total,
matriz resultante, caminhos para gráficos gerados, etc.) utilizando os métodos
auxiliares da própria classe.
"""

import os
import sys
import threading
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

METRICAS_DIR = "metricas"
MAX_IMG_WIDTH = 700

CORES_ESTADOS = {
    0: (46, 204, 113),  # Ignorante - Verde
    1: (231, 76, 60),   # Espalhador - Vermelho
    2: (149, 165, 166), # Inativo - Cinza
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

        self.title("Fake News Simulator - Telemetria e Execução")
        self.geometry("1100x700")
        self.minsize(950, 600)

        self.is_running = False
        self.tempos_execucao = {
            "Sequencial": None,
            "Paralela": None,
            "Distribuída": None
        }

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.construir_sidebar()
        self.construir_painel_principal()

        self.redirector = RedirectorConsole(self.text_console, self)
        sys.stdout = self.redirector

        self.mostrar_boas_vindas()

    def construir_sidebar(self):
        """Constrói o painel lateral com configurações do simulador."""
        self.sidebar = ctk.CTkScrollableFrame(self, width=260, corner_radius=0, fg_color="#212121")
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.sidebar, text="⚙ Parâmetros", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.entradas = {}
        campos = [
            ("Linhas", "linhas", "100"),
            ("Colunas", "colunas", "100"),
            ("Gerações", "geracoes", "50"),
            ("% Espalhadores", "espalhadores", "0.05"),
            ("Limiar", "limiar", "3"),
            ("Semente", "semente", "42"),
            ("Nº Workers", "workers", "2"),
        ]

        row_idx = 1
        for rotulo, chave, padrao in campos:
            ctk.CTkLabel(self.sidebar, text=rotulo, font=ctk.CTkFont(size=13)).grid(row=row_idx, column=0, padx=20, pady=(5, 0), sticky="w")
            row_idx += 1
            
            var = ctk.StringVar(value=padrao)
            ctk.CTkEntry(self.sidebar, textvariable=var, height=30).grid(row=row_idx, column=0, padx=20, pady=(2, 5), sticky="ew")
            self.entradas[chave] = var
            row_idx += 1

        ctk.CTkFrame(self.sidebar, height=2, fg_color="gray30").grid(row=row_idx, column=0, padx=20, pady=15, sticky="ew")
        row_idx += 1

        ctk.CTkLabel(self.sidebar, text="📊 Comparativo de Desempenho", font=ctk.CTkFont(size=14, weight="bold")).grid(row=row_idx, column=0, padx=20, pady=(0, 5), sticky="w")
        row_idx += 1

        self.label_speedup_seq = ctk.CTkLabel(self.sidebar, text="Seq: -- s", text_color="gray60", font=ctk.CTkFont(size=12))
        self.label_speedup_seq.grid(row=row_idx, column=0, padx=20, pady=2, sticky="w")
        row_idx += 1

        self.label_speedup_par = ctk.CTkLabel(self.sidebar, text="Par: -- s (Speedup: --x)", text_color="gray60", font=ctk.CTkFont(size=12))
        self.label_speedup_par.grid(row=row_idx, column=0, padx=20, pady=2, sticky="w")
        row_idx += 1

        self.label_speedup_dist = ctk.CTkLabel(self.sidebar, text="Dist: -- s (Speedup: --x)", text_color="gray60", font=ctk.CTkFont(size=12))
        self.label_speedup_dist.grid(row=row_idx, column=0, padx=20, pady=2, sticky="w")
        row_idx += 1

        self.label_status = ctk.CTkLabel(self.sidebar, text="● Ocioso", font=ctk.CTkFont(size=14, weight="bold"), text_color="#4CAF50")
        self.label_status.grid(row=row_idx, column=0, padx=20, pady=(20, 10), sticky="w")

    def construir_painel_principal(self):
        """Constrói a área principal onde ficam os botões de execução e as abas."""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
        self.main_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        self.btn_seq = ctk.CTkButton(self.main_frame, text="▶ Executar Sequencial", height=45, font=ctk.CTkFont(size=14, weight="bold"), command=self.btn_action_sequencial)
        self.btn_seq.grid(row=0, column=0, padx=5, pady=(0, 10), sticky="ew")

        self.btn_par = ctk.CTkButton(self.main_frame, text="▶ Executar Paralelo", height=45, font=ctk.CTkFont(size=14, weight="bold"), fg_color="#8E44AD", hover_color="#732D91", command=self.btn_action_paralelo)
        self.btn_par.grid(row=0, column=1, padx=5, pady=(0, 10), sticky="ew")

        self.btn_dist = ctk.CTkButton(self.main_frame, text="▶ Executar Distribuído", height=45, font=ctk.CTkFont(size=14, weight="bold"), fg_color="#27AE60", hover_color="#1E8449", command=self.btn_action_distribuido)
        self.btn_dist.grid(row=0, column=2, padx=5, pady=(0, 10), sticky="ew")

        self.progressbar = ctk.CTkProgressBar(self.main_frame, height=8)
        self.progressbar.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        self.progressbar.set(0)

        self.tabs = ctk.CTkTabview(self.main_frame)
        self.tabs.grid(row=2, column=0, columnspan=3, sticky="nswe")
        
        self.tab_console = self.tabs.add("Console / Logs")
        self.tab_metricas = self.tabs.add("Métricas e Telemetria")

        self.construir_aba_console()
        self.construir_aba_metricas()

    def construir_aba_console(self):
        self.tab_console.grid_columnconfigure(0, weight=1)
        self.tab_console.grid_rowconfigure(0, weight=1)
        self.text_console = ctk.CTkTextbox(self.tab_console, state="disabled", font=ctk.CTkFont(family="Courier", size=12), wrap="word")
        self.text_console.grid(row=0, column=0, sticky="nswe", padx=5, pady=5)

    def construir_aba_metricas(self):
        self.tab_metricas.grid_columnconfigure(0, weight=1)
        self.tab_metricas.grid_rowconfigure(0, weight=1)
        
        self.scroll_metricas = ctk.CTkScrollableFrame(self.tab_metricas, fg_color="transparent")
        self.scroll_metricas.grid(row=0, column=0, sticky="nswe", padx=5, pady=5)
        self.scroll_metricas.grid_columnconfigure(0, weight=1)

        self.lbl_placeholder_metricas = ctk.CTkLabel(self.scroll_metricas, text="Execute uma simulação (Distribuída ou Paralela) para visualizar os gráficos de telemetria.", font=ctk.CTkFont(size=14), text_color="gray50")
        self.lbl_placeholder_metricas.pack(pady=50)

        self.container_graficos = ctk.CTkFrame(self.scroll_metricas, fg_color="transparent")
        self.container_graficos.pack(fill="both", expand=True)
        self.container_graficos.grid_columnconfigure(0, weight=1)
        
        self._imagens_carregadas = []

    def mostrar_boas_vindas(self):
        print("=" * 60)
        print(" FAKE NEWS SIMULATOR - Painel Integrado de Controle")
        print("=" * 60)
        print(" Selecione os parâmetros na barra lateral.")
        print(" Para o modo Distribuído:")
        print("   1. Certifique-se de iniciar o Pyro5 nameserver: python3 -m Pyro5.nameserver --port 9090")
        print("   2. Inicie os workers em outros terminais: python3 -m distribuido.main_worker")
        print("=" * 60 + "\\n")

    def alterar_estado_botoes(self, ativo: bool):
        estado = "normal" if ativo else "disabled"
        self.btn_seq.configure(state=estado)
        self.btn_par.configure(state=estado)
        self.btn_dist.configure(state=estado)
        self.is_running = not ativo
        if not ativo:
            self.progressbar.set(0)
            self.label_status.configure(text="● Processando...", text_color="#F39C12")
        else:
            self.progressbar.set(1.0)
            self.label_status.configure(text="● Concluído", text_color="#4CAF50")

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
            print(f"[Erro de Configuração] Verifique os valores inseridos. Erro: {e}")
            return None

    def atualizar_speedup(self, modalidade, tempo_total):
        self.tempos_execucao[modalidade] = tempo_total
        
        t_seq = self.tempos_execucao["Sequencial"]
        t_par = self.tempos_execucao["Paralela"]
        t_dist = self.tempos_execucao["Distribuída"]

        if t_seq:
            self.label_speedup_seq.configure(text=f"Seq: {t_seq:.4f} s", text_color="white")
        
        if t_par:
            if t_seq:
                speedup_p = t_seq / t_par
                self.label_speedup_par.configure(text=f"Par: {t_par:.4f} s (Speedup: {speedup_p:.2f}x)", text_color="#3498DB")
            else:
                self.label_speedup_par.configure(text=f"Par: {t_par:.4f} s", text_color="white")
                
        if t_dist:
            if t_seq:
                speedup_d = t_seq / t_dist
                self.label_speedup_dist.configure(text=f"Dist: {t_dist:.4f} s (Speedup: {speedup_d:.2f}x)", text_color="#3498DB")
            else:
                self.label_speedup_dist.configure(text=f"Dist: {t_dist:.4f} s", text_color="white")

    def carregar_graficos_telemetria(self):
        """No Linux, quando o ImageTk não está disponível, abrimos os gráficos externamente."""
        for widget in self.container_graficos.winfo_children():
            widget.destroy()
            
        self.lbl_placeholder_metricas.pack_forget()
        
        ctk.CTkLabel(self.container_graficos, text="✅ Gráficos de Telemetria Gerados com Sucesso!", font=ctk.CTkFont(size=18, weight="bold"), text_color="#2ecc71").pack(pady=(40, 10))
        ctk.CTkLabel(self.container_graficos, text="Os arquivos PNG foram salvos na pasta 'metricas/'.", font=ctk.CTkFont(size=14)).pack(pady=5)
        
        def abrir_pasta():
            import subprocess
            try:
                subprocess.Popen(["xdg-open", METRICAS_DIR])
            except:
                print("[Erro] Não foi possível abrir a pasta automaticamente.")

        btn_abrir = ctk.CTkButton(self.container_graficos, text="📂 Abrir Pasta de Gráficos", height=40, font=ctk.CTkFont(weight="bold"), command=abrir_pasta)
        btn_abrir.pack(pady=20)


    def btn_action_sequencial(self):
        if self.is_running: return
        params = self.ler_parametros()
        if not params: return
        
        self.alterar_estado_botoes(False)
        self.tabs.set("Console / Logs")
        
        threading.Thread(target=self._rodar_sequencial_worker, args=(params,), daemon=True).start()

    def _rodar_sequencial_worker(self, params):
        try:
            from main_sequencial import executar_sequencial
            
            matriz, tempo_total = executar_sequencial(
                linhas=params["linhas"],
                colunas=params["colunas"],
                geracoes=params["geracoes"],
                percentual_espalhadores=params["espalhadores"],
                limiar=params["limiar"],
                semente=params["semente"],
                mostrar_grade=False
            )
            
            self.after(0, self.atualizar_speedup, "Sequencial", tempo_total)
            
        except Exception as e:
            print(f"\\n[ERRO NA EXECUÇÃO SEQUENCIAL]: {e}")
        finally:
            self.after(0, self.alterar_estado_botoes, True)

    def btn_action_distribuido(self):
        if self.is_running: return
        params = self.ler_parametros()
        if not params: return
        
        self.alterar_estado_botoes(False)
        self.tabs.set("Console / Logs")
        
        threading.Thread(target=self._rodar_distribuido_worker, args=(params,), daemon=True).start()

    def _rodar_distribuido_worker(self, params):
        try:
            import Pyro5.api
            import Pyro5.server
            from distribuido.mestre import MestreDistribuido
            from core.utils import Cronometro
            from core.automato import contar_estados, IGNORANTE, ESPALHADOR, INATIVO
            from core.metricas import RelatorioMetricas

            print("=> Iniciando Mestre Distribuído...")
            
            mestre = MestreDistribuido(
                linhas=params["linhas"], colunas=params["colunas"],
                geracoes=params["geracoes"], percentual_espalhadores=params["espalhadores"],
                limiar=params["limiar"], semente=params["semente"],
                num_workers=params["workers"]
            )

            daemon = Pyro5.server.Daemon(host="0.0.0.0")
            uri = daemon.register(mestre, objectId="mestre.fakenews.obj")
            
            try:
                ns = Pyro5.api.locate_ns(port=9090)
                ns.register("mestre.fakenews", uri)
            except Exception as e:
                print(f"[ERRO] Falha ao registrar no NameServer (a porta 9090 está aberta?): {e}")
                return

            thread_daemon = threading.Thread(target=daemon.requestLoop, daemon=True)
            thread_daemon.start()

            print(f"Aguardando conexão de {params['workers']} workers...")
            mestre.aguardar_workers()
            print("Todos os workers conectados! Processando...")

            crono = Cronometro()
            crono.iniciar()
            mestre.aguardar_resultado()
            crono.parar()

            matriz_final = mestre.obter_matriz_final()
            
            print("Processamento distribuído concluído. Gerando relatórios de telemetria...")
            
            metricas_raw = mestre.aguardar_metricas()
            relatorio = RelatorioMetricas(params["workers"])
            for mw in metricas_raw:
                relatorio.adicionar_metricas_worker(mw)
                
            relatorio.imprimir_resumo(crono.elapsed)
            relatorio.exportar_csv()
            relatorio.gerar_graficos()

            try:
                ns.remove("mestre.fakenews")
            except Exception: pass
            daemon.shutdown()

            self.after(0, self.atualizar_speedup, "Distribuída", crono.elapsed)
            self.after(0, self.carregar_graficos_telemetria)
            self.after(0, lambda: self.tabs.set("Métricas e Telemetria"))

        except Exception as e:
            print(f"\\n[ERRO NA EXECUÇÃO DISTRIBUÍDA]: {e}")
        finally:
            self.after(0, self.alterar_estado_botoes, True)

    def btn_action_paralelo(self):
        """
        Disparado quando o botão 'Executar Paralelo' é clicado.
        Esta é a CAMADA VISUAL. Não implementamos a lógica do paralelo aqui.
        """
        if self.is_running: return
        params = self.ler_parametros()
        if not params: return
        
        self.alterar_estado_botoes(False)
        self.tabs.set("Console / Logs")
        
        threading.Thread(target=self._rodar_paralelo_hook, args=(params,), daemon=True).start()

    def _rodar_paralelo_hook(self, params):
        try:
            from paralelo.mestre import MestreParalelo
            from core.utils import Cronometro
            
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

            print("Processamento paralelo concluído.")
            
            self.after(0, self.atualizar_speedup, "Paralela", crono.elapsed)

        except Exception as e:
            print(f"\\n[ERRO NA EXECUÇÃO PARALELA]: {e}")
        finally:
            self.after(0, self.alterar_estado_botoes, True)


if __name__ == "__main__":
    app = FakeNewsApp()
    app.mainloop()
