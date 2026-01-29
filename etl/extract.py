# Importar do módulo compartilhado:
import requests
import logging
from typing import List, Dict, Any, Optional
import sys
import os

# Garantir que possamos importar da API:
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.schemas import PokemonDetail, PokemonStats

logger = logging.getLogger(__name__)

POKEAPI_URL = "https://pokeapi.co/api/v2/pokemon"

def _map_stats(stats_data: List[Dict[str, Any]]) -> PokemonStats:
    """Função auxiliar para mapear estatísticas da PokeAPI para o modelo PokemonStats."""
    stats_dict = {}
    for stat in stats_data:
        name = stat['stat']['name'].replace('-', '_')
        value = stat['base_stat']
        stats_dict[name] = value
    
    # Lidar com diferenças específicas de nomenclatura, 
    # se houver (special-attack -> special_attack é tratado por substituição):
    return PokemonStats(**stats_dict)

def fetch_pokemon_data(limit: int = 100) -> List[PokemonDetail]:
    """
    Obtém dados de Pokémon da PokeAPI e retorna modelos Pydantic estruturados.
    Esta ferramenta é útil para recuperar detalhes sobre Pokémon,
    para preencher um banco de dados ou responder a perguntas.

    Args:
        limit: O número de Pokémon a serem buscados. O padrão é 100.
    
    Returns:
        Uma lista de objetos PokemonDetail contendo estatísticas e informações básicas.
    """
    results: List[PokemonDetail] = []
    url: str = f"{POKEAPI_URL}?limit={limit}"
    
    logger.info(f"Buscando {limit} pokémons da PokeAPI...")
    
    try:
        # Primeiro, obtenha a lista de Pokémon:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        pokemon_list = data.get("results", [])

        # Agora, busque os detalhes de cada Pokémon.
        # Usando uma sessão para o agrupamento de conexões.
        with requests.Session() as session:
            for item in pokemon_list:
                details_url = item["url"]
                try:
                    r = session.get(details_url, timeout=10)
                    r.raise_for_status()
                    raw_data = r.json()
                    
                    # Mapear dados brutos para o modelo Pydantic:
                    stats = _map_stats(raw_data.get('stats', []))
                    
                    # Tipos de extrato:
                    types = [t['type']['name'] for t in raw_data.get('types', [])]
                    
                    pokemon = PokemonDetail(
                        id=raw_data['id'],
                        name=raw_data['name'],
                        height=raw_data['height'],
                        weight=raw_data['weight'],
                        types=types,
                        stats=stats
                    )
                    
                    results.append(pokemon)
                    logger.info(f"Processado {item['name']}")
                except Exception as e:
                    logger.error(f"Falha ao buscar/processar {item['name']}: {e}")

    except Exception as e:
        logger.error(f"Erro fatal ao buscar lista: {e}")
        return []

    return results

if __name__ == "__main__":
    # Configuração básica para testes independentes:
    logging.basicConfig(level=logging.INFO)
    data = fetch_pokemon_data(limit=5)
    logger.info(f"Buscados com sucesso {len(data)} modelos de Pokémon.")
    if data:
        logger.info(f"Sample: {data[0]}")
