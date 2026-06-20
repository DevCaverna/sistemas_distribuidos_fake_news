# Testes

Framework de testes automatizados usando **pytest** e **mutmut** (teste de mutacao).

## Execucao

```bash
# Todos os testes (exceto distribuidos, que precisam de NS)
pytest tests/ -v -m "not distribuido"

# Todos os testes (com nameserver Pyro5 rodando na porta 9090)
pytest tests/ -v

# Apenas um modulo
pytest tests/test_core_automato.py -v

# Um teste especifico
pytest tests/test_core_automato.py::TestCalcularGeracao::test_ghost_rows_influenciam_borda_topo -v

# Com cobertura
pytest tests/ -v -m "not distribuido" --cov=. --cov-report=term-missing
```

Testes marcados com `@pytest.mark.distribuido` requerem o nameserver Pyro5 rodando (`pyro5-ns -p 9090`).

## Estrutura

```
tests/
  conftest.py              — fixtures compartilhadas (matrizes, mapas)
  test_core_automato.py    — automato: calcular_geracao, aplicar_midia, contar_estados
  test_core_utils.py       — utils: criar_matriz, fatiar/remontar, cronometro
  test_sequencial.py       — main_sequencial: fluxo completo, determinismo, CLI
  test_paralelo.py         — paralelo/mestre: MestreParalelo com 1 e 2 workers
  test_distribuido.py      — distribuido: metodos internos + worker mockado
```

## Cobertura por Modulo

### `test_core_automato.py`

Testa funcoes **puras** de `core/automato.py` com matrizes pequenas construidas manualmente (1x1, 1x3, 3x3). Cada teste verifica uma unica regra de transicao:

- ESPALHADOR -> INATIVO
- IGNORANTE com vizinhos suficientes -> ESPALHADOR
- IGNORANTE sem vizinhos suficientes -> permanece IGNORANTE
- Ghost rows afetando bordas (topo e base)
- Pureza: funcao nao altera a matriz de entrada
- Efeito midia: `aplicar_midia` com/sem midia ativa
- Contagem de estados e influenciadores

### `test_core_utils.py`

- Dimensoes corretas da matriz criada
- Identidade: `fatiar_matriz` + `remontar_matriz` = matriz original
- Determinismo: mesma semente produz matriz identica
- `Cronometro`: medicao de tempo

### `test_sequencial.py`

Testa o **contrato** da funcao `executar_sequencial()`:

- Retorna tupla de 3 elementos `(matriz, tempo, metricas)`
- Dimensoes corretas da matriz final
- Tempo positivo
- Estados validos (apenas 0, 1, 2)
- Determinismo com mesma semente
- Com e sem influenciadores
- Uma geracao
- Parada antecipada quando nao ha espalhadores
- Dimensoes nao quadradas
- `limiar` alto reduz propagacao

### `test_paralelo.py`

Testa `MestreParalelo` diretamente (usa threads no mesmo processo):

- Com 1 worker: resultado identico ao sequencial (sem ghost rows)
- Com 2 workers: shape correto, estados validos
- Determinismo (pode ser flaky devido ao escalonamento de threads)
- Early stop sem espalhadores

### `test_distribuido.py`

Testa `MestreDistribuido` e `WorkerDistribuido` sem Pyro5:

- **Mestre:** metodos internos (`_calcular_ghosts`, `obter_matriz_final`, `registrar_worker`) chamados diretamente, manipulando estado interno.
- **Worker:** testado com `unittest.mock.patch` para substituir `Pyro5.api.Proxy` por `MagicMock`. Verifica:
  - URI correta do mestre.
  - Protocolo de registro (`registrar_worker`).
  - Contagem de chamadas por geracao.
  - Parada com `terminar=True`.
  - Deserializacao de mapa de influenciadores (lista -> set).

## Teste de Mutacao (mutmut)

O **mutmut** modifica o codigo fonte artificialmente (ex: troca `>=` por `>`, inverte `if`) e roda os testes. Se os testes falham, o mutante foi **morto** (teste eficaz). Se passam, o mutante **sobreviveu** (ponto fraco).

```bash
pip install mutmut
mutmut run       # gera mutantes e testa
mutmut results   # resumo
mutmut show <ID> # detalhe de um mutante
```

**Resultado:** 262 mortos / 16 sobreviveram (94% de deteccao) em 278 mutantes gerados no modulo `core/`.

## Configuracao

`pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = .
markers =
    distribuido: testes que requerem Pyro5 nameserver rodando
```

`setup.cfg` (mutmut):

```ini
[mutmut]
paths_to_cover = core/
backup = False
```
