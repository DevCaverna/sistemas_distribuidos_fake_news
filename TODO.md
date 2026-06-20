[ ] Métrica de CPU ser dividido por todos os núcleos (107%)

- Atualmente, a porcentagem vem baseada em um único núcleo, caso hajam múltiplos, a porcentagem não está sendo dividida por todos.

[ ] Interface gráfica inicia os workers em background depois do mestre

- Ao iniciar a execução distribuída, os workers devem ser iniciados em background e o mestre deve esperar até que todos estejam prontos.

[ ] Gráficos na interface gráfica

- Existe uma uma aba na inteface gráfica "Métricas e telemetria".
- Existe uma geração de gráficos que gera gráficos de métricas e telemetria e grava ela na pasta métricas/.
- Na aba "Métricas e telemetria", devem ser exibidos esses gráficos, um abaixo do outro.

[ ] Métricas funcionando no paralelo

- Na aba "Console" da GUI, ao executar o códido em paralelo, nenhuma métrica é logada.
- Deve gerar gráficos e exibi-los assim como na execução distribuída.

[ ] Devem haver gráficos e métricas para todos os tipos de execução, sequencial, paralelo, distribuído.

[ ] Gráficos comparativos de todos os tipos de execuções

- Deve comparar consumo de CPU, rede (se aplicável) e tempo de execução entre os diferentes tipos de execução.

[ ] Atualizar o README.md, arquitetura.md e documentar TODOS os métodos com docstrings.
