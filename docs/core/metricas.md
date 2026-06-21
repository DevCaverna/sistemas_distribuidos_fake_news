# Módulo `core/metricas.py`

Sistema de telemetria para coleta, exportação e visualização de métricas de desempenho das três modalidades de execução.

## `MetricasWorker`

Coletor executado dentro de cada worker (thread ou processo remoto). Registra por geração:

| Métrica               | Unidade | Descrição                                |
| --------------------- | ------- | ---------------------------------------- |
| `cpu_percent`         | %       | Uso de CPU do processo durante o cálculo |
| `tempo_processamento` | ms      | Tempo gasto na função `calcular_geracao` |
| `tempo_comunicacao`   | ms      | Tempo gasto enviando/recebendo bordas    |

**Métodos:**

| Método                      | Descrição                                     |
| --------------------------- | --------------------------------------------- |
| `iniciar_processamento()`   | Marca início do cálculo da geração atual      |
| `finalizar_processamento()` | Registra `cpu_percent` e tempo de cálculo     |
| `iniciar_comunicacao()`     | Marca início da troca de bordas               |
| `finalizar_comunicacao()`   | Registra tempo de comunicação                 |
| `exportar()`                | Retorna o registro da geração como dicionário |

## `RelatorioMetricas`

Consolida métricas de todos os workers e gera relatórios.

| Método                                 | Descrição                                         |
| -------------------------------------- | ------------------------------------------------- |
| `adicionar_metricas_worker(lista)`     | Adiciona registros de um worker                   |
| `exportar_csv()`                       | Salva `metricas/metricas_workers.csv`             |
| `gerar_graficos()`                     | Gera PNGs de telemetria (CPU, latência, gargalos) |
| `imprimir_resumo(tempo_total, rotulo)` | Exibe tabela formatada no console                 |

### Gráficos Gerados

Todos salvos em `metricas/`:

| Arquivo                         | Conteúdo                                    |
| ------------------------------- | ------------------------------------------- |
| `gargalos_rede_vs_cpu.png`      | Dispersão: latência de rede vs tempo de CPU |
| `processamento_vs_latencia.png` | Evolução temporal por worker                |
| `profiling_tempos_barras.png`   | Barras empilhadas por geração               |
| `profiling_cpu.png`             | Consumo de CPU por worker ao longo do tempo |

### Normalização de CPU

O valor de `psutil.cpu_percent()` é dividido por `psutil.cpu_count()` para representar o percentual do sistema total (0-100%), em vez de percentual por núcleo (que poderia exceder 100% em máquinas multicore).
