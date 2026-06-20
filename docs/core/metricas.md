# Modulo `core/metricas.py`

Sistema de telemetria para coleta, exportação e visualização de métricas de desempenho das tres modalidades de execução.

## `MetricasWorker`

Coletor executado dentro de cada worker (thread ou processo remoto). Registra por geração:

| Métrica               | Unidade | Descricao                                |
| --------------------- | ------- | ---------------------------------------- |
| `cpu_percent`         | %       | Uso de CPU do processo durante o calculo |
| `tempo_processamento` | ms      | Tempo gasto na funcao `calcular_geracao` |
| `tempo_comunicacao`   | ms      | Tempo gasto enviando/recebendo bordas    |
| `bytes_enviados`      | bytes   | Dados enviados na troca de bordas        |
| `bytes_recebidos`     | bytes   | Dados recebidos na troca de bordas       |

**Metodos:**

| Metodo                      | Descricao                                     |
| --------------------------- | --------------------------------------------- |
| `iniciar_processamento()`   | Marca início do calculo da geração atual      |
| `finalizar_processamento()` | Registra `cpu_percent` e tempo de calculo     |
| `iniciar_comunicacao()`     | Marca início da troca de bordas               |
| `finalizar_comunicacao()`   | Registra tempo e bytes da comunicação         |
| `exportar()`                | Retorna o registro da geração como dicionario |

## `RelatorioMetricas`

Consolida métricas de todos os workers e gera relatorios.

| Metodo                                 | Descricao                                         |
| -------------------------------------- | ------------------------------------------------- |
| `adicionar_metricas_worker(lista)`     | Adiciona registros de um worker                   |
| `exportar_csv()`                       | Salva `métricas/metricas_workers.csv`             |
| `gerar_graficos()`                     | Gera PNGs de telemetria (CPU, latência, gargalos) |
| `imprimir_resumo(tempo_total, rotulo)` | Exibe tabela formatada no console                 |

### Graficos Gerados

Todos salvos em `métricas/`:

| Arquivo                         | Conteudo                                    |
| ------------------------------- | ------------------------------------------- |
| `gargalos_rede_vs_cpu.png`      | Dispersao: latência de rede vs tempo de CPU |
| `processamento_vs_latencia.png` | Evolucao temporal por worker                |
| `profiling_tempos_barras.png`   | Barras empilhadas por geração               |
| `profiling_cpu.png`             | Consumo de CPU por worker ao longo do tempo |

### Normalizacao de CPU

O valor de `psutil.cpu_percent()` e dividido por `psutil.cpu_count()` para representar o percentual do sistema total (0-100%), em vez de percentual por nucleo (que poderia exceder 100% em maquinas multicore).
