# Modulo `core/utils.py`

Funcoes utilitarias para criacao, manipulacao e visualizacao de matrizes, alem de cronometro para medicao de desempenho.

## Funcoes

### `criar_matriz(linhas, colunas, percentual_espalhadores, semente)`

Gera a matriz inicial da populacao. Todos os individuos comecam como `IGNORANTE`; posicoes aleatorias sao convertidas em `ESPALHADOR` conforme o percentual.

| Parametro                 | Default | Descricao                                             |
| ------------------------- | ------- | ----------------------------------------------------- |
| `linhas`                  | —       | Numero de linhas                                      |
| `colunas`                 | —       | Numero de colunas                                     |
| `percentual_espalhadores` | 0.02    | Fracao de celulas que iniciam como espalhadoras       |
| `semente`                 | —       | Seed para `random.seed()` — garante reprodutibilidade |

**Retorno:** `list[list[int]]`.

### `fatiar_matriz(matriz, num_fatias)`

Divide a matriz horizontalmente em `num_fatias` submatrizes. Se a divisao nao for exata, a ultima fatia absorve as linhas restantes.

**Retorno:** `list[list[list[int]]]`.

### `remontar_matriz(fatias)`

Recombina uma lista de fatias (na ordem) em uma unica matriz global.

**Retorno:** `list[list[int]]`.

### `gerar_mapa_influenciadores(linhas, colunas, semente)`

**OBS:** Esta funcao foi movida para `core/automato.py::criar_mapa_influenciadores`. Mantida por compatibilidade.

### `imprimir_grade(matriz)`

Imprime a matriz formatada no console com cores (ANSI) para cada estado.

### `imprimir_estatisticas(geracao, contagem)`

Exibe resumo textual de uma geracao: quantidade de ignorantes, espalhadores e inativos.

### `Cronometro`

Classe simples para medicao de tempo:

```python
crono = Cronometro()
crono.iniciar()
# ... trabalho ...
crono.parar()
print(crono.elapsed)  # segundos (float)
```
