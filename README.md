# Propagação de Fake News em Sistemas Paralelos e Distribuídos

Este projeto simula a propagação de fake news em uma população (matriz bidimensional) baseada em autômatos celulares e vizinhança de Moore. O objetivo principal é evoluir uma aplicação sequencial para versões **paralela (Threads)** e **distribuída (Pyro5 RMI)**, avaliando speedup, eficiência e escalabilidade.

## 📌 Estrutura do Projeto

O código está estruturado para maximizar o reaproveitamento lógico:

```text
.
├── core/
│   ├── automato.py       # Lógica de transição de estados (Moore + Influenciadores 5x5)
│   └── utils.py          # Geração da matriz, influenciadores, fatiamento, cronômetro
├── paralelo/             # Implementação paralela usando Threads (Master + Nodes)
├── distribuido/          # Implementação distribuída via Pyro5 RMI
├── main_sequencial.py    # Entry point para rodar a versão sequencial refatorada
└── FakeNews(Professor).py           # Código sequencial original do professor (referência)
```

## ⚙️ Executando o Projeto

### Versão Sequencial

Para rodar a versão sequencial refatorada baseada na implementação base `core`:

```bash
python3 main_sequencial.py
```

## 🧠 Extensão: Influenciadores Digitais

O modelo base foi estendido com o agente **Influenciador Digital**, que simula perfis de alto impacto em redes sociais:

| Parâmetro | Valor |
|---|---|
| Distribuição Inicial | 1% da população total (mapeamento estático) |
| Vizinhança | Bloco 5×5 (até 24 vizinhos), ao invés de Moore 3×3 |
| Probabilidade de Transmissão | Sorteada uniformemente entre 45% e 60% por tentativa |

A flag `--influenciadores` (CLI) ou `usar_influenciadores` (código) ativa/desativa esta mecânica.

## 📚 Documentação Adicional

- [Enunciado do Trabalho](enunciado.md)
- [Arquitetura do Sistema Distribuído](arquitetura.md)
- [Divisão de Tarefas (Roadmap)](tasks.md)
