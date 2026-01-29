# DAGs do Airflow:

Este diretório contém os DAGs (Grafos Acíclicos Direcionados) para a Plataforma de Dados Pokémon.

## Visão Geral dos DAGs:

### 1. `model_etl_dag.py` (Padrão Ouro).
Esta é a implementação de referência para executar tarefas ETL.

- **Operador**: `DockerOperator`
- **Motivo**: Executa tarefas em contêineres isolados para evitar conflitos de dependência.

- **Configurações Principais**:

- `network_mode="pokemon-api-ai_default"`: Garante o acesso ao serviço `db`.

- `auto_remove=True`: Limpa o contêiner após a execução.

- `retries=2`: Lida com falhas transitórias.

### 2. `pokemon_etl_dag.py` (Legado/Simples)
Um DAG simples baseado em Bash.
- **Operador**: `BashOperator`
- **Caso de uso**: Scripts simples ou testes.

## Implantação:
Os DAGs são sincronizados automaticamente desta pasta para o contêiner do Airflow por meio de volumes do Docker.

1. Adicione seu arquivo DAG aqui.

2. Aguarde cerca de 30 segundos para que o Agendador o reconheça.

3. Verifique a interface do Airflow.

## Boas Práticas:
- **Idempotência**: Garanta que suas tarefas possam ser executadas novamente sem duplicação (tratado pela lógica do script ETL).

- **Segredos**: Não insira credenciais diretamente no código. Use Conexões do Airflow ou Variáveis ​​de Ambiente.

- **Isolamento**: Use `DockerOperator` para dependências complexas do Python.
