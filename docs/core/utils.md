# Módulo `core/utils.py`

Funções utilitárias para criação, manipulação e visualização de matrizes, além de cronômetro para medição de desempenho.

## Funções

### `criar_matriz(linhas, colunas, percentual_espalhadores, semente)`

Gera a matriz inicial da população. Todos os indivíduos começam como `IGNORANTE`; posições aleatórias são convertidas em `ESPALHADOR` conforme o percentual.

| Parâmetro                 | Default | Descrição                                             |
| ------------------------- | ------- | ----------------------------------------------------- |
| `linhas`                  | —       | Número de linhas                                      |
| `colunas`                 | —       | Número de colunas                                     |
| `percentual_espalhadores` | 0.02    | Fração de células que iniciam como espalhadoras       |
| `semente`                 | —       | Seed para `random.seed()` — garante reprodutibilidade |

**Retorno:** `list[list[int]]`.

### `fatiar_matriz(matriz, num_fatias)`

Divide a matriz horizontalmente em `num_fatias` submatrizes. Se a divisão não for exata, a última fatia absorve as linhas restantes.

**Retorno:** `list[list[list[int]]]`.

### `remontar_matriz(fatias)`

Recombina uma lista de fatias (na ordem) em uma única matriz global.

**Retorno:** `list[list[int]]`.

### `criar_mapa_influenciadores(linhas, colunas, percentual=0.01, semente_influenciadores=123)`

Cria um conjunto de coordenadas globais de influenciadores. Por padrão, marca 1% da população usando semente fixa para reprodutibilidade.

### `imprimir_grade(matriz)`

Imprime a matriz formatada no console com cores (ANSI) para cada estado.

### `imprimir_estatisticas(contagem, geracao=None, total_celulas=None)`

Exibe resumo textual de uma geração: quantidade de ignorantes, espalhadores e inativos.

### `Cronometro`

Classe simples para medição de tempo:

```python
crono = Cronometro()
crono.iniciar()
# ... trabalho ...
crono.parar()
print(crono.elapsed)  # segundos (float)
```
