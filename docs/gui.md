# Interface Gráfica (`app_gui.py` e `gui/`)

Interface gráfica integrada construída com **CustomTkinter** e **matplotlib** (FigureCanvasTkAgg) para exibir gráficos de telemetria inline.

## Estrutura do Módulo

```
gui/
  __init__.py          — módulo vazio
  console.py           — RedirectorConsole (redireciona stdout para o widget Textbox)
  telemetria.py        — exibição de gráficos, fullscreen, carregamento de métricas
  executores.py        — execução das 3 modalidades em background
app_gui.py             — classe FakeNewsApp (sidebar, painel, botões)
```

### `RedirectorConsole` (`gui/console.py`)

Redireciona `sys.stdout` para o widget `CTkTextbox` na aba "Console / Logs". Todo `print()` aparece tanto no terminal quanto na interface.

### `gui/telemetria.py`

Funções para exibição de gráficos:

| Função                                        | Descrição                                                              |
| --------------------------------------------- | ---------------------------------------------------------------------- |
| `exibir_imagem_grafico(app, caminho, idx)`    | Carrega PNG em FigureCanvasTkAgg, mantém aspect ratio ao redimensionar |
| `abrir_imagem_tela_cheia(caminho)`            | Abre imagem em janela fullscreen (clique para fechar)                  |
| `limpar_graficos(app)`                        | Remove todos os gráficos do container                                  |
| `carregar_graficos_telemetria(app, caminhos)` | Exibe gráficos de telemetria + adicionais                              |
| `tentar_exibir_comparativo(app)`              | Se todas as 3 modalidades já executaram, gera gráfico comparativo      |

### `gui/executores.py`

Funções que executam cada modalidade em background (chamadas por `threading.Thread`):

| Função                           | Descrição                                                        |
| -------------------------------- | ---------------------------------------------------------------- |
| `rodar_sequencial(app, params)`  | Executa `main_sequencial.executar_sequencial` e carrega métricas |
| `rodar_paralelo(app, params)`    | Instância `MestreParalelo`, executa e carrega gráficos           |
| `rodar_distribuido(app, params)` | Inicia NS + workers + mestre, executa e carrega gráficos         |

### `FakeNewsApp` (`app_gui.py`)

Classe principal que herda de `ctk.CTk`:

- **Sidebar:** campos de configuração (linhas, colunas, gerações, workers, etc.) e indicadores de speedup.
- **3 botões:** Executar Sequencial, Paralelo, Distribuído — cada um dispara uma thread background.
- **Abas:** "Console / Logs" (saída textual) e "Métricas e Telemetria" (gráficos inline).
- **Progress bar:** indicador visual de execução.
- **Speedup:** atualizado automaticamente na sidebar após cada execução.

### Funcionalidades

- **Redimensionamento:** gráficos mantêm aspect ratio ao redimensionar a janela via callback `<Configure>`.
- **Fullscreen:** clique em qualquer gráfico para abrir em tela cheia; clique ou `<Escape>` fecha.
- **Workers locais:** no modo Distribuído, a GUI inicia workers como `subprocess.Popen` com `python3 -m distribuido.main_worker`.
- **Name Server:** iniciado automaticamente como subprocesso pela GUI.

## Execução

```bash
python3 app_gui.py
```

Requer `python3-tk` (pacote de sistema):

```bash
sudo apt-get install python3-tk
```
