# Versão Paralela (`paralelo/`)

Implementação paralela com **multiprocessing** nativo do Python, seguindo o padrão Mestre-Trabalhador. Cada worker é um **processo separado** com seu próprio interpretador e GIL, garantindo **paralelismo real em múltiplos núcleos de CPU** para tarefas CPU-bound.

## Arquitetura

```
MestreParalelo
  ├── Worker 0 (processo) — fatia [0..N1)
  ├── Worker 1 (processo) — fatia [N1..N2)
  ├── Worker 2 (processo) — fatia [N2..N3)
  └── ...
```

### Mestre (`mestre.py`)

Classe `MestreParalelo` que:

1. Cria a matriz global e divide em fatias horizontais (`fatiar_matriz`).
2. Dispara `num_workers` processos, cada um processando sua fatia.
3. A cada geração:
   - Envia bordas para cada worker (`enviar_bordas`).
   - Workers calculam a nova geração localmente em paralelo real.
   - Workers retornam bordas para o mestre (`obter_ghosts`).
   - Mestre calcula ghost rows para cada worker (`_calcular_ghosts`).
4. Ao final, coleta métricas e remonta a matriz.

### Sincronização

- `multiprocessing.Condition` e `multiprocessing.Lock` para coordenar a troca de bordas entre processos.
- Barreira lógica: todos os workers devem completar o cálculo antes de iniciar a próxima geração.
- `multiprocessing.Manager.dict()` para compartilhar dados das bordas entre processos.
- Ghost rows: cada worker recebe a última linha do worker anterior (ghost_topo) e a primeira linha do worker seguinte (ghost_base).

### Worker (`_worker_thread`)

Cada worker (processo):

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

Com `num_workers=1` (sem ghost rows), o resultado é idêntico ao sequencial. Com 2+ workers, o determinismo entre execuções depende da ordem de aquisição dos locks do multiprocessing, podendo variar entre execuções.

## Por que multiprocessing em vez de threading?

Em CPython, o **GIL (Global Interpreter Lock)** impede que threads executem bytecode Python em paralelo em múltiplos núcleos. Para tarefas CPU-bound (como a simulação do autômato), o `threading` oferece apenas **concorrência** (revezamento), não **paralelismo** real. O `multiprocessing` cria processos independentes, cada um com seu próprio GIL, permitindo execução genuinamente paralela em todos os núcleos disponíveis.

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
| `--workers`      | 2       | Número de processos workers        |

## Arquivos Gerados

| Arquivo                         | Conteúdo                            |
| ------------------------------- | ----------------------------------- |
| `metricas/metricas_workers.csv` | Métricas por worker/geração         |
| `metricas/profiling_*.png`      | Gráficos de CPU, latência, gargalos |
