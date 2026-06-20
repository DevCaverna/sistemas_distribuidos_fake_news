# Plano de Arquitetura: Sistema Distribuído de Propagação de Fake News

## 1. Visão Geral da Arquitetura

A arquitetura adotada é o padrão **Mestre-Trabalhador (Master-Worker)** com topologia em estrela.
A comunicação é realizada via **Pyro5 (Python Remote Objects)**, que abstrai a invocação de métodos remotos (RMI) sobre TCP. O Mestre é registrado como objeto remoto no Name Server do Pyro5, e os Workers obtêm um proxy para invocar seus métodos diretamente.

- **Linguagem:** Python 3.x
- **Comunicação:** Pyro5 (RPC sobre TCP)
- **Descoberta de Serviço:** Pyro5 Name Server (registro de objetos remotos)
- **Serialização:** Pyro5 (interna, via serpent)

## 2. Estratégia de Particionamento (Decomposição 1D)

A matriz bidimensional (população) é fatiada horizontalmente.

- **Matriz Global:** `N` linhas x `M` colunas.
- **Número de Workers:** `W`.
- **Fatia por Worker:** Cada Worker recebe `N/W` linhas. Se a divisão não for exata, o último Worker absorve o resto.
- **Células Fantasmas (Ghost Rows):** Em vez de alocar localmente, as ghost rows são enviadas pelo Mestre a cada geração. O Worker as recebe como parâmetro na chamada `calcular_geracao(fatia, borda_topo, borda_base)`.

## 3. Componentes do Sistema

### 3.1. Serviço de Nomes (Pyro5 Name Server)

Processo independente que atua como serviço de descoberta. O Mestre registra seu objeto remoto com um nome simbólico (`mestre.fakenews`), e os Workers o localizam através desse nome, sem precisar conhecer IP/porta do Mestre antecipadamente.

Orquestrador central responsável por:

1. Inicializar a matriz completa com o estado inicial (Ignorantes e Espalhadores).
2. Fatiar a matriz horizontalmente em `W` partes.
3. Registrar-se no Name Server e expor um objeto remoto via Pyro5.
4. Aguardar que todos os `W` Workers se registrem (`registrar_worker`). Cada registro retorna a fatia inicial e as ghost rows iniciais.
5. **Sincronizador de Geração (Barreira):** A cada geração:
   - Receber as bordas superior e inferior de cada Worker (`enviar_bordas`).
   - Quando todos os `W` Workers tiverem enviado, cruzar os dados (a base do Worker X vira ghost_topo do Worker X+1, e o topo do Worker X vira ghost_base do Worker X-1).
   - Liberar os Workers para buscar as ghost rows calculadas (`obter_ghosts`).
   - Se não houver mais espalhadores, sinalizar `terminar = True` para todos.
6. Receber as submatrizes finais (`enviar_resultado`), remontar a matriz global e calcular o tempo total.

### 3.3. Nó Trabalhador (`executar_worker`)

Processo isolado (pode rodar em terminais ou máquinas diferentes) que processa as regras do autômato celular.

**Fluxo:**

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

1. Iniciar o **Pyro5 Name Server** (`python3 -m Pyro5.nameserver`).
2. Iniciar o **Mestre** — ele cria a matriz, fatia, e se registra no Name Server.
3. Iniciar os **Workers** (um ou mais processos/terminais) — cada um se conecta ao Name Server, obtém o proxy do Mestre e chama `registrar_worker()`.

### Por Geração

1. **Cálculo Local:** O Worker executa `calcular_geracao` com sua fatia e ghost rows recebidas.
2. **Envio de Fronteiras:** O Worker envia sua primeira e última linha real para o Mestre (`enviar_bordas`).
3. **Barreira no Mestre:** O Mestre bloqueia até receber bordas de todos os Workers para a geração G.
4. **Roteamento:** O Mestre cruza os dados: a base do Worker X vira ghost_topo do Worker X+1; o topo do Worker X vira ghost_base do Worker X-1. Se não houver mais espalhadores, marca `terminar = True`.
5. **Coleta de Ghosts:** O Worker chama `obter_ghosts` e recebe as ghost rows atualizadas (ou sinal de término).
6. **Avanço:** Geração G termina. Inicia-se G+1.

### Finalização

1. Workers enviam suas fatias finais via `enviar_resultado`.
2. Mestre remonta a matriz global, exibe estatísticas e tempo total.

## 6. Coleta de Métricas (Requisitos de Avaliação)

- **Tempo Total de Processamento:** `time.perf_counter()` no Mestre (antes de `aguardar_workers` até após `aguardar_resultado`).
- **Custo de Comunicação:** O Mestre incrementa `bytes_trafegados` com `sys.getsizeof()` dos dados de borda trafegados a cada chamada de `enviar_bordas` e `obter_ghosts`.

## 7. Estratégia para Melhorias (Diferencial / Inovação)

Para buscar a pontuação extra de inovações, a arquitetura permite as seguintes extensões fáceis de plugar:

- **Redução de Comunicação (Comunicação Peer-to-Peer):** Em vez do Mestre fazer o roteamento das bordas (Fase 5), o Mestre envia aos Workers os IPs uns dos outros. A cada geração, o Worker X abre um socket direto com o Worker X-1 e X+1 para trocar bordas. Isso diminui o gargalo no Mestre drasticamente.
- **Influenciadores Digitais:**
  - _Distribuição:_ 1% da população total é marcada estaticamente como influenciador no início da simulação (`criar_mapa_influenciadores` em `core/utils.py`).
  - _Vizinhança Estendida:_ Quando um influenciador está no estado ESPALHADOR, seu raio de influência abrange um bloco 5×5 (até 24 vizinhos), ao invés da vizinhança de Moore padrão (3×3, 8 vizinhos).
  - _Transmissão Probabilística:_ A cada tentativa de conversão de um IGNORANTE dentro do bloco 5×5, a probabilidade é sorteada uniformemente entre 45% e 60%.
  - _Transporte Distribuído:_ O mapa de influenciadores é serializado como lista de tuplas e enviado pelo Mestre a cada Worker na fase `INIT` (`registrar_worker`). O Worker reconstrói o `set` localmente e o repassa a `calcular_geracao` junto com o `offset_global` da sua fatia.
