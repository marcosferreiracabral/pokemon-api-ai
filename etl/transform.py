# Importar do módulo compartilhado:
from typing import List, Dict, Any, Tuple
import logging
import pandas as pd
import pandera as pa
from pandera.typing import DataFrame, Series
import sys
import os

# Garantir que possamos importar da API:
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.schemas import PokemonDetail

logger = logging.getLogger(__name__)

# --- Pandera Schemas ---
PokemonSchema = pa.DataFrameSchema({
    "id": pa.Column(int, checks=pa.Check.ge(1), unique=True, coerce=True),
    "name": pa.Column(str, checks=pa.Check.str_length(min_value=1), coerce=True),
    "height": pa.Column(int, checks=pa.Check.ge(0), coerce=True),
    "weight": pa.Column(int, checks=pa.Check.ge(0), coerce=True),
})

StatsSchema = pa.DataFrameSchema({
    "pokemon_id": pa.Column(int, checks=pa.Check.ge(1), coerce=True),
    "hp": pa.Column(int, checks=pa.Check.ge(0), coerce=True),
    "attack": pa.Column(int, checks=pa.Check.ge(0), coerce=True),
    "defense": pa.Column(int, checks=pa.Check.ge(0), coerce=True),
    "special_attack": pa.Column(int, checks=pa.Check.ge(0), coerce=True),
    "special_defense": pa.Column(int, checks=pa.Check.ge(0), coerce=True),
    "speed": pa.Column(int, checks=pa.Check.ge(0), coerce=True),
})

TypeLinkSchema = pa.DataFrameSchema({
    "pokemon_id": pa.Column(int, checks=pa.Check.ge(1), coerce=True),
    "type_name": pa.Column(str, checks=pa.Check.str_length(min_value=1), coerce=True),
    "slot": pa.Column(int, checks=pa.Check.isin([1, 2]), coerce=True),
})

def transform_data(raw_data: List[PokemonDetail]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Transforma dados brutos da PokeAPI (Pydantic Models) em DataFrames normalizados e validados.
    
    Raises:
        pa.errors.SchemaError: Se os dados não passarem na validação.
    """
    logger.info("Transformando dados...")
    
    pokemon_list = []
    stats_list = []
    types_list = []  # Para tabela de links: pokemon_id, type_name, slot.
    unique_types = set()

    for p in raw_data:
        # Acesse os atributos diretamente do modelo Pydantic:
        p_id = p.id
        name = p.name
        height = p.height
        weight = p.weight
        
        pokemon_list.append({
            'id': p_id,
            'name': name,
            'height': height,
            'weight': weight
        })
        
        # Estatísticas: Access from p.stats object
        stats_entry = {
            'pokemon_id': p_id,
            'hp': p.stats.hp,
            'attack': p.stats.attack,
            'defense': p.stats.defense,
            'special_attack': p.stats.special_attack,
            'special_defense': p.stats.special_defense,
            'speed': p.stats.speed,
        }
        stats_list.append(stats_entry)
        
        # Tipos: Acesso a partir da lista de strings de p.types
        # Ajustando a lógica: a lógica em extract.py simplesmente retorna uma lista de strings para tipos.
        # Mas espere, a lógica original tinha 'slot'.
        # Vamos verificar schemas.py: types: List[str]
        # Perdemos a informação de 'slot' no modelo Pydantic se armazenarmos apenas strings!
        # No entanto, por simplicidade/MVP, slot geralmente é apenas índice + 1.
        for i, t_name in enumerate(p.types):
            slot = i + 1
            unique_types.add(t_name)
            types_list.append({
                'pokemon_id': p_id,
                'type_name': t_name,
                'slot': slot
            })

    df_pokemon = pd.DataFrame(pokemon_list)
    df_stats = pd.DataFrame(stats_list)
    df_types_link = pd.DataFrame(types_list)
    df_dim_type = pd.DataFrame({'name': list(unique_types)}).sort_values('name')

    logger.info("Validando schemas com Pandera...")
    try:
        # Valide usando o Pandera:
        validated_pokemon = PokemonSchema.validate(df_pokemon)
        validated_stats = StatsSchema.validate(df_stats)
        validated_types = TypeLinkSchema.validate(df_types_link)
        logger.info("Dados validados com sucesso.")
    except pa.errors.SchemaError as e:
        logger.critical(f"Falha na validação do esquema: {e}")
        # Em um ETL real, podemos descartar linhas inválidas ou colocá-las em quarentena.
        # Aqui, relançamos o erro para interromper o pipeline conforme o SLA.
        raise e

    return df_pokemon, df_dim_type, df_types_link, df_stats
