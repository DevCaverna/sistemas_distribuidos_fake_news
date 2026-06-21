# Versão Paralela (`paralelo/`)

Implementação paralela com `threading` nativo do Python, seguindo o padrão Mestre-Trabalhador.

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
- Barreira lógica: todos os workers devem completar o cálculo antes de iniciar a próxima geração.
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

### Divisão da Matriz

A matriz é dividida horizontalmente em `num_workers` fatias de tamanho aproximadamente igual. Se a divisão não for exata, o último worker absorve as linhas restantes.

### Determinismo

Com `num_workers=1` (sem ghost rows), o resultado é idêntico ao sequencial. Com 2+ workers, o determinismo entre execuções depende do escalonamento das threads (`Condition.acquire()`), podendo variar entre execuções devido a disputa por locks.

## CLI

```bash
python3 -m paralelo.main_paralelo [--param valor]
```

| Parâmetro        | Default | Descrição                          |
| ---------------- | ------- | ---------------------------------- |
| `--linhas`       | 100     | Número de linhas                   |
| `--colunas`      | 100     | Número de colunas                  |
| `--geracoes`     | 50      | Número de gerações                 |
| `--espalhadores` | 0.05    | Percentual inicial de espalhadores |
| `--limiar`       | 3       | Limiar de contágio                 |
| `--semente`      | 42      | Semente aleatória                  |
| `--workers`      | 2       | Número de threads workers          |

## Arquivos Gerados

| Arquivo                         | Conteúdo                            |
| ------------------------------- | ----------------------------------- |
| `metricas/metricas_workers.csv` | Métricas por worker/geração         |
| `metricas/profiling_*.png`      | Gráficos de CPU, latência, gargalos |
