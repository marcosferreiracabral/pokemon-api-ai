import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import logging
from airflow import DAG
from airflow.operators.python import PythonOperator

# Adicione a raiz do projeto ao PATH para permitir a importação dos módulos ETL e API
# Supondo que o DAG esteja em airflow/dags/etl_dag.py, a raiz do projeto é ../../
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

try:
    from etl import extract, transform, load
    from api.schemas import PokemonDetail
except ImportError as e:
    logging.error(f"Failed to import project modules: {e}")
    # Isso pode acontecer durante a análise sintática se as dependências não forem atendidas no ambiente do agendador do Airflow.
    # Por enquanto, permitimos que o DAG seja analisado mesmo se as importações falharem (as chamadas de função falharão em tempo de execução).
    pass

default_args = {
    'owner': 'antigravity',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def run_extract(**kwargs):
    """
    Extrai dados e serializa modelos Pydantic em dicionários para XCom.
    """
    limit = kwargs.get('limit', 50) # Mantenha pequeno para demonstração.
    logging.info(f"Extracting {limit} pokemon...")
    
    # Retorna List[PokemonDetail].
    data = extract.fetch_pokemon_data(limit=limit)
    
    # Serializar para formato compatível com JSON:
    serialized_data = [p.model_dump() for p in data]
    return serialized_data

def run_transform(**kwargs):
    """
   Desserializa dados, transforma e serializa DataFrames para XCom.
    """
    ti = kwargs['ti']
    raw_data_dicts = ti.xcom_pull(task_ids='extract_task')
    
    if not raw_data_dicts:
        raise ValueError("No data received from extract task")
        
    logging.info(f"Received {len(raw_data_dicts)} records. Transforming...")
    
    # Reidratar modelos Pydantic.
    # Observação: Usar mode='python' ou simplesmente construir ajuda na validação.
    pydantic_models = [PokemonDetail(**d) for d in raw_data_dicts]
    
    # Retorna uma tupla [DataFrame, DataFrame, DataFrame, DataFrame]
    df_pokemon, df_dim_type, df_types_link, df_stats = transform.transform_data(pydantic_models)
    
    # Serializar DataFrames em dicionários
    return {
        'df_pokemon': df_pokemon.to_dict('records'),
        'df_dim_type': df_dim_type.to_dict('records'),
        'df_types_link': df_types_link.to_dict('records'),
        'df_stats': df_stats.to_dict('records')
    }

def run_load(**kwargs):
    """
    Desserializa DataFrames e os carrega no banco de dados.
    """
    ti = kwargs['ti']
    data_dict = ti.xcom_pull(task_ids='transform_task')
    
    if not data_dict:
        raise ValueError("No data received from transform task")
        
    logging.info("Loading data to database...")
    
    # Reconstruir DataFrames:
    df_pokemon = pd.DataFrame(data_dict['df_pokemon'])
    df_dim_type = pd.DataFrame(data_dict['df_dim_type'])
    df_types_link = pd.DataFrame(data_dict['df_types_link'])
    df_stats = pd.DataFrame(data_dict['df_stats'])
    
    # Load
    load.load_data(df_pokemon, df_dim_type, df_types_link, df_stats)

with DAG(
    'pokemon_etl_pipeline',
    default_args=default_args,
    description='A simple ETL pipeline for Pokemon data',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:

    extract_task = PythonOperator(
        task_id='extract_task',
        python_callable=run_extract,
        op_kwargs={'limit': 20},
    )

    transform_task = PythonOperator(
        task_id='transform_task',
        python_callable=run_transform,
    )

    load_task = PythonOperator(
        task_id='load_task',
        python_callable=run_load,
    )

    extract_task >> transform_task >> load_task
