# Trabalho Prático

## Propagação de Fake News em Sistemas Paralelos e Distribuídos

O trabalho consiste na transformação e evolução de uma aplicação sequencial para versões paralela e distribuída.

O problema aborda a simulação da propagação de fake news em uma população representada por uma matriz bidimensional, inspirada em modelos de autômatos celulares e dinâmica de propagação de informação.

Cada posição da matriz representa um indivíduo da população, que pode assumir diferentes estados:

- **Ignorante**: ainda não recebeu/acredita na informação;
- **Espalhador**: acredita e compartilha a informação;
- **Inativo**: recebeu a informação, mas não compartilha mais.

A propagação ocorre localmente utilizando a vizinhança de Moore (até 8 vizinhos), em gerações discretas. O código sequencial é fornecido em Python. O grupo deverá compreender o funcionamento do algoritmo, refatorar e adaptar a implementação para versões paralela e distribuída.

O grupo deverá:

- Desenvolver uma versão paralela utilizando Threads (Python ou Java);
- Desenvolver uma versão distribuída utilizando Sockets ou RMI;
- Comparar o desempenho entre as versões sequencial, paralela e distribuída, analisando speedup, eficiência, melhorias e limitações.

### Requisitos

Nas versões paralela e distribuída a serem avaliadas, o cálculo da próxima geração deve ser dividido explicitamente entre threads ou processos implementados pelo grupo.

_O uso de bibliotecas ou mecanismos de paralelização implícita/automática não será considerado como implementação válida para fins de avaliação. Exemplos: NumPy vetorizado, Pandas, Numba, Cython, GPU/CUDA e frameworks paralelos._

#### Implementação Paralela

A implementação paralela deve:

- utilizar Threads;
- dividir o processamento da matriz entre múltiplas threads;
- manter a consistência entre gerações;
- evitar condições de corrida (_race conditions_).

#### Implementação Distribuída

A implementação distribuída deve:

- utilizar Sockets ou RMI;
- dividir o processamento da matriz entre múltiplos processos/máquinas;
- sincronizar as fronteiras da matriz entre processos;
- garantir consistência das gerações.

#### Código Sequencial fornecido

- uma implementação sequencial funcional;
- documentação básica do código;
- descrição do modelo computacional.

O grupo poderá:

- reutilizar integralmente o código;
- refatorar o código;
- modificar estruturas e algoritmos;
- implementar melhorias adicionais.

### Melhorias e Extensões

É desejável que o grupo proponha melhorias e extensões no modelo original.
As melhorias poderão ser utilizadas como critério de diferenciação entre os trabalhos. O grupo deverá justificar tecnicamente as melhorias implementadas.

Exemplos:

- probabilidades diferentes de convencimento;
- influenciadores digitais;
- bots automatizados;
- múltiplas fake news simultâneas;
- resistência à propagação;
- uso de grafos/redes sociais;
- balanceamento dinâmico de carga;
- visualização gráfica;
- estatísticas adicionais;
- otimizações computacionais;
- redução de comunicação distribuída;
- análise probabilística.

O grupo deve buscar referências bibliográficas para fundamentar tanto o modelo, quanto as otimizações e as decisões de implementação.

Podem ser utilizadas:

- IEEE, ACM, Scopus;
- artigos científicos, livros;
- repositórios acadêmicos;
- documentação técnica.

### Medição de Desempenho

O grupo deverá executar experimentos variando:

- tamanho da matriz;
- número de gerações;
- percentual inicial de espalhadores;
- número de threads;
- número de hosts/processos distribuídos.

Os mesmos cenários devem ser executados para as versões sequencial, paralela e distribuída.
As implementações paralela e distribuída devem preservar o comportamento lógico da versão sequencial.

### Configuração Experimental

Descrever detalhadamente:

- processador, quantidade de núcleos, memória RAM, sistema operacional;
- linguagem utilizada, versão do interpretador/compilador;
- ambiente de execução.

### Análise

O grupo deverá apresentar:

- tabelas comparativas, gráficos de desempenho;
- speedup, eficiência;
- análise de gargalos, análise de sincronização, análise de custo de comunicação;
- limitações observadas.

### O que deve ser entregue

- Código-fonte compactado contendo todos os códigos e instruções de execução;
- Apresentação (PDF):
  - descrição do problema;
  - explicação do modelo computacional e funcionamento da solução sequencial;
  - explicação das versões paralela e distribuída (divisão da matriz/processamento);
  - tabelas e gráficos (speedup e eficiência);
  - dificuldades encontradas e melhorias implementadas;
  - referências bibliográficas;
  - contribuição individual dos integrantes.

### Apresentação

- **Tempo:** 15 a 20 minutos (os alunos não serão interrompidos durante a apresentação);
- Todos os integrantes devem participar;
- O grupo deverá demonstrar a execução das versões sequencial (apenas se houver alteração), paralela e distribuída;
- Melhorias/extensões e resultados das comparações;
- Após a apresentação, o professor poderá solicitar explicações individuais sobre partes específicas do código e decisões de implementação.

### Critérios de Avaliação

| Item                                                 | Pontuação |
| ---------------------------------------------------- | --------- |
| Código Paralelo/Distribuído funcionando corretamente | 1         |
| Participação de todos na apresentação                | 1         |
| Respostas e explicações técnicas apresentadas        | 0,5       |
| Qualidade e organização dos códigos comentados       | 1         |
| Resultados experimentais                             | 1         |
| Melhorias e Inovações\*                              | até 3     |
| Disponibilidade no GitHub                            | 0,5       |
| Qualidade dos slides e apresentação                  | 1         |
| Referências utilizadas                               | 1         |

_\*Cada melhoria/inovação poderá acrescentar até 0,5 ponto, limitado ao máximo de 3,0 pontos._

### Observações

- Trabalhos iguais terão nota zero;
- Não será aceito trabalho após o prazo;
- O grupo deve compreender o código desenvolvido;
- O aluno que não participar da apresentação no dia estipulado ficará com zero no trabalho;
- O uso de IA generativa é permitido como apoio, mas não substitui o entendimento do código, análise experimental, fundamentação teórica e implementação prática. Toda utilização de código externo, IA generativa, artigos, repositórios ou bibliotecas adicionais deve ser devidamente referenciada.
