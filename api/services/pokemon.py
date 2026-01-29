from typing import List, Optional
import json
from api.repositories.pokemon import PokemonRepository
from api.schemas import PokemonDetail, PokemonRank

class PokemonService:
    """
    Camada de Serviço (Use Cases) para lógica de negócios de Pokémons.
    Gerencia regras de negócio, caching e delega acesso a dados para o repositório.
    """

    def __init__(self, repository: PokemonRepository, redis_client=None):
        self.repository = repository
        self.redis = redis_client

    def get_pokemon_details(self, name: str) -> Optional[PokemonDetail]:
        """
        Obtém detalhes do Pokémon pelo nome.
        """
        return self.repository.get_pokemon_by_name(name)

    def list_pokemons(self, type_filter: Optional[str] = None) -> List[str]:
        """
        Lista nomes de Pokémons aplicando filtros opcionais.
        """
        return self.repository.list_pokemons_by_type(type_filter)

        return result

    def get_ranking(self, stat: str, limit: int = 10) -> List[PokemonRank]:
        """
        Obtém ranking de atributos com suporte a Caching (Redis).
        """
        cache_key = f"ranking:{stat}:{limit}"
        CACHE_TTL_SECONDS = 60
        
        # Tentar obter do Cache
        if self.redis:
            try:
                cached = self.redis.get(cache_key)
                if cached:
                    # Deserializar e retornar lista de modelos
                    data_json = json.loads(cached)
                    return [PokemonRank(**item) for item in data_json]
            except Exception:
                # Falha silenciosa no cache (fallback para DB)
                pass

        # Buscar no Banco de Dados
        result = self.repository.get_ranking_by_stat(stat, limit)

        # Salvar no Cache
        if self.redis and result:
            try:
                # Serializar lista de modelos para JSON
                json_data = json.dumps([r.dict() for r in result])
                self.redis.setex(cache_key, CACHE_TTL_SECONDS, json_data)
            except Exception:
                pass

        return result
