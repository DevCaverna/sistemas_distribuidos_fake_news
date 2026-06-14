# Propagação de Fake News em Sistemas Paralelos e Distribuídos

Este projeto simula a propagação de fake news em uma população (matriz bidimensional) baseada em autômatos celulares e vizinhança de Moore. O objetivo principal é evoluir uma aplicação sequencial para versões **paralela (Threads)** e **distribuída (Sockets TCP)**, avaliando speedup, eficiência e escalabilidade.

## 📌 Estrutura do Projeto

O código está estruturado para maximizar o reaproveitamento lógico:

```text
.
├── core/
│   ├── automato.py        # Lógica pura de transição de estados (Vizinhança de Moore)
│   └── utils.py           # Geração da matriz, fatiamento, cronômetro e impressão
├── paralelo/              # Implementação paralela usando Threads (Master + Nodes)
├── distribuido/           # Implementação distribuída via Sockets TCP
├── main_sequencial.py     # Entry point para rodar a versão sequencial refatorada
└── FakeNews(Professor).py # Código sequencial original do professor (referência)
```

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

## 📚 Documentação Adicional

- [Enunciado do Trabalho](enunciado.md)
- [Arquitetura do Sistema Distribuído](arquitetura.md)
- [Divisão de Tarefas (Roadmap)](tasks.md)
