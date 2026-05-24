# Plano de Arquitetura: Sistema Distribuído de Propagação de Fake News

## 1. Visão Geral da Arquitetura

A arquitetura adotada é o padrão **Mestre-Trabalhador (Master-Worker)** com topologia em estrela.
A comunicação será realizada de forma explícita via Sockets TCP nativos do Python. Esta escolha permite o controle granular sobre o envio e recebimento de pacotes, facilitando a medição do custo de comunicação (exigência do trabalho) e garantindo que não haja paralelização implícita.

- **Linguagem:** Python 3.x
- **Comunicação:** Biblioteca `socket` (TCP/IPv4)
- **Serialização de Dados:** Biblioteca `pickle` (ou `json`) acoplada com empacotamento de tamanho de cabeçalho (`struct.pack`).

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

1. Inicializar a matriz completa com o estado inicial (Ignorantes e Espalhadores).
2. Levantar um servidor Socket e aguardar a conexão de `W` Workers.
3. Fatiar a matriz e enviar para cada Worker sua respectiva parte.
4. **Sincronizador de Geração (Barreira):** A cada geração, receber as fronteiras atualizadas dos Workers e repassá-las cruzadas (a base do Worker 1 vai para o topo do Worker 2, etc.).
5. Recolher as submatrizes no final, remontar a matriz global e calcular o tempo total (para o Speedup).

### 3.2. Nó Trabalhador (WorkerNode)

Processo isolado (pode rodar em terminais ou máquinas diferentes) que processa as regras do autômato celular.

**Responsabilidades:**

1. Conectar-se ao Mestre via IP/Porta.
2. Receber sua submatriz e alocar espaço para as Ghost Rows.
3. Executar o loop de gerações.
4. Ao fim de cada geração local, enviar as fronteiras (sua primeira e última linha real) para o Mestre.
5. Atualizar as Ghost Rows com os dados recebidos do Mestre antes de calcular a próxima geração.
6. Retornar a submatriz final processada.

## 4. Protocolo de Comunicação (Mensageria)

Para evitar o problema de leitura fragmentada no TCP (TCP streaming), toda mensagem enviada pelo socket deve ter um prefixo de 4 bytes indicando o tamanho do payload.

**Estrutura do Pacote:**

```
[Tamanho: 4 bytes int][Payload Serializado com Pickle]
```

**Tipos de Mensagens (Payloads):**

- `INIT` (Mestre -> Worker): Contém a submatriz inicial, número da geração máxima, ID do Worker e vizinhos lógicos.
- `SYNC_SEND` (Worker -> Mestre): Envia as linhas de borda atualizadas da geração atual.
  - Conteúdo: `{ worker_id, geracao, linha_topo, linha_base }`
- `SYNC_RECEIVE` (Mestre -> Worker): Devolve as ghost rows preenchidas com os dados dos vizinhos.
  - Conteúdo: `{ geracao, fantasma_topo, fantasma_base }`
- `RESULT` (Worker -> Mestre): Submatriz final após o término de todas as gerações.

## 5. Fluxo de Execução Passo a Passo (Garantia de Consistência)

A consistência de estado é o ponto mais crítico. Para resolver isso, usamos a técnica de **Double Buffering** no Worker e uma **Barreira Global** no Mestre.

**Fluxo por Geração G:**

1. **Cálculo Local:** O Worker lê de `matriz_atual` e escreve as mudanças em `matriz_proxima`. Ele processa apenas suas linhas reais (índices 1 a K).
2. **Swap:** `matriz_atual = matriz_proxima`.
3. **Envio de Fronteiras:** O Worker extrai a linha 1 (topo) e a linha K (base) da `matriz_atual` e envia para o Mestre via pacote `SYNC_SEND`.
4. **Barreira no Mestre:** O Mestre bloqueia. Ele só continua quando recebe pacotes `SYNC_SEND` de todos os Workers para a geração G.
5. **Roteamento:** O Mestre cruza os dados e envia pacotes `SYNC_RECEIVE` para os Workers.
6. **Atualização de Fantasmas:** O Worker recebe os pacotes, atualiza os índices 0 e K+1 da `matriz_atual`.
7. **Avanço:** A geração G termina. Inicia-se G+1.

## 6. Coleta de Métricas (Requisitos de Avaliação)

Para garantir os gráficos e análises pedidos no trabalho, o código deverá instanciar contadores:

- **Tempo Total de Processamento:** `time.perf_counter()` no Mestre (antes de dividir a carga até receber todos os resultados).
- **Custo de Comunicação:** O Mestre deve possuir uma variável `bytes_trafegados` que incrementa baseado no tamanho (em bytes) de cada pacote recebido/enviado (`sys.getsizeof()` no payload).
- **Tempo de Sincronização:** Medir quanto tempo o sistema fica ocioso esperando o pacote mais lento na Barreira Global.

## 7. Estratégia para Melhorias (Diferencial / Inovação)

Para buscar a pontuação extra de inovações, a arquitetura permite as seguintes extensões fáceis de plugar:

- **Redução de Comunicação (Comunicação Peer-to-Peer):** Em vez do Mestre fazer o roteamento das bordas (Fase 5), o Mestre envia aos Workers os IPs uns dos outros. A cada geração, o Worker X abre um socket direto com o Worker X-1 e X+1 para trocar bordas. Isso diminui o gargalo no Mestre drasticamente.
- **Influenciadores Digitais:**
  - _Como:_ Algumas células podem ser inicializadas com o estado "Super Espalhador" (raio de vizinhança maior ou probabilidade de contágio de 100%). No envio da carga inicial (`INIT`), o Mestre sinaliza essas células.
