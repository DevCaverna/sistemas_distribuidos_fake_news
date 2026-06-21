# Modulo `core/automato.py`

Implementa o modelo computacional de propagação de fake news como um autômato celular sobre matriz bidimensional com vizinhança de Moore.

## Estados

Cada celula representa um indivíduo da população:

| Valor | Constante    | Significado                                    |
| ----- | ------------ | ---------------------------------------------- |
| 0     | `IGNORANTE`  | Ainda nao recebeu/acredita na informação       |
| 1     | `ESPALHADOR` | Acredita e compartilha a informação            |
| 2     | `INATIVO`    | Recebeu a informação, mas nao compartilha mais |

## Funcoes Principais

### `calcular_geracao(fatia, borda_topo=None, borda_base=None, limiar=2, mapa_influenciadores=None, offset_global=0)`

Funcao **pura** — nao altera a fatia original. Constroi uma matriz de trabalho com ghost rows (se fornecidas) e retorna a nova geração.

**Regras de transição:**

1. **IGNORANTE -> ESPALHADOR** se tiver pelo menos `limiar` vizinhos ESPALHADOR (vizinanca de Moore, ate 8).

2. **ESPALHADOR -> INATIVO** apos uma geração (todo espalhador se torna inativo na geração seguinte).

3. **INATIVO -> INATIVO** permanece inativo indefinidamente.

4. **Influenciadores:** se a celula esta dentro do raio 5x5 de um influenciador ESPALHADOR, pode ser convertida IGNORANTE->ESPALHADOR com probabilidade entre 45% e 60% (sorteada uniformemente), mesmo sem atingir o limiar normal.

**Parametros:**

| Parametro              | Tipo | Default | Descricao                                             |
| ---------------------- | ---- | ------- | ----------------------------------------------------- |
| `fatia`                | list | —       | Submatriz a processar                                 |
| `borda_topo`           | list | None    | Linha de borda superior (fatia anterior)              |
| `borda_base`           | list | None    | Linha de borda inferior (fatia posterior)             |
| `limiar`               | int  | 2       | Vizinhos necessarios para conversao                   |
| `mapa_influenciadores` | set  | None    | Conjunto de `(linha, col)` dos influenciadores        |
| `offset_global`        | int  | 0       | Offset global da fatia (para mapa de influenciadores) |

**Retorno:** `list[list[int]]` — nova submatriz calculada.

### `aplicar_midia(fatia, media_ativa, ...)`

Aplica o efeito da mídia sobre uma fatia da população. Atuando apenas em celulas IGNORANTE.

- **15%** das celulas IGNORANTE sao alcançadas pela mídia (`chance_alcance=0.15`).
- Das alcançadas:
  - `prob_sensacionalista` (default 8%): IGNORANTE -> ESPALHADOR (mídia dissemina fake news).
  - caso contrario: IGNORANTE -> INATIVO (mídia combate fake news).

| Parametro              | Tipo   | Default  | Descricao                                             |
| ---------------------- | ------ | -------- | ----------------------------------------------------- |
| `fatia`                | list   | —        | Submatriz a processar                                 |
| `media_ativa`          | bool   | —        | Se `True`, aplica o efeito; se `False`, retorna copia |
| `rng`                  | Random | `random` | Gerador de numeros aleatorios                         |
| `chance_alcance`       | float  | 0.15     | Probabilidade de uma celula IGNORANTE ser alcançada   |
| `prob_sensacionalista` | float  | 0.08     | Chance de a mídia disseminar em vez de combater       |

**Retorno:** `list[list[int]]` — nova fatia apos acao da mídia.

### `contar_estados(matriz)`

Conta quantas celulas de cada estado existem em uma (sub)matriz.

**Retorno:** `dict[int, int]` — `{IGNORANTE: N, ESPALHADOR: N, INATIVO: N}`.

### Influenciadores

O mapa de influenciadores e criado por `criar_mapa_influenciadores(linhas, colunas, percentual=0.01, semente_influenciadores=123)` em `core/utils.py`.

**Retorno:** `set[tuple[int, int]]`.

## Vizinhança de Moore

Cada celula possui ate 8 vizinhos (N, NE, E, SE, S, SO, O, NO). As bordas da matriz global nao possuem vizinhos fora dos limites — estes sao simplesmente ignorados na contagem.

Nas versões paralela e distribuida, as linhas de borda entre fatias sao compartilhadas via **ghost rows** para que cada worker tenha acesso aos vizinhos da fatia adjacente.
