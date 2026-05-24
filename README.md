# Propagação de Fake News em Sistemas Paralelos e Distribuídos

Este projeto simula a propagação de fake news em uma população (matriz bidimensional) baseada em autômatos celulares e vizinhança de Moore. O objetivo principal é evoluir uma aplicação sequencial para versões **paralela (Threads)** e **distribuída (Sockets TCP)**, avaliando speedup, eficiência e escalabilidade.

## 📌 Estrutura do Projeto

O código está estruturado para maximizar o reaproveitamento lógico:

```text
.
├── core/
│   ├── automato.py       # Lógica pura de transição de estados (Vizinhança de Moore)
│   └── utils.py          # Geração da matriz, fatiamento, cronômetro e impressão
├── paralelo/             # Implementação paralela usando Threads (Master + Nodes)
├── distribuido/          # Implementação distribuída via Sockets TCP
├── main_sequencial.py    # Entry point para rodar a versão sequencial refatorada
└── FakeNews(Professor).py           # Código sequencial original do professor (referência)
```

## ⚙️ Executando o Projeto

### Versão Sequencial

Para rodar a versão sequencial refatorada baseada na implementação base `core`:

```bash
python3 main_sequencial.py
```

_(A seguir: implementação das versões paralela e distribuída)_

## 📚 Documentação Adicional

- [Enunciado do Trabalho](enunciado.md)
- [Arquitetura do Sistema Distribuído](arquitetura.md)
- [Divisão de Tarefas (Roadmap)](tasks.md)
