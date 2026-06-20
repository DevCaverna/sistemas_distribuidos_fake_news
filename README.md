# Propagacao de Fake News em Sistemas Paralelos e Distribuidos

Este projeto simula a propagacao de fake news em uma populacao (matriz bidimensional) baseada em automatos celulares e vizinhanca de Moore. O objetivo principal e evoluir uma aplicacao sequencial para versoes **paralela (Threads)** e **distribuida (Pyro5 RMI)**, avaliando speedup, eficiencia e escalabilidade.

## Estrutura do Projeto

O código está estruturado para maximizar o reaproveitamento lógico:

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

A versao paralela usa `threading` do Python e implementa o mesmo protocolo logico do Mestre-Trabalhador por meio de chamadas locais e primitivas de sincronizacao (Condition/Lock). Nao e necessaria biblioteca externa adicional.

Para executar:

```bash
python3 -m paralelo.main_paralelo --linhas 100 --colunas 100 --geracoes 50 --workers 4
```

Gera metricas por worker em `metricas/metricas_workers.csv` e graficos de telemetria (CPU, latencia, processamento).

### Versao Distribuida (Pyro5)

A versao distribuida usa o **Pyro5** para comunicacao remota entre processos. E necessario instalar a dependencia primeiro:

```bash
pip install Pyro5
```

A execucao e feita em **tres etapas** (em terminais/maquinas separadas):

**1. Iniciar o Name Server** (responsavel pelo servico de descoberta):

```bash
python3 -m Pyro5.nameserver --port 9090
```

**2. Iniciar o Mestre** (orquestrador, cria a matriz e coordena os workers):

```bash
python3 -m distribuido.main_mestre --linhas 100 --colunas 100 --geracoes 50 --workers 2
```

**3. Iniciar os Workers** (um terminal por worker, podem estar em maquinas distintas):

```bash
python3 -m distribuido.main_worker --host localhost --porta-ns 9090
```

> Os workers podem rodar em maquinas diferentes -- basta apontar `--host` para o IP da maquina onde o Name Server esta rodando.

**Parametros do Mestre:**

| Parametro                | Default | Descricao                                     |
| ------------------------ | ------- | --------------------------------------------- |
| `--linhas`               | 100     | Numero de linhas da matriz                    |
| `--colunas`              | 100     | Numero de colunas da matriz                   |
| `--geracoes`             | 50      | Numero de geracoes                            |
| `--espalhadores`         | 0.05    | Percentual inicial de espalhadores            |
| `--limiar`               | 3       | Limiar de contagio                            |
| `--semente`              | 42      | Semente aleatoria                             |
| `--workers`              | 2       | Quantidade de workers                         |
| `--host`                 | 0.0.0.0 | IP do Mestre                                  |
| `--porta-ns`             | 9090    | Porta do Name Server                          |
| `--influenciadores`      | True    | Ativa/desativa influenciadores digitais       |
| `--usar-midia`           | True    | Ativa/desativa efeito da midia                |
| `--geracao-midia`        | 5       | Geracao a partir da qual a midia age          |
| `--prob-sensacionalista` | 0.08    | Probabilidade de a midia disseminar fake news |

**Arquitetura:**

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

Cada worker processa uma fatia horizontal da matriz e troca linhas de borda (ghost rows) via Mestre a cada geracao.

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

### Grafico Comparativo

Apos executar as tres modalidades (sequencial, paralela, distribuida), um grafico de barras e gerado comparando tempo total, CPU media e dados de rede (quando aplicavel).

## Testes

### Configuracao do ambiente

Os testes usam um ambiente virtual Python (`venv`) para isolar as dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest Pyro5==5.16
```

### pytest

O **pytest** e o framework de testes usado no projeto. Ele descobre automaticamente arquivos `test_*.py`, executa cada funcao/metodo de teste e reporta o resultado. Testes sao organizados em classes para agrupar comportamentos relacionados.

**Comandos:**

```bash
# Rodar todos os testes
pytest tests/ -v -m "not distribuido"

# Rodar apenas um arquivo
pytest tests/test_core_automato.py -v

# Rodar apenas um teste especifico
pytest tests/test_core_automato.py::TestCalcularGeracao::test_ghost_rows_influenciam_borda_topo -v

# Rodar com relatorio de cobertura de codigo
pytest tests/ -v -m "not distribuido" --cov=. --cov-report=term-missing
```

> Testes marcados com `@pytest.mark.distribuido` requerem o nameserver Pyro5 rodando e sao excluidos por padrao com `-m "not distribuido"`.

### mutmut — teste de mutacao

O **mutmut** verifica se os testes sao realmente eficazes. Ele modifica o codigo fonte artificialmente (ex: troca `>=` por `>`, inverte condicoes) e roda os testes. Se os testes **falham** com a modificacao, o mutante foi **morto** — os testes detectaram o bug. Se os testes **passam mesmo com o bug**, o mutante **sobreviveu** — indicando ponto fraco na suite.

```bash
pip install mutmut

# Rodar mutacao no modulo core/
mutmut run

# Ver resumo dos resultados
mutmut results

# Ver o detalhe de um mutante especifico
mutmut show <ID>
```

**Resultado obtido:** 262 mortos / 16 sobreviveram (94% de deteccao) em 278 mutantes gerados.

---

### Estrutura dos testes

```
tests/
├── conftest.py              # fixtures compartilhadas (matrizes, mapas)
├── test_core_automato.py    # testes de core/automato.py
├── test_core_utils.py       # testes de core/utils.py
├── test_sequencial.py       # testes de main_sequencial.py
├── test_paralelo.py         # testes de paralelo/mestre.py
└── test_distribuido.py      # testes de distribuido/mestre.py e worker.py
```

### Como cada modulo foi testado

**`core/automato.py`** — funcoes puras testadas com matrizes pequenas construidas manualmente (1x1, 1x3, 3x3). Cada teste verifica uma unica regra de transicao: ESPALHADOR->INATIVO, IGNORANTE com vizinhos suficientes->ESPALHADOR, ghost rows afetando bordas, pureza da funcao (entrada nao mutada).

**`core/utils.py`** — verificacao de propriedades matematicas: dimensoes corretas, identidade fatiar->remontar, determinismo com mesma semente, comportamento do cronometro. Funcoes de impressao recebem smoke tests (so verifica que nao levantam excecao).

**`main_sequencial.py`** — testa o contrato da funcao: retorna tupla `(matriz, tempo)`, dimensoes corretas, tempo positivo, determinismo com mesma semente, parada antecipada sem espalhadores.

**`paralelo/mestre.py`** — `MestreParalelo` usa threads no mesmo processo e pode ser testado diretamente. Com 1 worker (sem ghost rows) o resultado e identico ao sequencial. Com 2+ workers verifica shape, estados validos e determinismo.

**`distribuido/mestre.py`** — testado sem Pyro5: metodos internos (`_calcular_ghosts`, `obter_matriz_final`, `registrar_worker`) sao chamados diretamente, manipulando o estado interno da classe para verificar o cruzamento de bordas e o reassembly da matriz.

**`distribuido/worker.py`** — testado com `unittest.mock.patch` para substituir `Pyro5.api.Proxy` por um `MagicMock`. O mock controla as respostas do "mestre remoto" sem nenhuma conexao de rede, verificando: URI correta, protocolo de registro, contagem de chamadas por geracao, parada antecipada com `terminar=True`, e deserializacao do mapa de influenciadores de lista->set.

---

## Melhorias em Relacao ao Modelo Base

### Influenciadores Digitais

O modelo base foi estendido com o agente **Influenciador Digital**, que simula perfis de alto impacto em redes sociais:

| Parametro                    | Valor                                                  |
| ---------------------------- | ------------------------------------------------------ |
| Distribuicao Inicial         | 1% da populacao total (mapeamento estatico)            |
| Vizinanca                    | Bloco 5x5 (ate 24 vizinhos), ao inves de Moore 3x3    |
| Probabilidade de Transmissao | Sorteada uniformemente entre 45% e 60% por tentativa  |

Quando um influenciador esta no estado ESPALHADOR, seu raio de influencia abrange um bloco 5x5. Um IGNORANTE dentro desse bloco pode ser convertido com probabilidade entre 45% e 60%, mesmo sem atingir o limiar normal de vizinhos.

A flag `--influenciadores` (CLI) ou `usar_influenciadores` (codigo) ativa/desativa esta mecanica.

### Efeito Midia

Apos uma determinada geracao (`--geracao-midia`, padrao 5), a **midia** comeca a atuar sobre a populacao a cada geracao, representando a cobertura jornalistica do fenomeno.

A cada geracao, **15% das celulas IGNORANTE** sao alcancadas pela midia. Destas:

| Efeito              | Chance (padrao) | Consequencia            |
| ------------------- | --------------- | ----------------------- |
| Dissemina fake news | 8%              | IGNORANTE -> ESPALHADOR |
| Combate fake news   | 92%             | IGNORANTE -> INATIVO    |

A probabilidade de a midia ser sensacionalista (disseminar fake news) e configuravel via `--prob-sensacionalista` (default `0.08`).

Flags: `--usar-midia` (default `True`), `--geracao-midia` (default `5`), `--prob-sensacionalista` (default `0.08`).

## Documentacao Adicional

- [Enunciado do Trabalho](enunciado.md)
- [Arquitetura do Sistema Distribuido](arquitetura.md)
- [Divisao de Tarefas (Roadmap)](tasks.md)
- [Relatorio Completo de Testes](RELATORIO_TESTES.md)
