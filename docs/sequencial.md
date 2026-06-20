# Versao Sequencial (`main_sequencial.py`)

Entry point e implementacao da versao sequencial refatorada.

## Fluxo de Execucao

1. Parsing de argumentos CLI via `argparse`.
2. Criacao da matriz inicial com `criar_matriz()`.
3. Para cada geracao:
   - Calcula a nova geracao com `calcular_geracao()`.
   - Aplica efeito midia com `aplicar_midia()` (a partir de `--geracao-midia`).
   - Coleta metricas de CPU (`psutil.cpu_percent()`) e tempo por geracao.
   - Conta estados com `contar_estados()`.
4. Exporta metricas para CSV e gera grafico ao final.

## CLI

```bash
python3 main_sequencial.py [--param valor]
```

| Parametro              | Default | Descricao                                     |
| ---------------------- | ------- | --------------------------------------------- |
| `--linhas`             | 100     | Numero de linhas                              |
| `--colunas`            | 100     | Numero de colunas                             |
| `--geracoes`           | 50      | Numero de geracoes                            |
| `--espalhadores`       | 0.05    | Percentual inicial de espalhadores            |
| `--limiar`             | 3       | Limiar de contagio (vizinhos necessarios)     |
| `--semente`            | 42      | Semente aleatoria para reproducibilidade      |
| `--grade`              | flag    | Imprime a grade no console a cada geracao     |
| `--influenciadores`    | True    | Ativa/desativa influenciadores digitais       |
| `--usar-midia`         | True    | Ativa/desativa efeito midia                   |
| `--geracao-midia`      | 5       | Geracao a partir da qual a midia atua         |
| `--prob-sensacionalista` | 0.08  | Probabilidade de midia disseminar fake news   |

## Retorno

A funcao `executar_sequencial()` retorna uma tupla de 3 elementos:

```python
(matriz, tempo_total, metricas)
```

- `matriz : list[list[int]]` — estado final da populacao.
- `tempo_total : float` — tempo total de execucao em segundos.
- `metricas : list[dict]` — lista com dicts de metricas por geracao.

## Arquivos Gerados

| Arquivo                               | Conteudo                              |
| ------------------------------------- | ------------------------------------- |
| `metricas/metricas_sequencial.csv`    | CPU e tempo por geracao               |
| `metricas/metricas_sequencial.png`    | Grafico de CPU e tempo por geracao    |
