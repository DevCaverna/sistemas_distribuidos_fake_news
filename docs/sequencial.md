# Versao Sequencial (`main_sequencial.py`)

Entry point e implementação da versao sequencial refatorada.

## Fluxo de Execução

1. Parsing de argumentos CLI via `argparse`.
2. Criacao da matriz inicial com `criar_matriz()`.
3. Para cada geração:
   - Calcula a nova geração com `calcular_geracao()`.
   - Aplica efeito mídia com `aplicar_midia()` (a partir de `--geracao-midia`).
   - Coleta métricas de CPU (`psutil.cpu_percent()`) e tempo por geração.
   - Conta estados com `contar_estados()`.
4. Exporta métricas para CSV e gera grafico ao final.

## CLI

```bash
python3 main_sequencial.py [--param valor]
```

| Parametro                | Default | Descricao                                   |
| ------------------------ | ------- | ------------------------------------------- |
| `--linhas`               | 100     | Numero de linhas                            |
| `--colunas`              | 100     | Numero de colunas                           |
| `--gerações`             | 50      | Numero de gerações                          |
| `--espalhadores`         | 0.05    | Percentual inicial de espalhadores          |
| `--limiar`               | 3       | Limiar de contagio (vizinhos necessarios)   |
| `--semente`              | 42      | Semente aleatória para reproducibilidade    |
| `--grade`                | flag    | Imprime a grade no console a cada geração   |
| `--influenciadores`      | True    | Ativa/desativa influenciadores digitais     |
| `--usar-midia`           | True    | Ativa/desativa efeito mídia                 |
| `--geracao-midia`        | 5       | Geração a partir da qual a mídia atua       |
| `--prob-sensacionalista` | 0.08    | Probabilidade de mídia disseminar fake news |

## Retorno

A funcao `executar_sequencial()` retorna uma tupla de 3 elementos:

```python
(matriz, tempo_total, métricas)
```

- `matriz : list[list[int]]` — estado final da população.
- `tempo_total : float` — tempo total de execução em segundos.
- `métricas : list[dict]` — lista com dicts de métricas por geração.

## Arquivos Gerados

| Arquivo                            | Conteudo                           |
| ---------------------------------- | ---------------------------------- |
| `métricas/metricas_sequencial.csv` | CPU e tempo por geração            |
| `métricas/metricas_sequencial.png` | Grafico de CPU e tempo por geração |
