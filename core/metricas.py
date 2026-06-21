"""
core/métricas.py — Telemetria e profiling do sistema distribuído.

Coleta métricas detalhadas de cada Worker (CPU, tempo de processamento,
latência de rede) e consolida no Master para exportação em CSV e geração
automática de gráficos com matplotlib.
"""

import csv
import os
import time

import psutil


class MetricasWorker:
    """Coletor de métricas executado dentro de cada Worker.

    Registra, para cada geração:
      - % de CPU utilizado durante o cálculo
      - Tempo exato gasto na função de cálculo (processamento)
      - Tempo gasto aguardando a rede (latência)
    """

    def __init__(self, worker_id):
        self.worker_id = worker_id
        self._registros = []
        self._processo = psutil.Process()
        self._t0 = None
        self._tempo_proc = 0.0

    def iniciar_processamento(self):
        self._processo.cpu_percent()
        self._t0 = time.perf_counter()

    def finalizar_processamento(self):
        self._tempo_proc = time.perf_counter() - self._t0
        raw_cpu = self._processo.cpu_percent()
        self._cpu_percent = raw_cpu / psutil.cpu_count()

    def iniciar_comunicacao(self):
        self._t0 = time.perf_counter()

    def finalizar_comunicacao(self):
        tempo_rede = time.perf_counter() - self._t0
        self._registros.append({
            "processamento": self._tempo_proc,
            "latencia_rede": tempo_rede,
            "cpu_percent": self._cpu_percent,
        })

    def exportar(self):
        """Retorna lista de dicts serializável para envio via Pyro5."""
        resultado = []
        for g, reg in enumerate(self._registros, start=1):
            resultado.append({
                "worker_id": self.worker_id,
                "geracao": g,
                "tempo_processamento": reg["processamento"],
                "latencia_rede": reg["latencia_rede"],
                "cpu_percent": reg["cpu_percent"],
            })
        return resultado


class RelatorioMetricas:
    """Consolida métricas de todos os Workers e gera relatórios."""

    def __init__(self, num_workers, diretorio_saida="metricas"):
        self.num_workers = num_workers
        self.diretorio_saida = diretorio_saida
        self._dados = []

    def adicionar_metricas_worker(self, metricas_worker):
        self._dados.extend(metricas_worker)

    def exportar_csv(self):
        os.makedirs(self.diretorio_saida, exist_ok=True)
        caminho = os.path.join(self.diretorio_saida, "metricas_workers.csv")

        campos = [
            "worker_id", "geracao",
            "tempo_processamento", "latencia_rede",
            "cpu_percent", "tempo_total",
        ]

        with open(caminho, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            for reg in sorted(self._dados, key=lambda r: (r["worker_id"], r["geracao"])):
                reg["tempo_total"] = reg["tempo_processamento"] + reg["latencia_rede"]
                writer.writerow(reg)

        return caminho

    def gerar_graficos(self):
        try:
            import pandas as pd
            import seaborn as sns
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            print("[Métricas] pandas, seaborn ou matplotlib não instalados. Use pip para instalar.")
            return []
        
        os.makedirs(self.diretorio_saida, exist_ok=True)
        arquivos = []

        df = pd.DataFrame(self._dados)
        if df.empty:
            return []
            
        df["tempo_processamento"] = df["tempo_processamento"] * 1000
        df["latencia_rede"] = df["latencia_rede"] * 1000

        sns.set_theme(style="whitegrid", context="talk")

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.scatterplot(
            data=df, x="tempo_processamento", y="latencia_rede", 
            hue="worker_id", palette="deep", s=100, alpha=0.8, ax=ax
        )
        
        idx_max_lat = df["latencia_rede"].idxmax()
        outlier = df.loc[idx_max_lat]
        
        ax.annotate(
            f"W{int(outlier['worker_id'])} - Geração {int(outlier['geracao'])}",
            xy=(outlier["tempo_processamento"], outlier["latencia_rede"]),
            xytext=(15, -15), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="#f1c40f", alpha=0.8),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0", color="gray", lw=1.5)
        )
        
        max_val = max(df["tempo_processamento"].max(), df["latencia_rede"].max())
        if pd.isna(max_val) or max_val <= 0: max_val = 1
        ax.plot([0, max_val], [0, max_val], "r--", alpha=0.5, label="Equilíbrio 1:1")

        ax.set_xlabel("Tempo de Processamento (ms)", fontsize=12)
        ax.set_ylabel("Latência de Rede (ms)", fontsize=12)
        ax.set_title("Gargalos: Latência de Rede vs. Velocidade de Processamento", fontsize=14, weight="bold")
        ax.legend(title="Worker", fontsize=10)
        plt.tight_layout()
        
        caminho1 = os.path.join(self.diretorio_saida, "gargalos_rede_vs_cpu.png")
        fig.savefig(caminho1, dpi=150)
        plt.close(fig)
        arquivos.append(caminho1)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        sns.lineplot(data=df, x="geracao", y="tempo_processamento", hue="worker_id", palette="deep", ax=ax1, marker="o", lw=2)
        ax1.set_title("Evolução do Tempo de Processamento", fontsize=13, weight="bold")
        ax1.set_ylabel("Processamento (ms)", fontsize=11)
        ax1.legend(title="Worker", loc="upper right")
        
        sns.lineplot(data=df, x="geracao", y="latencia_rede", hue="worker_id", palette="deep", ax=ax2, marker="s", linestyle="--", lw=2)
        ax2.set_title("Evolução da Latência de Rede", fontsize=13, weight="bold")
        ax2.set_ylabel("Latência (ms)", fontsize=11)
        ax2.set_xlabel("Geração", fontsize=12)
        ax2.legend(title="Worker", loc="upper right")

        plt.tight_layout()
        caminho2 = os.path.join(self.diretorio_saida, "processamento_vs_latencia.png")
        fig.savefig(caminho2, dpi=150)
        plt.close(fig)
        arquivos.append(caminho2)

        
        df_melted = df.melt(
            id_vars=["geracao", "worker_id"], 
            value_vars=["tempo_processamento", "latencia_rede"],
            var_name="Metrica", value_name="Tempo_ms"
        )
        df_melted["Metrica"] = df_melted["Metrica"].replace({
            "tempo_processamento": "Processamento",
            "latencia_rede": "Latência"
        })
        
        fig, ax = plt.subplots(figsize=(14, 6))
        sns.barplot(
            data=df_melted, x="geracao", y="Tempo_ms", hue="Metrica", 
            errorbar=None, palette=["#3498db", "#e74c3c"], ax=ax
        )
        
        if df["geracao"].max() > 20:
            for ind, label in enumerate(ax.get_xticklabels()):
                label.set_visible(ind % 5 == 0)
                    
        ax.set_title("Distribuição do Tempo de Execução por Geração", fontsize=14, weight="bold")
        ax.set_xlabel("Geração", fontsize=12)
        ax.set_ylabel("Tempo (ms)", fontsize=12)
        ax.legend(title="Métrica")
        plt.tight_layout()
        
        caminho3a = os.path.join(self.diretorio_saida, "profiling_tempos_barras.png")
        fig.savefig(caminho3a, dpi=150)
        plt.close(fig)
        arquivos.append(caminho3a)
        
        fig, ax = plt.subplots(figsize=(12, 5))
        sns.lineplot(
            data=df, x="geracao", y="cpu_percent", hue="worker_id", 
            palette="Set2", lw=3, marker="D", markersize=6, ax=ax
        )
        ax.set_title("Consumo de CPU por Worker ao Longo do Tempo", fontsize=14, weight="bold")
        ax.set_ylabel("CPU (%)", fontsize=12)
        ax.set_xlabel("Geração", fontsize=12)
        ax.legend(title="Worker")
        plt.tight_layout()
        
        caminho3b = os.path.join(self.diretorio_saida, "profiling_cpu.png")
        fig.savefig(caminho3b, dpi=150)
        plt.close(fig)
        arquivos.append(caminho3b)

        return arquivos

    def imprimir_resumo(self, tempo_total, rotulo="SISTEMA DISTRIBUÍDO"):
        dados_por_worker = {}
        for reg in self._dados:
            wid = reg["worker_id"]
            dados_por_worker.setdefault(wid, []).append(reg)

        print()
        print("=" * 60)
        print(f"  MÉTRICAS DO SISTEMA {rotulo}")
        print("=" * 60)

        for wid in sorted(dados_por_worker):
            regs = dados_por_worker[wid]
            total_proc = sum(r["tempo_processamento"] for r in regs)
            total_rede = sum(r["latencia_rede"] for r in regs)
            media_cpu = sum(r["cpu_percent"] for r in regs) / len(regs)
            total = total_proc + total_rede
            pct_rede = total_rede / total * 100 if total > 0 else 0

            print(f"  Worker {wid}:")
            print(f"    Processamento: {total_proc:.4f}s")
            print(f"    Latência Rede: {total_rede:.4f}s")
            print(f"    CPU Médio:     {media_cpu:.1f}%")
            print(f"    Overhead Rede: {pct_rede:.1f}%")

        total_proc_global = sum(r["tempo_processamento"] for r in self._dados)
        total_rede_global = sum(r["latencia_rede"] for r in self._dados)
        media_cpu_global = sum(r["cpu_percent"] for r in self._dados) / len(self._dados) if self._dados else 0
        total_global = total_proc_global + total_rede_global
        pct_global = total_rede_global / total_global * 100 if total_global > 0 else 0

        print("-" * 60)
        print(f"  Total processamento: {total_proc_global:.4f}s")
        print(f"  Total latência rede: {total_rede_global:.4f}s")
        print(f"  CPU médio global:    {media_cpu_global:.1f}%")
        print(f"  Overhead rede:       {pct_global:.1f}%")
        print(f"  Tempo real (Master): {tempo_total:.4f}s")
        print("=" * 60)
