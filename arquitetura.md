# Plano de Arquitetura: Sistema Distribuído de Propagação de Fake News

## 1. Visão Geral da Arquitetura

A arquitetura adotada é o padrão **Mestre-Trabalhador (Master-Worker)** com topologia em estrela.
A comunicação é realizada via **Pyro5 (Python Remote Objects)**, que abstrai a invocação de métodos remotos (RMI) sobre TCP. O Mestre é registrado como objeto remoto no Name Server do Pyro5, e os Workers obtêm um proxy para invocar seus métodos diretamente.

- **Linguagem:** Python 3.x
- **Comunicação:** Pyro5 (RMI sobre TCP/IPv4)
- **Serialização de Dados:** Serpent (padrão do Pyro5)

## 2. Estratégia de Particionamento (Decomposição 1D)

A matriz bidimensional (população) será fatiada horizontalmente.

- **Matriz Global:** `N` linhas x `M` colunas.
- **Número de Workers:** `W`.
- **Fatia por Worker:** Cada Worker recebe `N/W` linhas. Se a divisão não for exata, o último Worker absorve o resto.
- **Células Fantasmas (Ghost Rows):** Cada fatia local terá 2 linhas extras alocadas em memória:
  - `linha_fantasma_topo` (índice 0)
  - `linhas_reais` (índices 1 a K)
  - `linha_fantasma_base` (índice K+1)

## 3. Componentes do Sistema e Classes

### 3.1. Nó Mestre (MasterNode)

Responsável pela orquestração, distribuição de carga e sincronização.

**Responsabilidades:**

1. Inicializar a matriz completa com o estado inicial (Ignorantes, Espalhadores e mapa de Influenciadores).
2. Registrar-se como objeto remoto no Name Server do Pyro5 e aguardar a conexão de `W` Workers.
3. Fatiar a matriz e fornecer a cada Worker sua respectiva parte via `registrar_worker()`.
4. **Sincronizador de Geração (Barreira):** A cada geração, receber as fronteiras atualizadas dos Workers e repassá-las cruzadas (a base do Worker 1 vai para o topo do Worker 2, etc.).
5. Recolher as submatrizes no final, remontar a matriz global e calcular o tempo total (para o Speedup).

### 3.2. Nó Trabalhador (WorkerNode)

Processo isolado (pode rodar em terminais ou máquinas diferentes) que processa as regras do autômato celular.

**Responsabilidades:**

1. Obter um proxy do Mestre via Pyro5 Name Server.
2. Registrar-se e receber sua submatriz, ghost rows iniciais, mapa de influenciadores e offset global.
3. Executar o loop de gerações.
4. Ao fim de cada geração local, enviar as fronteiras (sua primeira e última linha real) para o Mestre.
5. Atualizar as Ghost Rows com os dados recebidos do Mestre antes de calcular a próxima geração.
6. Retornar a submatriz final processada.

## 4. Protocolo de Comunicação (RMI via Pyro5)

A comunicação é realizada via invocação de métodos remotos. O Mestre expõe os seguintes métodos:

- `registrar_worker()` → Retorna config inicial (fatia, ghost rows, limiar, mapa de influenciadores, offset global).
- `enviar_bordas(worker_id, geracao, borda_topo, borda_base, contagem_espalhadores)` → Worker envia fronteiras atualizadas.
- `obter_ghosts(worker_id, geracao)` → Worker recebe ghost rows cruzadas dos vizinhos.
- `enviar_resultado(worker_id, fatia_final)` → Worker envia submatriz final processada.

## 5. Fluxo de Execução Passo a Passo (Garantia de Consistência)

A consistência de estado é o ponto mais crítico. Para resolver isso, usamos a técnica de **Double Buffering** no Worker e uma **Barreira Global** no Mestre.

**Fluxo por Geração G:**

1. **Cálculo Local:** O Worker executa `calcular_geracao()` sobre sua fatia, recebendo as ghost rows atuais e o mapa de influenciadores.
2. **Envio de Fronteiras:** O Worker envia a primeira e última linha da fatia calculada via `enviar_bordas()`.
3. **Barreira no Mestre:** O Mestre bloqueia (via `threading.Condition`). Ele só libera quando recebe bordas de todos os Workers para a geração G.
4. **Roteamento:** O Mestre cruza os dados e disponibiliza via `obter_ghosts()`.
5. **Atualização de Fantasmas:** O Worker recebe as novas ghost rows.
6. **Avanço:** A geração G termina. Inicia-se G+1.

## 6. Coleta de Métricas (Requisitos de Avaliação)

Para garantir os gráficos e análises pedidos no trabalho, o código deverá instanciar contadores:

- **Tempo Total de Processamento:** `time.perf_counter()` no Mestre (antes de dividir a carga até receber todos os resultados).
- **Custo de Comunicação:** O Mestre deve possuir uma variável `bytes_trafegados` que incrementa baseado no tamanho (em bytes) de cada pacote recebido/enviado (`sys.getsizeof()` no payload).
- **Tempo de Sincronização:** Medir quanto tempo o sistema fica ocioso esperando o pacote mais lento na Barreira Global.

## 7. Estratégia para Melhorias (Diferencial / Inovação)

Para buscar a pontuação extra de inovações, a arquitetura permite as seguintes extensões fáceis de plugar:

- **Redução de Comunicação (Comunicação Peer-to-Peer):** Em vez do Mestre fazer o roteamento das bordas (Fase 5), o Mestre envia aos Workers os IPs uns dos outros. A cada geração, o Worker X abre um socket direto com o Worker X-1 e X+1 para trocar bordas. Isso diminui o gargalo no Mestre drasticamente.
- **Influenciadores Digitais:**
  - _Distribuição:_ 1% da população total é marcada estaticamente como influenciador no início da simulação (`criar_mapa_influenciadores` em `core/utils.py`).
  - _Vizinhança Estendida:_ Quando um influenciador está no estado ESPALHADOR, seu raio de influência abrange um bloco 5×5 (até 24 vizinhos), ao invés da vizinhança de Moore padrão (3×3, 8 vizinhos).
  - _Transmissão Probabilística:_ A cada tentativa de conversão de um IGNORANTE dentro do bloco 5×5, a probabilidade é sorteada uniformemente entre 45% e 60%.
  - _Transporte Distribuído:_ O mapa de influenciadores é serializado como lista de tuplas e enviado pelo Mestre a cada Worker na fase `INIT` (`registrar_worker`). O Worker reconstrói o `set` localmente e o repassa a `calcular_geracao` junto com o `offset_global` da sua fatia.
