from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import os

# Argumentos padrão para o DAG:
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'model_etl_dag',
    default_args=default_args,
    description='A model DAG demonstrating isolated execution using DockerOperator',
    schedule_interval=timedelta(days=1),
    start_date=days_ago(1),
    catchup=False,
    tags=['model', 'docker', 'etl'],
) as dag:

    # Exemplo: Executando o processo ETL dentro de um contêiner dedicado.
    # Isso evita conflitos de dependência com o ambiente do Airflow.
    run_etl_isolated = DockerOperator(
        task_id='run_etl_isolated',
        image='pokedex-etl:latest',  # A imagem foi criada pelo docker-compose.
        api_version='auto',
        auto_remove=True,
        command="python main.py",
        docker_url="unix://var/run/docker.sock",
        network_mode="pokemon-api-ai_default", # Conecte-se à mesma rede que o banco de dados.
        environment={
            "POSTGRES_HOST": "db",
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "postgres",
            "POSTGRES_DB": "pokedex"
        },
        # Montar volumes se necessário (por exemplo, para logs ou arquivos de saída).
        # mounts=[Mount(source='/host/path', target='/container/path', type='bind')].
    )

    run_etl_isolated
