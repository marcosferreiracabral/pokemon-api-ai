from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.repositories.base import BaseRepository
from api.schemas import PokemonDetail, PokemonStats, PokemonRank

class PokemonRepository(BaseRepository):
    """
    Repositório concreto para acesso a dados de Pokémon.
    Utiliza SQLAlchemy para interagir com o banco de dados.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_by_id(self, id: int) -> Optional[Any]:
        # Implementação genérica se necessário, ou específica abaixo
        pass

    def get_all(self, limit: int = 10, offset: int = 0) -> List[Any]:
        pass

    def get_pokemon_by_name(self, name: str) -> Optional[PokemonDetail]:
        """
        Busca detalhes completos de um Pokémon pelo nome.
        """
        stmt = text("""
            SELECT 
                p.id, p.name, p.height, p.weight,
                f.hp, f.attack, f.defense, f.special_attack, f.special_defense, f.speed
            FROM dim_pokemon p
            JOIN fact_stats f ON p.id = f.pokemon_id
            WHERE p.name = :name
        """)
        result = self.db.execute(stmt, {"name": name.lower()}).fetchone()
        
        if not result:
            return None
        
        # Buscar tipos
        stmt_types = text("""
            SELECT t.name 
            FROM dim_type t
            JOIN pokemon_types pt ON t.id = pt.type_id
            WHERE pt.pokemon_id = :pid
            ORDER BY pt.slot
        """)
        types_res = self.db.execute(stmt_types, {"pid": result.id}).fetchall()
        types = [t[0] for t in types_res]
        
        return PokemonDetail(
            id=result.id,
            name=result.name,
            height=result.height,
            weight=result.weight,
            types=types,
            stats=PokemonStats(
                hp=result.hp,
                attack=result.attack,
                defense=result.defense,
                special_attack=result.special_attack,
                special_defense=result.special_defense,
                speed=result.speed
            )
        )

    def list_pokemons_by_type(self, type_name: Optional[str] = None) -> List[str]:
        """
        Lista nomes de Pokémons, opcionalmente filtrados por tipo.
        """
        if type_name:
            stmt = text("""
                SELECT p.name
                FROM dim_pokemon p
                JOIN pokemon_types pt ON p.id = pt.pokemon_id
                JOIN dim_type t ON pt.type_id = t.id
                WHERE t.name = :type_name
                ORDER BY p.name
            """)
            results = self.db.execute(stmt, {"type_name": type_name.lower()}).fetchall()
        else:
            stmt = text("SELECT name FROM dim_pokemon ORDER BY name")
            results = self.db.execute(stmt).fetchall()
        
        return [row.name for row in results]

    def get_ranking_by_stat(self, stat: str, limit: int = 10) -> List[PokemonRank]:
        """
        Obtém o ranking dos top N Pokémons para um determinado atributo.
        Nota: Validação de segurança do nome da coluna deve ser feita no Service ou aqui.
        """
        # Proteção básica contra SQL Injection via validação de schema (feito no service normalmente),
        # mas aqui garantimos que a query seja montada seguramente se o input for validado antes.
        query = f"""
            SELECT p.name, f.{stat} as value
            FROM dim_pokemon p
            JOIN fact_stats f ON p.id = f.pokemon_id
            ORDER BY f.{stat} DESC
            LIMIT :limit
        """
        stmt = text(query)
        results = self.db.execute(stmt, {"limit": limit}).fetchall()
        
        return [
            PokemonRank(rank=i+1, name=row.name, value=row.value)
            for i, row in enumerate(results)
        ]
