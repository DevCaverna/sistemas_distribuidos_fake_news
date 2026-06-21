# Módulo `core/comparativo.py`

Gera gráfico de barras comparativo entre as três modalidades de execução (Sequencial, Paralela, Distribuída) após todas terem sido executadas.

## Variável Global

`_resultados : dict[str, ResultadoExecucao]` — dicionário que acumula os resultados das execuções durante a sessão. Reseta quando o script reinicia.

## Funções

### `registrar_resultado(tipo, tempo_total, cpu_medio, rede_bytes=0)`

Registra o resultado da última execução para um tipo de modalidade.

| Parâmetro     | Tipo  | Descrição                                       |
| ------------- | ----- | ----------------------------------------------- |
| `tipo`        | str   | `"Sequencial"`, `"Paralela"` ou `"Distribuída"` |
| `tempo_total` | float | Tempo total de execução em segundos             |
| `cpu_medio`   | float | Uso médio de CPU (%)                            |
| `rede_bytes`  | int   | Total de bytes trafegados (0 se N/A)            |

### `todos_executados()`

Retorna `True` se as três modalidades já foram registradas na sessão atual.

### `gerar_comparativo()`

Gera um gráfico de barras com 3 subplots (tempo, CPU, rede) comparando as modalidades.

**Retorno:** `list[str]` — caminhos dos arquivos PNG gerados (ex: `metricas/comparativo.png`).

### `limpar_resultados()`

Limpa todos os resultados registrados (para reiniciar a comparação).

## Funcionamento

1. Cada runner (`rodar_sequencial`, `rodar_paralelo`, `rodar_distribuido`) chama `registrar_resultado()` ao finalizar.
2. A GUI chama `tentar_exibir_comparativo()` após cada execução.
3. Se `todos_executados()` retorna `True`, o gráfico comparativo é gerado e exibido na aba de métricas.

O gráfico é composto por três barras lado a lado para cada métrica, facilitando a comparação visual do desempenho entre as três abordagens.
