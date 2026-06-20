# Versao Distribuida (`distribuido/`)

Implementação distribuida com **Pyro5** (Python Remote Objects) para comunicação entre processos via RMI. Segue o padrao Mestre-Trabalhador com processos autonomos que podem estar em maquinas distintas.

## Arquitetura

```
┌──────────┐   descobre     ┌────────────┐
│  Name    │<─────────────> │   Mestre   │
│  Server  │    registra    │  (Pyro5)   │
└──────────┘                └─────┬──────┘
      │                           │
      │                     ┌─────┴──────┐
      │                     │  barreira  │
      │                     │  (troca de │
      │                     │   bordas)  │
      │                     └─────┬──────┘
      │                           │
      │               ┌───────────┼───────────┐
      │               │           │           │
   ┌──┴──────┐   ┌────┴────┐ ┌────┴────┐ ┌────┴────┐
   │ Worker 0│   │Worker 1 │ │Worker 2 │ │Worker 3 │
   └─────────┘   └─────────┘ └─────────┘ └─────────┘
```

### Componentes

**Name Server (NS):** Servico de descoberta do Pyro5. Workers e Mestre o consultam para se localizar mutuamente.

**Mestre (`mestre.py`):** Classe `MestreDistribuido` exposta como objeto Pyro5. Orquestra a simulação:

1. Registra-se no NS com o ID `"mestre.fakenews"`.
2. Aguarda que `num_workers` workers se conectem (`registrar_worker`).
3. A cada geração:
   - Workers chamam `obter_ghosts(wid)` — o mestre retorna as ghost rows calculadas.
   - Workers processam suas fatias localmente.
   - Workers chamam `enviar_bordas(wid, topo, base)` — o mestre armazena.
   - Mestre calcula novas ghost rows com `_calcular_ghosts()`.
4. Ao final, cada worker chama `enviar_resultado(wid, fatia, métricas)`.
5. Mestre remonta a matriz final e coleta métricas.

**Worker (`worker.py`):** Classe `WorkerDistribuido` executada como processo autonomo:

1. Conecta-se ao NS, obtem URI do mestre.
2. Chama `registrar_worker(wid)` — recebe sua fatia inicial, mapa de influenciadores e config.
3. Para cada geração:
   - Chama `obter_ghosts(wid)` — recebe ghost rows.
   - Calcula `calcular_geracao(fatia, ..., ghost_topo, ghost_base)`.
   - Aplica mídia via `aplicar_midia()` se configurado.
   - Chama `enviar_bordas(wid, topo, base)` — envia bordas calculadas.
4. Ao final, chama `enviar_resultado(wid, fatia_final, métricas)`.

### Protocolo de Comunicação

Toda comunicação e feita via RPC (chamada de metodo remoto Pyro5). A cada geração:

1. **Worker -> Mestre:** `obter_ghosts(wid)` — busca ghosts.
2. **Worker:** calcula nova geração localmente.
3. **Worker -> Mestre:** `enviar_bordas(wid, topo, base)` — entrega bordas.
4. **Mestre:** computa novas ghost rows para a proxima geração.

Ghost rows sao as linhas de fronteira entre fatias: cada worker recebe a última linha do worker anterior (ghost_topo) e a primeira linha do worker seguinte (ghost_base).

### Limpeza de Recursos

Ao finalizar, o mestre:

- Remove seu ID do NS (`ns.remove("mestre.fakenews")`).
- Desliga o daemon Pyro5 (`daemon.shutdown()`).
- Remove workers do seu registro interno.

## Execução Manual

```bash
# Terminal 1: Name Server
python3 -m Pyro5.nameserver --port 9090

# Terminal 2: Mestre (pode ficar rodando)
python3 -m distribuido.main_mestre --linhas 100 --colunas 100 --gerações 50 --workers 2

# Terminal 3+: Workers (um terminal cada)
python3 -m distribuido.main_worker --host localhost --porta-ns 9090
```

### Parametros do Mestre

| Parametro                | Default | Descricao                               |
| ------------------------ | ------- | --------------------------------------- |
| `--linhas`               | 100     | Numero de linhas                        |
| `--colunas`              | 100     | Numero de colunas                       |
| `--gerações`             | 50      | Numero de gerações                      |
| `--espalhadores`         | 0.05    | Percentual inicial de espalhadores      |
| `--limiar`               | 3       | Limiar de contagio                      |
| `--semente`              | 42      | Semente aleatória                       |
| `--workers`              | 2       | Quantidade de workers                   |
| `--host`                 | 0.0.0.0 | IP do Mestre                            |
| `--porta-ns`             | 9090    | Porta do Name Server                    |
| `--influenciadores`      | True    | Ativa/desativa influenciadores digitais |
| `--usar-midia`           | True    | Ativa/desativa efeito mídia             |
| `--geracao-midia`        | 5       | Geração a partir da qual a mídia age    |
| `--prob-sensacionalista` | 0.08    | Probabilidade de mídia disseminar fake  |

### Parametros do Worker

| Parametro    | Default     | Descricao                            |
| ------------ | ----------- | ------------------------------------ |
| `--host`     | `localhost` | IP do Name Server                    |
| `--porta-ns` | 9090        | Porta do Name Server                 |
| `--wid`      | auto        | ID do worker (atribuido pelo mestre) |

## Arquivos Gerados

Os mesmos da versao paralela: `métricas/metricas_workers.csv` e graficos de telemetria.
