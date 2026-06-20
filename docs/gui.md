# Interface Grafica (`app_gui.py` e `gui/`)

Interface grafica integrada construida com **CustomTkinter** e **matplotlib** (FigureCanvasTkAgg) para exibir graficos de telemetria inline.

## Estrutura do Modulo

```
gui/
  __init__.py          — modulo vazio
  console.py           — RedirectorConsole (redireciona stdout para o widget Textbox)
  telemetria.py        — exibicao de graficos, fullscreen, carregamento de metricas
  executores.py        — execucao das 3 modalidades em background
app_gui.py             — classe FakeNewsApp (sidebar, painel, botoes)
```

### `RedirectorConsole` (`gui/console.py`)

Redireciona `sys.stdout` para o widget `CTkTextbox` na aba "Console / Logs". Todo `print()` aparece tanto no terminal quanto na interface.

### `gui/telemetria.py`

Funcoes para exibicao de graficos:

| Funcao                                        | Descricao                                                              |
| --------------------------------------------- | ---------------------------------------------------------------------- |
| `exibir_imagem_grafico(app, caminho, idx)`    | Carrega PNG em FigureCanvasTkAgg, mantem aspect ratio ao redimensionar |
| `abrir_imagem_tela_cheia(caminho)`            | Abre imagem em janela fullscreen (clique para fechar)                  |
| `limpar_graficos(app)`                        | Remove todos os graficos do container                                  |
| `carregar_graficos_telemetria(app, caminhos)` | Exibe graficos de telemetria + adicionais                              |
| `tentar_exibir_comparativo(app)`              | Se todas as 3 modalidades ja executaram, gera grafico comparativo      |

### `gui/executores.py`

Funcoes que executam cada modalidade em background (chamadas por `threading.Thread`):

| Funcao                           | Descricao                                                        |
| -------------------------------- | ---------------------------------------------------------------- |
| `rodar_sequencial(app, params)`  | Executa `main_sequencial.executar_sequencial` e carrega metricas |
| `rodar_paralelo(app, params)`    | Instancia `MestreParalelo`, executa e carrega graficos           |
| `rodar_distribuido(app, params)` | Inicia NS + workers + mestre, executa e carrega graficos         |

### `FakeNewsApp` (`app_gui.py`)

Classe principal que herda de `ctk.CTk`:

- **Sidebar:** campos de configuracao (linhas, colunas, geracoes, workers, etc.) e indicadores de speedup.
- **3 botoes:** Executar Sequencial, Paralelo, Distribuido — cada um dispara uma thread background.
- **Abas:** "Console / Logs" (saida textual) e "Metricas e Telemetria" (graficos inline).
- **Progress bar:** indicador visual de execucao.
- **Speedup:** atualizado automaticamente na sidebar apos cada execucao.

### Funcionalidades

- **Redimensionamento:** graficos mantem aspect ratio ao redimensionar a janela via callback `<Configure>`.
- **Fullscreen:** clique em qualquer grafico para abrir em tela cheia; clique ou `<Escape>` fecha.
- **Workers locais:** no modo Distribuido, a GUI inicia workers como `subprocess.Popen` com `python3 -m distribuido.main_worker`.
- **Name Server:** iniciado automaticamente como subprocesso pela GUI.

## Execucao

```bash
python3 app_gui.py
```

Requer `python3-tk` (pacote de sistema):

```bash
sudo apt-get install python3-tk
```
