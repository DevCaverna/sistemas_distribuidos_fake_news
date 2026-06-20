# Propagação de Fake News em Sistemas Paralelos e Distribuídos

Este projeto simula a propagação de fake news em uma população (matriz bidimensional) baseada em autômatos celulares e vizinhança de Moore. O objetivo principal é evoluir uma aplicação sequencial para versões **paralela (Threads)** e **distribuída (Pyro5 RMI)**, avaliando speedup, eficiência e escalabilidade.

## 📌 Estrutura do Projeto

O código está estruturado para maximizar o reaproveitamento lógico:

```text
.
├── core/
│   ├── automato.py        # Lógica de transição de estados (Moore + Influenciadores 5x5)
│   └── utils.py           # Geração da matriz, influenciadores, fatiamento, cronômetro
├── paralelo/              # Implementação paralela usando Threads (Master + Nodes)
├── distribuido/           # Implementação distribuída via Pyro5 RMI
├── main_sequencial.py     # Entry point para rodar a versão sequencial refatorada
└── FakeNews(Professor).py # Código sequencial original do professor (referência)
```

## 🧠 Extensão: Influenciadores Digitais

O modelo base foi estendido com o agente **Influenciador Digital**, que simula perfis de alto impacto em redes sociais:

| Parâmetro | Valor |
|---|---|
| Distribuição Inicial | 1% da população total (mapeamento estático) |
| Vizinhança | Bloco 5×5 (até 24 vizinhos), ao invés de Moore 3×3 |
| Probabilidade de Transmissão | Sorteada uniformemente entre 45% e 60% por tentativa |

A flag `--influenciadores` (CLI) ou `usar_influenciadores` (código) ativa/desativa esta mecânica.

## ⚙️ Executando o Projeto

### Versão Sequencial

```bash
python3 main_sequencial.py
```

### Versão Distribuída (Pyro5)

A versão distribuída usa o **Pyro5** para comunicação remota entre processos. É necessário instalar a dependência primeiro:

```bash
pip install Pyro5
```

A execução é feita em **três etapas** (em terminais/máquinas separadas):

**1. Iniciar o Name Server** (responsável pelo serviço de descoberta):

```bash
python3 -m Pyro5.nameserver --port 9090
```

**2. Iniciar o Mestre** (orquestrador, cria a matriz e coordena os workers):

```bash
python3 -m distribuido.main_mestre --linhas 100 --colunas 100 --geracoes 50 --workers 2
```

**3. Iniciar os Workers** (um terminal por worker, podem estar em máquinas distintas):

```bash
python3 -m distribuido.main_worker --host localhost --porta-ns 9090
```

> 💡 Os workers podem rodar em máquinas diferentes — basta apontar `--host` para o IP da máquina onde o Name Server está rodando.

**Parâmetros do Mestre:**

| Parâmetro        | Default | Descrição                          |
| ---------------- | ------- | ---------------------------------- |
| `--linhas`       | 100     | Número de linhas da matriz         |
| `--colunas`      | 100     | Número de colunas da matriz        |
| `--geracoes`     | 50      | Número de gerações                 |
| `--espalhadores` | 0.05    | Percentual inicial de espalhadores |
| `--limiar`       | 3       | Limiar de contágio                 |
| `--semente`      | 42      | Semente aleatória                  |
| `--workers`      | 2       | Quantidade de workers              |
| `--host`         | 0.0.0.0 | IP do Mestre                       |
| `--porta-ns`     | 9090    | Porta do Name Server               |

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

Cada worker processa uma fatia horizontal da matriz e troca linhas de borda (ghost rows) via Mestre a cada geração.

### Versão Paralela (Threads)

A versão paralela usa `threading` do Python e implementa o mesmo protocolo lógico do Mestre-Trabalhador
por meio de chamadas locais e primitivas de sincronização (Condition/Lock). Não é necessária biblioteca
externa adicional.

Para executar a versão paralela (em um único processo, múltiplas threads):

```bash
python3 -m paralelo.main_paralelo --linhas 100 --colunas 100 --geracoes 50 --workers 4
```

Parâmetros são os mesmos da versão distribuída (`--linhas`, `--colunas`, `--geracoes`, `--workers`, etc.).

## 🧪 Testes

### Configuração do ambiente

Os testes usam um ambiente virtual Python (`venv`) para isolar as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest Pyro5==5.16
```

### pytest

O **pytest** é o framework de testes usado no projeto. Ele descobre automaticamente arquivos `test_*.py`, executa cada função/método de teste e reporta o resultado. Testes são organizados em classes para agrupar comportamentos relacionados.

**Comandos:**

```bash
# Rodar todos os testes
pytest tests/ -v -m "not distribuido"

# Rodar apenas um arquivo
pytest tests/test_core_automato.py -v

# Rodar apenas um teste específico
pytest tests/test_core_automato.py::TestCalcularGeracao::test_ghost_rows_influenciam_borda_topo -v

# Rodar com relatório de cobertura de código
pytest tests/ -v -m "not distribuido" --cov=. --cov-report=term-missing
```

> Testes marcados com `@pytest.mark.distribuido` requerem o nameserver Pyro5 rodando e são excluídos por padrão com `-m "not distribuido"`.

### mutmut — teste de mutação

O **mutmut** verifica se os testes são realmente eficazes. Ele modifica o código fonte artificialmente (ex: troca `>=` por `>`, inverte condições) e roda os testes. Se os testes **falham** com a modificação, o mutante foi **morto** — os testes detectaram o bug. Se os testes **passam mesmo com o bug**, o mutante **sobreviveu** — indicando ponto fraco na suíte.

```bash
pip install mutmut

# Rodar mutação no módulo core/
mutmut run

# Ver resumo dos resultados
mutmut results

# Ver o detalhe de um mutante específico
mutmut show <ID>
```

**Resultado obtido:** 214 mortos / 64 sobreviveram (77% de detecção) em 278 mutantes gerados.

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

### Como cada módulo foi testado

**`core/automato.py`** — funções puras testadas com matrizes pequenas construídas manualmente (1×1, 1×3, 3×3). Cada teste verifica uma única regra de transição: ESPALHADOR→INATIVO, IGNORANTE com vizinhos suficientes→ESPALHADOR, ghost rows afetando bordas, pureza da função (entrada não mutada).

**`core/utils.py`** — verificação de propriedades matemáticas: dimensões corretas, identidade fatiar→remontar, determinismo com mesma semente, comportamento do cronômetro. Funções de impressão recebem smoke tests (só verifica que não levantam exceção).

**`main_sequencial.py`** — testa o contrato da função: retorna tupla `(matriz, tempo)`, dimensões corretas, tempo positivo, determinismo com mesma semente, parada antecipada sem espalhadores.

**`paralelo/mestre.py`** — `MestreParalelo` usa threads no mesmo processo e pode ser testado diretamente. Com 1 worker (sem ghost rows) o resultado é idêntico ao sequencial. Com 2+ workers verifica shape, estados válidos e determinismo.

**`distribuido/mestre.py`** — testado sem Pyro5: métodos internos (`_calcular_ghosts`, `obter_matriz_final`, `registrar_worker`) são chamados diretamente, manipulando o estado interno da classe para verificar o cruzamento de bordas e o reassembly da matriz.

**`distribuido/worker.py`** — testado com `unittest.mock.patch` para substituir `Pyro5.api.Proxy` por um `MagicMock`. O mock controla as respostas do "mestre remoto" sem nenhuma conexão de rede, verificando: URI correta, protocolo de registro, contagem de chamadas por geração, parada antecipada com `terminar=True`, e deserialização do mapa de influenciadores de lista→set.

---

## 📚 Documentação Adicional

- [Enunciado do Trabalho](enunciado.md)
- [Arquitetura do Sistema Distribuído](arquitetura.md)
- [Divisão de Tarefas (Roadmap)](tasks.md)
- [Relatório Completo de Testes](RELATORIO_TESTES.md)
