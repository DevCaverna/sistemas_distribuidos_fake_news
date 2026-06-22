"""
core/comparativo.py — Graficos comparativos entre tipos de execução.

Armazena os resultados da última execução de cada modalidade (sequencial,
paralela, distribuida) e gera graficos comparativos de tempo e CPU.
"""

import os

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _MATPLOTLIB_OK = True
except ImportError:
    _MATPLOTLIB_OK = False

DIRETORIO = "metricas"


class ResultadoExecucao:
    """Armazena o resultado de uma execução para comparação."""

    def __init__(self, tipo, tempo_total, cpu_medio, rede_bytes=None):
        self.tipo = tipo
        self.tempo_total = tempo_total
        self.cpu_medio = cpu_medio
        self.rede_bytes = rede_bytes


_resultados = {}


def registrar_resultado(tipo, tempo_total, cpu_medio, rede_bytes=None):
    """Registra o resultado da última execução de um tipo."""
    _resultados[tipo] = ResultadoExecucao(tipo, tempo_total, cpu_medio, rede_bytes)


def todos_executados():
    """Retorna True se todos os 3 tipos ja foram executados."""
    return all(t in _resultados for t in ("Sequencial", "Paralela", "Distribuida"))


def gerar_comparativo():
    """Gera grafico comparativo entre todos os tipos registrados."""
    if not _MATPLOTLIB_OK:
        print("[Comparativo] matplotlib nao instalado. pip install matplotlib")
        return []

    if not _resultados:
        return []

    os.makedirs(DIRETORIO, exist_ok=True)
    arquivos = []

    tipos = list(_resultados.keys())
    tempos = [_resultados[t].tempo_total for t in tipos]
    cpus = [_resultados[t].cpu_medio for t in tipos]
    redes = [_resultados[t].rede_bytes for t in tipos]

    cores = {"Sequencial": "#3498db", "Paralela": "#8E44AD", "Distribuida": "#27AE60"}

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    bar_colors = [cores.get(t, "#95a5a6") for t in tipos]

    # --- Topo Esquerdo: Tempo Total ---
    axes[0, 0].bar(tipos, tempos, color=bar_colors, edgecolor="white", linewidth=1.5)
    axes[0, 0].set_ylabel("Tempo (s)")
    axes[0, 0].set_title("Tempo Total de Execucao", fontsize=13, weight="bold")
    axes[0, 0].grid(axis="y", alpha=0.3)
    for i, v in enumerate(tempos):
        axes[0, 0].text(i, v + max(tempos) * 0.02, f"{v:.4f}s",
                        ha="center", fontsize=10, fontweight="bold")

    # --- Topo Direito: CPU ---
    axes[0, 1].bar(tipos, cpus, color=bar_colors, edgecolor="white", linewidth=1.5)
    axes[0, 1].set_ylabel("CPU (%)")
    axes[0, 1].set_title("Consumo Medio de CPU", fontsize=13, weight="bold")
    axes[0, 1].grid(axis="y", alpha=0.3)
    max_cpu = max(cpus) if cpus else 1
    for i, v in enumerate(cpus):
        axes[0, 1].text(i, v + max_cpu * 0.02 + 0.5, f"{v:.1f}%",
                        ha="center", fontsize=10, fontweight="bold")

    # --- Baixo Esquerdo: Rede ---
    rede_labels = []
    for t, r in zip(tipos, redes):
        if r is not None:
            rede_labels.append(f"{r / 1024:.1f} KB")
        else:
            rede_labels.append("N/A")
    axes[1, 0].bar(tipos, [r if r is not None else 0 for r in redes],
                   color=bar_colors, edgecolor="white", linewidth=1.5)
    axes[1, 0].set_ylabel("Dados Trafegados (bytes)")
    axes[1, 0].set_title("Comunicacao de Rede", fontsize=13, weight="bold")
    axes[1, 0].grid(axis="y", alpha=0.3)
    for i, label in enumerate(rede_labels):
        axes[1, 0].text(i, (redes[i] or 0) + max([r or 0 for r in redes]) * 0.02,
                        label, ha="center", fontsize=10, fontweight="bold")

    # --- Baixo Direito: Speedup ---
    t_seq = _resultados.get("Sequencial")
    speedups = []
    speedup_labels = []
    for t in tipos:
        r = _resultados[t]
        if t_seq and r.tempo_total > 0:
            sp = t_seq.tempo_total / r.tempo_total
        else:
            sp = 1.0
        speedups.append(sp)
        speedup_labels.append(f"{sp:.2f}x")

    speedup_colors = [cores.get(t, "#95a5a6") for t in tipos]

    bars = axes[1, 1].bar(tipos, speedups, color=speedup_colors, edgecolor="white", linewidth=1.5)
    axes[1, 1].axhline(y=1.0, color="black", linestyle="--", linewidth=1.2, alpha=0.7, label="Baseline Sequencial (1x)")
    axes[1, 1].set_ylabel("Speedup")
    axes[1, 1].set_title("Speedup (T_seq / T_par)", fontsize=13, weight="bold")
    axes[1, 1].grid(axis="y", alpha=0.3)
    axes[1, 1].legend(fontsize=9)

    max_sp = max(speedups) if speedups else 1.0
    for i, v in enumerate(speedups):
        offset = max_sp * 0.03 if v >= 0 else -max_sp * 0.06
        va = "bottom" if v >= 0 else "top"
        axes[1, 1].text(i, v + offset, speedup_labels[i],
                        ha="center", va=va, fontsize=10, fontweight="bold",
                        color=cores.get(tipos[i], "#333333"))

    plt.tight_layout()
    caminho = os.path.join(DIRETORIO, "comparativo.png")
    fig.savefig(caminho, dpi=150)
    plt.close(fig)
    arquivos.append(caminho)

    return arquivos
