# Propagação de Fake News em Sistemas Paralelos e Distribuídos

Este projeto simula a propagação de fake news em uma população representada por matriz bidimensional, inspirada em modelos de autômatos celulares e vizinhança de Moore. Evolui uma implementação sequencial para versões **paralela (Threads)** e **distribuída (Pyro5 RMI)**, com métricas de telemetria, interface gráfica e testes automatizados.

## Estrutura

```
core/                  # Núcleo reutilizável (autômato, métricas, utils, comparativo)
paralelo/              # Versão paralela com threads (Mestre-Trabalhador)
distribuido/           # Versão distribuída via Pyro5 RMI
gui/                   # Interface gráfica (CustomTkinter + matplotlib)
app_gui.py             # Entry point da interface gráfica
main_sequencial.py     # Entry point sequencial
FakeNews(Professor).py # Código original fornecido
```

## Inovações

### 1. Interface Gráfica

GUI integrada com CustomTkinter que unifica as três modalidades em uma única janela: botões de execução, console embutido, gráficos de telemetria inline com redimensionamento e clique para tela cheia, indicadores de speedup na barra lateral. No modo Distribuído, a GUI inicia automaticamente workers locais e o Name Server como subprocessos.

[Documentação detalhada](docs/gui.md)

### 2. Influenciador Digital

Agente com raio de influência 5x5 (até 24 vizinhos) e probabilidade de transmissão entre 45% e 60% por tentativa. Simula perfis de alto impacto em redes sociais. Ativado via `--influenciadores`.

[Documentação detalhada](docs/core/automato.md)

### 3. Efeito Mídia

A partir de uma geração configurável, a mídia começa a atuar: 15% dos IGNORANTES são alcançados, podendo se tornar ESPALHADOR (mídia sensacionalista, `--prob-sensacionalista`) ou INATIVO (mídia de combate a fake news). Configurável via `--usar-midia`, `--geracao-midia` e `--prob-sensacionalista`.

[Documentação detalhada](docs/core/automato.md)

### 4. Métricas e Telemetria

Coleta de CPU (normalizada por núcleo), tempo de processamento, latência de rede e bytes trafegados por worker/geração. Exportação para CSV e geração de gráficos (gargalos, profiling, evolução temporal). Ao executar as três modalidades, um gráfico comparativo é gerado automaticamente.

[Documentação detalhada](docs/core/metricas.md) | [Comparativo](docs/core/comparativo.md)

### 5. Testes Automatizados

Suíte com **150 testes** (pytest) cobrindo desde funções puras do autômato até integração com processos reais (Pyro5). Teste de mutação com **mutmut** atingindo 94% de detecção (262 mortos / 16 sobreviventes) no módulo `core/`.

[Documentação detalhada](docs/testes.md)

---

## Execução

### Sequencial

```bash
python3 main_sequencial.py --linhas 100 --colunas 100 --geracoes 50 --espalhadores 0.05 --limiar 3 --semente 42 --influenciadores True --usar-midia True --geracao-midia 5 --prob-sensacionalista 0.08
```

### Paralela (Threads)

```bash
python3 -m paralelo.main_paralelo --linhas 100 --colunas 100 --geracoes 50 --workers 4 --espalhadores 0.05 --limiar 3 --semente 42
```

### Distribuída (Pyro5)

**Workers primeiro, mestre descobre automaticamente**:

```bash
# 1. Name Server
python3 -m Pyro5.nameserver --port 9090

# 2. Workers (um terminal cada) — retry até o mestre ficar disponível
python3 -m distribuido.main_worker --host localhost --porta-ns 9090

# 3. Mestre (descobre workers registrados automaticamente)
python3 -m distribuido.main_mestre --linhas 100 --colunas 100 --geracoes 50 --timeout-descoberta 3 --host 0.0.0.0 --porta-ns 9090 --influenciadores True --usar-midia True --geracao-midia 5 --prob-sensacionalista 0.08
```

### Interface Gráfica

```bash
python3 app_gui.py
```

### Testes

```bash
pytest tests/ -v -m "not distribuido"            # sem nameserver
pytest tests/ -v                                  # com nameserver na porta 9090
pytest tests/test_core_automato.py -v             # modulo especifico
pytest tests/ --cov=. --cov-report=term-missing   # com cobertura
```

---

## Documentação por Módulo

| Módulo                | Documentação                                         |
| --------------------- | ---------------------------------------------------- |
| `core/automato.py`    | [docs/core/automato.md](docs/core/automato.md)       |
| `core/utils.py`       | [docs/core/utils.md](docs/core/utils.md)             |
| `core/metricas.py`    | [docs/core/metricas.md](docs/core/metricas.md)       |
| `core/comparativo.py` | [docs/core/comparativo.md](docs/core/comparativo.md) |
| `main_sequencial.py`  | [docs/sequencial.md](docs/sequencial.md)             |
| `paralelo/`           | [docs/paralelo.md](docs/paralelo.md)                 |
| `distribuido/`        | [docs/distribuido.md](docs/distribuido.md)           |
| `app_gui.py` + `gui/` | [docs/gui.md](docs/gui.md)                           |
| Testes                | [docs/testes.md](docs/testes.md)                     |

## Referências

- [Enunciado do Trabalho](enunciado.md)
- [Arquitetura do Sistema Distribuído](arquitetura.md)
