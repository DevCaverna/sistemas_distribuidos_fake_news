# Propagacao de Fake News em Sistemas Paralelos e Distribuidos

Este projeto simula a propagacao de fake news em uma populacao (matriz bidimensional) baseada em automatos celulares e vizinhanca de Moore. O objetivo principal e evoluir uma aplicacao sequencial para versoes **paralela (Threads)** e **distribuida (Pyro5 RMI)**, avaliando speedup, eficiencia e escalabilidade.

## Estrutura do Projeto

```text
.
├── core/
│   ├── automato.py        # Logica de transicao de estados (Moore + Influenciadores 5x5)
│   ├── metricas.py        # Telemetria: MetricasWorker, RelatorioMetricas, graficos
│   ├── comparativo.py     # Grafico comparativo entre os 3 tipos de execucao
│   └── utils.py           # Matriz, influenciadores, fatiamento, cronometro
├── paralelo/              # Versao paralela com threads (MestreParalelo + workers)
├── distribuido/           # Versao distribuida via Pyro5 RMI
├── app_gui.py             # Interface grafica (CustomTkinter + matplotlib inline)
├── main_sequencial.py     # Entry point sequencial (com metricas de CPU por geracao)
└── FakeNews(Professor).py # Codigo sequencial original do professor
```

## Executando o Projeto

### Instalacao

```bash
pip install -r requirements.txt
```

A interface grafica tambem requer o pacote de sistema `python3-tk`:

```bash
sudo apt-get install python3-tk
```

### Versao Sequencial

```bash
python3 main_sequencial.py
```

Gera metricas de CPU e tempo por geracao em `metricas/metricas_sequencial.csv` e `metricas/metricas_sequencial.png`.

### Versao Paralela (Threads)

```bash
python3 -m paralelo.main_paralelo --linhas 100 --colunas 100 --geracoes 50 --workers 4
```

Gera metricas por worker em `metricas/metricas_workers.csv` e graficos de telemetria (CPU, latencia, processamento).

### Versao Distribuida (Pyro5)

A versao distribuida requer tres etapas (terminais separados ou maquinas distintas):

```bash
# 1. Iniciar o Name Server
python3 -m Pyro5.nameserver --port 9090

# 2. Iniciar o Mestre
python3 -m distribuido.main_mestre --linhas 100 --colunas 100 --geracoes 50 --workers 2

# 3. Iniciar os Workers (um terminal por worker)
python3 -m distribuido.main_worker --host localhost --porta-ns 9090
```

### Interface Grafica

```bash
python3 app_gui.py
```

A GUI integra todas as tres modalidades:
- **Sequencial**: executa e gera metricas de CPU
- **Paralelo**: executa com pool de threads, metricas e graficos
- **Distribuido**: inicia automaticamente workers em background (locais), gera metricas

A aba "Metricas e Telemetria" exibe graficos inline. Apos executar as tres modalidades, um grafico comparativo e gerado automaticamente em `metricas/comparativo.png`.

## Metricas e Telemetria

### Metricas Coletadas

| Metrica                    | Sequencial | Paralelo | Distribuido |
|----------------------------|:----------:|:--------:|:-----------:|
| Tempo total (s)            | Sim        | Sim      | Sim         |
| CPU por geracao (%)        | Sim        | Sim      | Sim         |
| Tempo de processamento (ms)| Por geracao| Por worker/geracao | Por worker/geracao |
| Latencia de rede (ms)      | N/A        | Sincronia local | Sim (RPC) |
| Dados trafegados (bytes)   | N/A        | Sim      | Sim         |

### Graficos Gerados

Todos os graficos sao salvos em `metricas/`:

- `metricas_sequencial.png` — CPU e tempo por geracao (sequencial)
- `gargalos_rede_vs_cpu.png` — Dispersao latencia vs processamento (paralelo/distribuido)
- `processamento_vs_latencia.png` — Evolucao temporal por worker
- `profiling_tempos_barras.png` — Barras por geracao
- `profiling_cpu.png` — Consumo de CPU por worker
- `comparativo.png` — Barras comparativas entre os 3 tipos (tempo, CPU, rede)

## Parametros (Mestre Distribuido / Paralelo)

| Parametro        | Default | Descricao                          |
|------------------|---------|------------------------------------|
| `--linhas`       | 100     | Numero de linhas da matriz         |
| `--colunas`      | 100     | Numero de colunas da matriz        |
| `--geracoes`     | 50      | Numero de geracoes                 |
| `--espalhadores` | 0.05    | Percentual inicial de espalhadores |
| `--limiar`       | 3       | Limiar de contagio                 |
| `--semente`      | 42      | Semente aleatoria                  |
| `--workers`      | 2       | Quantidade de workers/threads      |
| `--host`         | 0.0.0.0 | IP do Mestre (distribuido)         |
| `--porta-ns`     | 9090    | Porta do Name Server               |

## Melhorias em Relacao ao Modelo Base

### Influenciadores Digitais

O modelo base foi estendido com o agente **Influenciador Digital**, que simula perfis de alto impacto:

| Parametro                    | Valor                                                  |
|------------------------------|--------------------------------------------------------|
| Distribuicao Inicial         | 1% da populacao total (mapeamento estatico)            |
| Vizinhanca                   | Bloco 5x5 (ate 24 vizinhos), ao inves de Moore 3x3    |
| Probabilidade de Transmissao | Sorteada uniformemente entre 45% e 60% por tentativa  |

Flag: `--influenciadores` (padrao `True`).

### Efeito Midia

A **midia** comeca a atuar a partir de uma geracao configuravel (`--geracao-midia`, padrao 5):

| Efeito              | Chance | Consequencia            |
|---------------------|--------|-------------------------|
| Dissemina fake news | 8%     | IGNORANTE -> ESPALHADOR |
| Combate fake news   | 92%    | IGNORANTE -> INATIVO    |

A cada geracao, 15% dos IGNORANTES sao alcancados. A probabilidade sensacionalista e configuravel via `--prob-sensacionalista` (padrao `0.08`).

### Grafico Comparativo

Apos executar as tres modalidades (sequencial, paralela, distribuida), um grafico de barras e gerado comparando tempo total, CPU media e dados de rede (quando aplicavel).

## Documentacao Adicional

- [Enunciado do Trabalho](enunciado.md)
- [Arquitetura do Sistema Distribuido](arquitetura.md)
- [Divisao de Tarefas (Roadmap)](tasks.md)
