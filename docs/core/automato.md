# Modulo `core/automato.py`

Implementa o modelo computacional de propagacao de fake news como um automato celular sobre matriz bidimensional com vizinhanca de Moore.

## Estados

Cada celula representa um individuo da populacao:

| Valor | Constante     | Significado                                    |
| ----- | ------------- | ---------------------------------------------- |
| 0     | `IGNORANTE`   | Ainda nao recebeu/acredita na informacao       |
| 1     | `ESPALHADOR`  | Acredita e compartilha a informacao            |
| 2     | `INATIVO`     | Recebeu a informacao, mas nao compartilha mais |

## Funcoes Principais

### `calcular_geracao(fatia, mapa_influenciadores, ghost_topo, ghost_base, ...)`

Funcao **pura** — nao altera a fatia original. Constroi uma matriz de trabalho com ghost rows (se fornecidas) e retorna a nova geracao.

**Regras de transicao:**

1. **IGNORANTE -> ESPALHADOR** se tiver pelo menos `limiar` vizinhos ESPALHADOR (vizinanca de Moore, ate 8).

2. **ESPALHADOR -> INATIVO** apos uma geracao (todo espalhador se torna inativo na geracao seguinte).

3. **INATIVO -> INATIVO** permanece inativo indefinidamente.

4. **Influenciadores:** se a celula esta dentro do raio 5x5 de um influenciador ESPALHADOR, pode ser convertida IGNORANTE->ESPALHADOR com probabilidade entre 45% e 60% (sorteada uniformemente), mesmo sem atingir o limiar normal.

**Parametros:**

| Parametro             | Tipo     | Default | Descricao                                       |
| --------------------- | -------- | ------- | ----------------------------------------------- |
| `fatia`               | list     | —       | Submatriz a processar                           |
| `mapa_influenciadores`| set      | —       | Conjunto de `(linha, col)` dos influenciadores  |
| `ghost_topo`          | list|None| None   | Linha de borda superior (fatia anterior)        |
| `ghost_base`          | list|None| None   | Linha de borda inferior (fatia posterior)       |
| `limiar`              | int      | 3       | Vizinhos necessarios para conversao             |
| `rng`                 | Random   | `random`| Gerador de numeros aleatorios                   |
| `linha_inicial`       | int      | 0       | Offset global da fatia (para mapa de influenciadores) |

**Retorno:** `list[list[int]]` — nova submatriz calculada.

### `aplicar_midia(fatia, media_ativa, ...)`

Aplica o efeito da midia sobre uma fatia da populacao. Atuando apenas em celulas IGNORANTE.

- **15%** das celulas IGNORANTE sao alcancadas pela midia (`chance_alcance=0.15`).
- Das alcancadas:
  - `prob_sensacionalista` (default 8%): IGNORANTE -> ESPALHADOR (midia dissemina fake news).
  - caso contrario: IGNORANTE -> INATIVO (midia combate fake news).

| Parametro              | Tipo   | Default | Descricao                                          |
| ---------------------- | ------ | ------- | -------------------------------------------------- |
| `fatia`                | list   | —       | Submatriz a processar                              |
| `media_ativa`          | bool   | —       | Se `True`, aplica o efeito; se `False`, retorna copia |
| `rng`                  | Random | `random`| Gerador de numeros aleatorios                      |
| `chance_alcance`       | float  | 0.15    | Probabilidade de uma celula IGNORANTE ser alcancada|
| `prob_sensacionalista` | float  | 0.08    | Chance de a midia disseminar em vez de combater    |

**Retorno:** `list[list[int]]` — nova fatia apos acao da midia.

### `contar_estados(matriz)`

Conta quantas celulas de cada estado existem em uma (sub)matriz.

**Retorno:** `dict[int, int]` — `{IGNORANTE: N, ESPALHADOR: N, INATIVO: N}`.

### `contar_totais(matriz, mapa_influenciadores)`

Igual a `contar_estados`, mas tambem separa a contagem de influenciadores.

**Retorno:** `dict[int, int]` — incluindo a chave `"influenciadores"`.

### `criar_mapa_influenciadores(linhas, colunas, semente)`

Distribui estaticamente 1% da populacao como influenciadores (mapeamento deterministico baseado em `semente`).

**Retorno:** `set[tuple[int, int]]`.

## Vizinhanca de Moore

Cada celula possui ate 8 vizinhos (N, NE, E, SE, S, SO, O, NO). As bordas da matriz global nao possuem vizinhos fora dos limites — estes sao simplesmente ignorados na contagem.

Nas versoes paralela e distribuida, as linhas de borda entre fatias sao compartilhadas via **ghost rows** para que cada worker tenha acesso aos vizinhos da fatia adjacente.
