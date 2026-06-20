import os
import sys
import threading

import customtkinter as ctk

from gui.console import RedirectorConsole
from gui.executores import rodar_sequencial, rodar_paralelo, rodar_distribuido

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CORES_ESTADOS = {
    0: (46, 204, 113),
    1: (231, 76, 60),
    2: (149, 165, 166),
}


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

    # ── Sidebar ──────────────────────────────────────────────────────────────

    def construir_sidebar(self):
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
        self.label_speedup_dist.grid(row=row_idx, column=0, padx=20, pady=2, sticky="w")
        row_idx += 1

        self.label_status = ctk.CTkLabel(
            self.sidebar, text="Ocioso",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4CAF50",
        )
        self.label_status.grid(row=row_idx, column=0, padx=20, pady=(20, 10), sticky="w")

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

    # ── Painel principal ────────────────────────────────────────────────────

    def construir_painel_principal(self):
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

    # ── Acoes dos botoes ─────────────────────────────────────────────────────

    def btn_action_sequencial(self):
        if self.is_running:
            return
        params = self.ler_parametros()
        if not params:
            return
        self.alterar_estado_botoes(False)
        self.tabs.set("Console / Logs")
        threading.Thread(
            target=rodar_sequencial, args=(self, params), daemon=True
        ).start()

    def btn_action_paralelo(self):
        if self.is_running:
            return
        params = self.ler_parametros()
        if not params:
            return
        self.alterar_estado_botoes(False)
        self.tabs.set("Console / Logs")
        threading.Thread(
            target=rodar_paralelo, args=(self, params), daemon=True
        ).start()

    def btn_action_distribuido(self):
        if self.is_running:
            return
        params = self.ler_parametros()
        if not params:
            return
        self.alterar_estado_botoes(False)
        self.tabs.set("Console / Logs")
        threading.Thread(
            target=rodar_distribuido, args=(self, params), daemon=True
        ).start()

    def mostrar_boas_vindas(self):
        print("=" * 60)
        print(" FAKE NEWS SIMULATOR - Painel Integrado de Controle")
        print("=" * 60)
        print(" Selecione os parametros na barra lateral.")
        print(" Para o modo Distribuido a GUI inicia workers localmente.")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    app = FakeNewsApp()
    app.mainloop()
