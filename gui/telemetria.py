import os

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image
import customtkinter as ctk

METRICAS_DIR = "metricas"


def exibir_imagem_grafico(app, caminho, idx=0):
    try:
        img = plt.imread(caminho)
        h, w = img.shape[:2]
        ratio = h / w

        fig = plt.Figure(figsize=(5, 5 * ratio), dpi=100, facecolor="none")
        ax = fig.add_subplot(111)
        ax.imshow(img, aspect="equal")
        ax.axis("off")
        fig.subplots_adjust(0, 0, 1, 1)

        col = idx % 2
        row = (idx // 2) + 1  # row 0 reservado para o cabecalho
        figura_ref = {"fig": fig, "ratio": ratio}

        canvas = FigureCanvasTkAgg(fig, app.container_graficos)
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
        app.after_idle(_ajustar)

        caminho_abs = os.path.abspath(caminho)
        widget.bind(
            "<Button-1>",
            lambda e, p=caminho_abs: abrir_imagem_tela_cheia(p),
        )

        if not hasattr(app, "_figuras"):
            app._figuras = []
        app._figuras.append(fig)
    except Exception as e:
        print(f"[Aviso] Nao foi possivel exibir {caminho}: {e}")


def abrir_imagem_tela_cheia(caminho):
    try:
        janela = ctk.CTkToplevel()
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
        ctk_img = ctk.CTkImage(
            light_image=pil_red, dark_image=pil_red, size=(display_w, display_h)
        )
        label = ctk.CTkLabel(janela, image=ctk_img, text="")
        label.pack(expand=True, fill="both")

        def fechar(e=None):
            janela.attributes("-fullscreen", False)
            janela.destroy()

        label.bind("<Button-1>", fechar)
        janela.bind("<Escape>", fechar)
    except Exception as e:
        print(f"[Aviso] Erro ao expandir imagem: {e}")


def limpar_graficos(app):
    for widget in app.container_graficos.winfo_children():
        widget.destroy()
    if hasattr(app, "_figuras"):
        for fig in app._figuras:
            plt.close(fig)
        app._figuras.clear()
    app.lbl_placeholder_metricas.pack_forget()


def carregar_graficos_telemetria(app, caminhos_adicionais=None):
    limpar_graficos(app)

    ctk.CTkLabel(
        app.container_graficos,
        text="Graficos de Telemetria",
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color="#2ecc71",
    ).grid(row=0, column=0, columnspan=2, pady=(30, 10))

    padrao = [
        "comparativo.png",
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
            exibir_imagem_grafico(app, caminho, idx=len(exibidos))
            exibidos.append(caminho)

    print(f"[Telemetria] {len(exibidos)} grafico(s) carregado(s): "
          f"{[os.path.basename(p) for p in exibidos]}")

    if caminhos_adicionais:
        for caminho in caminhos_adicionais:
            if caminho and os.path.exists(caminho) and caminho not in exibidos:
                exibir_imagem_grafico(app, caminho, idx=len(exibidos))
                exibidos.append(caminho)

    if not exibidos:
        ctk.CTkLabel(
            app.container_graficos,
            text="Nenhum grafico encontrado em metricas/",
            font=ctk.CTkFont(size=14),
            text_color="gray50",
        ).pack(pady=20)


def tentar_exibir_comparativo(app):
    from core.comparativo import todos_executados, gerar_comparativo

    if todos_executados():
        print(
            "\n[Comparativo] Todos os tipos executados. "
            "Gerando grafico comparativo..."
        )
        gerar_comparativo()
        # O arquivo gerado (metricas/comparativo.png) sera exibido por
        # carregar_graficos_telemetria, que o inclui no topo do padrao.
