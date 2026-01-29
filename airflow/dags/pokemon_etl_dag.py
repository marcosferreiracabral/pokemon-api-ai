from airflow import DAG
from airflow.operators.bash import BashOperator # Tipo: ignore.
from datetime import datetime, timedelta
import os

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'pokemon_etl_dag',
    default_args=default_args,
    description='A simple DAG to run the Pokemon ETL pipeline',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['pokemon', 'etl'],
) as dag:

    run_etl = BashOperator(
        task_id='run_pokemon_etl',
        bash_command='python /opt/airflow/etl/main.py',
        env={
            **os.environ,
            'PYTHONPATH': '/opt/airflow',
            # Forneça os detalhes de conexão caso ainda não estejam presentes no ambiente
            # (eles serão inseridos pelo docker-compose).
        }
    )
