# Divisão de Tarefas: Projeto Propagação de Fake News

Este documento organiza o escopo do projeto em Ramificações (Trilhas de Trabalho). Tarefas dentro de uma mesma ramificação são sequenciais (uma depende da anterior), mas ramificações diferentes podem ser executadas em paralelo por diferentes membros da equipe.

**Arquitetura do Repositório:** Todos os códigos ficarão no mesmo repositório. Haverá um pacote compartilhado (ex: `core/`) contendo a regra de negócio do autômato (Vizinhança de Moore) para ser reaproveitado. As execuções terão pontos de entrada (entry points) distintos para Paralelo e Distribuído, ambos baseados na lógica de Master + Nodes (o Master instancia o código do Node N vezes).

## 🌿 Ramificação A: Core e Base Compartilhada (Fundação)

Esta ramificação bloqueia as Ramificações B e C. Deve ser a primeira a ser feita.

- [x] **Task A.1: Configuração do Repositório e Estrutura**
  - **Ação:** Criar o repositório no GitHub. Definir a estrutura de pastas (ex: `/core`, `/paralelo`, `/distribuido`).
- [x] **Task A.2: Refatoração do Sequencial (Módulo Compartilhado)**
  - **Ação:** Extrair a lógica do código sequencial fornecido pelo professor para funções puras no módulo `/core/automato.py` (ex: `calcular_geracao(fatia_matriz, borda_topo, borda_base)`).
  - **Entregável:** Lógica de transição de estados isolada e testada, pronta para ser importada por qualquer versão.
- [x] **Task A.3: Padronização de Entradas e Saídas**
  - **Ação:** Criar funções auxiliares em `/core/utils.py` para gerar a matriz inicial aleatória (com semente/seed fixa para testes), medir tempo (`time.perf_counter`) e imprimir a matriz.

## 🌿 Ramificação B: Implementação Paralela (Master + Nodes Locais)

Pode iniciar assim que a Ramificação A estiver concluída.

- [ ] **Task B.1: Lógica de Divisão (Fatiamento)**
  - **Ação:** Criar a função no Master que calcula os índices de divisão da matriz bidimensional em N fatias.
- [ ] **Task B.2: Código do Node Paralelo**
  - **Ação:** Criar o código do trabalhador local. Ele deve importar a lógica do core, receber sua fatia de matriz, e calcular a próxima geração considerando sincronização de memória com o Master (usando buffers ou passagem de argumentos).
- [ ] **Task B.3: Entry Point - Master Paralelo**
  - **Ação:** Criar o `main_paralelo.py`. Este script irá instanciar o código do Node N vezes (utilizando `multiprocessing`, `subprocess` ou `threading`), repassar as fatias, aguardar o processamento de cada geração e remontar a matriz final.
- [ ] **Task B.4: Validação do Paralelo**
  - **Ação:** Rodar o `main_paralelo.py` e comparar a saída final com a saída do código sequencial original para garantir que não há condições de corrida (_race conditions_).

## 🌿 Ramificação C: Implementação Distribuída (Master + Nodes via Rede)

Pode iniciar assim que a Ramificação A estiver concluída. Pode compartilhar lógicas de fatiamento da Ramificação B.

- [ ] **Task C.1: Protocolo de Comunicação TCP**
  - **Ação:** Criar no `/core/rede.py` funções genéricas para envio/recebimento de matrizes via Sockets (usando `pickle` ou `json` com cabeçalho indicando o tamanho do pacote).
- [ ] **Task C.2: Entry Point - Node Distribuído (Worker)**
  - **Ação:** Criar o `main_node_dist.py`. Este script se conecta via Socket a um IP/Porta, recebe sua submatriz, processa a geração atual usando o `/core/automato.py`, envia as bordas atualizadas (_ghost cells_) e aguarda o próximo passo.
- [ ] **Task C.3: Entry Point - Master Distribuído**
  - **Ação:** Criar o `main_mestre_dist.py`. Ele atua como servidor, aguarda a conexão de N instâncias do `main_node_dist.py`, divide a matriz, envia a carga inicial e orquestra a troca de fronteiras a cada nova geração (barreira de rede).
- [ ] **Task C.4: Validação do Distribuído**
  - **Ação:** Rodar o Mestre e múltiplos Nodes em terminais diferentes (ou máquinas diferentes via IP). Verificar se a saída final bate com a versão sequencial.

## 🌿 Ramificação D: Automação, Métricas e Testes

Pode ser iniciada em paralelo, criando scripts vazios ou mockados, mas depende de B e C finalizadas para execução real.

- [ ] **Task D.1: Script de Automação de Execução**
  - **Ação:** Criar um script (`run_experiments.py` ou `.sh`) que executa o `main_paralelo` e o `main_mestre_dist` iterativamente variando: Tamanho da Matriz, Número de Gerações e Número de Nodes.
- [ ] **Task D.2: Coleta de Tempos e Exportação**
  - **Ação:** Fazer com que o Master (de ambas as versões) exporte o Tempo Total, Tempo de Processamento e Tempo de Sincronização/Comunicação para um arquivo `.csv`.
- [ ] **Task D.3: Cálculo e Geração de Gráficos**
  - **Ação:** Criar um Jupyter Notebook ou script Python usando Matplotlib/Pandas que lê o `.csv`, calcula o Speedup ($T_{seq}/T_{par}$) e a Eficiência, gerando os gráficos exigidos.

## 🌿 Ramificação E: Inovações e Extensões (Pontos Extras)

Pode iniciar em paralelo com D, após B e C estarem estáveis.

- [ ] **Task E.1: Escolha da Extensão**
  - **Ação:** Definir qual melhoria implementar (ex: "Múltiplas fake news simultâneas" ou "Balanceamento dinâmico de carga").
- [ ] **Task E.2: Implementação da Extensão**
  - **Ação:** Adicionar a nova funcionalidade ao repositório (preferencialmente ativável via parâmetro/flag no Master para não quebrar a versão base).
- [ ] **Task E.3: Medição do Impacto da Melhoria**
  - **Ação:** Gerar um gráfico demonstrando como a melhoria afetou a propagação (ex: gráfico mostrando como bots automatizados aceleraram a infecção da rede).

## 🌿 Ramificação F: Documentação e Apresentação

Acompanha todo o ciclo de vida do projeto.

- [ ] **Task F.1: Elaboração do Relatório/Slides - Parte Teórica**
  - **Ação:** Descrever a arquitetura Master+Nodes, a divisão da matriz e como a rede está trafegando as fronteiras. Referenciar a bibliografia utilizada.
- [ ] **Task F.2: Documentação do Repositório (README)**
  - **Ação:** Escrever o `README.md` com instruções claríssimas e comandos exatos para o professor executar as versões Paralela e Distribuída.
- [ ] **Task F.3: Inserção dos Resultados Práticos**
  - **Ação:** Colar os gráficos gerados na Ramificação D nos slides e documentar a análise de gargalos (ex: justificar por que o custo de comunicação afeta o speedup distribuído).
- [ ] **Task F.4: Ensaio e Finalização**
  - **Ação:** Equipe ensaia a apresentação, garantindo que o tempo fique entre 15 e 20 minutos e que a contribuição de cada membro esteja documentada nos slides.
