# Modulo `core/comparativo.py`

Gera grafico de barras comparativo entre as tres modalidades de execução (Sequencial, Paralela, Distribuida) apos todas terem sido executadas.

## Variavel Global

`_resultados : dict[str, ResultadoExecucao]` — dicionario que acumula os resultados das execucoes durante a sessao. Reseta quando o script reinicia.

## Funcoes

### `registrar_resultado(tipo, tempo_total, cpu_medio, rede_bytes=0)`

Registra o resultado da última execução para um tipo de modalidade.

| Parametro     | Tipo  | Descricao                                       |
| ------------- | ----- | ----------------------------------------------- |
| `tipo`        | str   | `"Sequencial"`, `"Paralela"` ou `"Distribuida"` |
| `tempo_total` | float | Tempo total de execução em segundos             |
| `cpu_medio`   | float | Uso medio de CPU (%)                            |
| `rede_bytes`  | int   | Total de bytes trafegados (0 se N/A)            |

### `todos_executados()`

Retorna `True` se as tres modalidades ja foram registradas na sessao atual.

### `gerar_comparativo()`

Gera um grafico de barras com 3 subplots (tempo, CPU, rede) comparando as modalidades.

**Retorno:** `list[str]` — caminhos dos arquivos PNG gerados (ex: `métricas/comparativo.png`).

### `limpar_resultados()`

Limpa todos os resultados registrados (para reiniciar a comparação).

## Funcionamento

1. Cada runner (`rodar_sequencial`, `rodar_paralelo`, `rodar_distribuido`) chama `registrar_resultado()` ao finalizar.
2. A GUI chama `tentar_exibir_comparativo()` apos cada execução.
3. Se `todos_executados()` retorna `True`, o grafico comparativo e gerado e exibido na aba de métricas.

O grafico e composto por tres barras lado a lado para cada métrica, facilitando a comparação visual do desempenho entre as tres abordagens.
