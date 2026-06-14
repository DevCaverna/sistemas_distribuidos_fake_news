# Plano de Arquitetura: Sistema Distribuído de Propagação de Fake News

## 1. Visão Geral da Arquitetura

A arquitetura adotada é o padrão **Mestre-Trabalhador (Master-Worker)** com topologia em estrela e barreira global gerenciada pelo Mestre.
A comunicação é realizada via **Pyro5**, um framework de RPC para Python que abstrai a camada de sockets e serialização. O Mestre expõe objetos remotos que os Workers invocam a cada geração para trocar bordas.

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

### 3.2. Nó Mestre (`MestreDistribuido`)

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

1. Conectar-se ao Name Server e obter um proxy para o objeto remoto do Mestre.
2. Chamar `registrar_worker()` para receber sua fatia, configuração e ghost rows iniciais.
3. Para cada geração:
   - Calcular a próxima geração localmente via `calcular_geracao(fatia, ghost_topo, ghost_base, limiar)`.
   - Extrair a primeira e última linha reais da fatia atualizada.
   - Enviar as bordas para o Mestre (`enviar_bordas`).
   - Aguardar as ghost rows calculadas pelo Mestre (`obter_ghosts`).
   - Atualizar `ghost_topo` e `ghost_base` para a próxima iteração.
   - Se `terminar` for `True`, interromper o loop.
4. Enviar a fatia final processada para o Mestre (`enviar_resultado`).

## 4. Protocolo de Comunicação (Pyro5 RPC)

Não há protocolo binário customizado. Toda comunicação ocorre por meio de chamadas de método remoto Pyro5, que serializa os argumentos e retornos automaticamente.

**Métodos Remotos Expostos pelo Mestre:**

| Método                                                                             | Direção         | Descrição                                          |
| ---------------------------------------------------------------------------------- | --------------- | -------------------------------------------------- |
| `registrar_worker()`                                                               | Worker → Mestre | Worker se registra e recebe sua fatia/configuração |
| `enviar_bordas(worker_id, geracao, borda_topo, borda_base, contagem_espalhadores)` | Worker → Mestre | Worker envia suas linhas de borda da geração atual |
| `obter_ghosts(worker_id, geracao)`                                                 | Worker → Mestre | Worker busca as ghost rows após a barreira         |
| `enviar_resultado(worker_id, fatia_final)`                                         | Worker → Mestre | Worker entrega sua fatia processada ao final       |

## 5. Fluxo de Execução Passo a Passo

### Inicialização

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

- **Redução de Comunicação (Peer-to-Peer):** Em vez de toda borda passar pelo Mestre, os Workers poderiam trocar ghost rows diretamente entre si, reduzindo o gargalo central.
- **Influenciadores Digitais:** Inicializar células como "Super Espalhador" (raio de vizinhança maior ou contágio de 100%).
