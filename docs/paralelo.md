# Versao Paralela (`paralelo/`)

Implementação paralela com `threading` nativo do Python, seguindo o padrao Mestre-Trabalhador.

## Arquitetura

```
MestreParalelo
  ├── Worker 0 (thread) — fatia [0..N1)
  ├── Worker 1 (thread) — fatia [N1..N2)
  ├── Worker 2 (thread) — fatia [N2..N3)
  └── ...
```

### Mestre (`mestre.py`)

Classe `MestreParalelo` que:

1. Cria a matriz global e divide em fatias horizontais (`fatiar_matriz`).
2. Dispara `num_workers` threads, cada uma processando sua fatia.
3. A cada geração:
   - Envia bordas para cada worker (`enviar_bordas`).
   - Workers calculam a nova geração localmente.
   - Workers retornam bordas para o mestre (`obter_ghosts`).
   - Mestre calcula ghost rows para cada worker (`_calcular_ghosts`).
4. Ao final, coleta métricas e remonta a matriz.

### Sincronização

- `threading.Condition` e `threading.Lock` para coordenar a troca de bordas.
- Barreira logica: todos os workers devem completar o calculo antes de iniciar a proxima geração.
- Ghost rows: cada worker recebe a última linha do worker anterior (ghost_topo) e a primeira linha do worker seguinte (ghost_base).

### Worker (`_worker_thread`)

Cada worker:

1. Aguarda sua fatia inicial do mestre.
2. Para cada geração:
   - Recebe ghost rows do mestre.
   - Executa `calcular_geracao(fatia, ..., ghost_topo, ghost_base)`.
   - Mede métricas via `MetricasWorker` (CPU, tempo de processamento).
   - Retorna bordas (primeira e última linha da fatia calculada) para o mestre.
3. Retorna fatia final e métricas ao mestre.

### Divisao da Matriz

A matriz e dividida horizontalmente em `num_workers` fatias de tamanho aproximadamente igual. Se a divisao nao for exata, o último worker absorve as linhas restantes.

### Determinismo

Com `num_workers=1` (sem ghost rows), o resultado e identico ao sequencial. Com 2+ workers, o determinismo entre execucoes depende do escalonamento das threads (`Condition.acquire()`), podendo variar entre execucoes devido a disputa por locks.

## CLI

```bash
python3 -m paralelo.main_paralelo [--param valor]
```

| Parametro        | Default | Descricao                          |
| ---------------- | ------- | ---------------------------------- |
| `--linhas`       | 100     | Numero de linhas                   |
| `--colunas`      | 100     | Numero de colunas                  |
| `--gerações`     | 50      | Numero de gerações                 |
| `--espalhadores` | 0.05    | Percentual inicial de espalhadores |
| `--limiar`       | 3       | Limiar de contagio                 |
| `--semente`      | 42      | Semente aleatória                  |
| `--workers`      | 2       | Numero de threads workers          |

## Arquivos Gerados

| Arquivo                         | Conteudo                            |
| ------------------------------- | ----------------------------------- |
| `métricas/metricas_workers.csv` | Métricas por worker/geração         |
| `métricas/profiling_*.png`      | Graficos de CPU, latência, gargalos |
