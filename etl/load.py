# Importar do módulo compartilhado:
import os
import pandas as pd
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from typing import Tuple

logger = logging.getLogger(__name__)

def get_db_engine() -> Engine:
    """Cria um mecanismo SQLAlchemy específico."""
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "pokedex")
    
    url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url)

def load_data(
    df_pokemon: pd.DataFrame,
    df_dim_type: pd.DataFrame,
    df_types_link: pd.DataFrame,
    df_stats: pd.DataFrame
):
    """
    Carrega DataFrames no banco de dados.
    """
    engine = get_db_engine()
    logger.info("Carregando dados em PostgreSQL...")

    with engine.begin() as conn:
        # 1. Dimensões de carga: Pokemon:
        logger.info("Atualizando o dim_pokemon...")
        for _, row in df_pokemon.iterrows():
            stmt = text("""
                INSERT INTO dim_pokemon (id, name, height, weight)
                VALUES (:id, :name, :height, :weight)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    height = EXCLUDED.height,
                    weight = EXCLUDED.weight;
            """)
            conn.execute(stmt, row.to_dict())

        # 2. Dimensões de carga: Tipos:
        logger.info("Atualizando o dim_type...")
        # Como geramos IDs na Transformação, talvez precisemos ter cuidado se dependermos do número de série do banco de dados.
        # Mas dim_type não tem um ID fixo da PokeAPI (tem uma URL com detalhes, mas usamos apenas o nome).
        # Devemos iterar e verificar a unicidade pelo nome.

        # Mapeamento auxiliar para nome do tipo -> id:
        type_name_to_id = {}
        
        for _, row in df_dim_type.iterrows():
            # Verifique se existe para obter o ID ou insira:
            stmt_select = text("SELECT id FROM dim_type WHERE name = :name")
            result = conn.execute(stmt_select, {"name": row['name']}).fetchone()
            
            if result:
                type_id = result[0]
            else:
                stmt_insert = text("INSERT INTO dim_type (name) VALUES (:name) RETURNING id")
                type_id = conn.execute(stmt_insert, {"name": row['name']}).fetchone()[0]
            
            type_name_to_id[row['name']] = type_id

        # 3. Carregar tabela de links: Tipos de Pokémon:
        logger.info("Atualizando o pokemon_types...")
        # Limpar os dados existentes desses Pokémon para evitar duplicação ou dados obsoletos?
        # Ou apenas inserir em caso de conflito? A chave primária é (pokemon_id, type_id).
        
        for _, row in df_types_link.iterrows():
            type_id = type_name_to_id.get(row['type_name'])
            if type_id:
                data = {
                    "pokemon_id": row['pokemon_id'],
                    "type_id": type_id,
                    "slot": row['slot']
                }
                stmt = text("""
                    INSERT INTO pokemon_types (pokemon_id, type_id, slot)
                    VALUES (:pokemon_id, :type_id, :slot)
                    ON CONFLICT (pokemon_id, type_id) DO UPDATE SET
                        slot = EXCLUDED.slot;
                """)
                conn.execute(stmt, data)

        # 4. Informações sobre a carga: Estatísticas:
        logger.info("Atualizando tabela fact_stats...")
        for _, row in df_stats.iterrows():
            stmt = text("""
                INSERT INTO fact_stats (pokemon_id, hp, attack, defense, special_attack, special_defense, speed)
                VALUES (:pokemon_id, :hp, :attack, :defense, :special_attack, :special_defense, :speed)
                ON CONFLICT (pokemon_id) DO UPDATE SET
                    hp = EXCLUDED.hp,
                    attack = EXCLUDED.attack,
                    defense = EXCLUDED.defense,
                    special_attack = EXCLUDED.special_attack,
                    special_defense = EXCLUDED.special_defense,
                    speed = EXCLUDED.speed;
            """)
            conn.execute(stmt, row.to_dict())
            
    logger.info("Carregamento do ETL concluído com sucesso.")
