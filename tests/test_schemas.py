import pytest
from pydantic import ValidationError
from api.schemas import PokemonStats, PokemonDetail, PokemonRank

def test_pokemon_stats_validation():
    # Estatísticas válidas:
    stats = PokemonStats(
        hp=100, attack=50, defense=50, 
        special_attack=50, special_defense=50, speed=50
    )
    assert stats.hp == 100

    # Estatísticas inválidas (valor negativo):
    with pytest.raises(ValidationError):
        PokemonStats(
            hp=-10, attack=50, defense=50, 
            special_attack=50, special_defense=50, speed=50
        )

def test_pokemon_rank_validation():
    # Classificação válida:
    rank = PokemonRank(rank=1, name="Pikachu", value=100)
    assert rank.name == "Pikachu"

    # Classificação inválida (0 ou negativo) - assumindo que rank 1 é o topo:
    with pytest.raises(ValidationError):
        PokemonRank(rank=0, name="Bulbasaur", value=50)

def test_pokemon_detail_structure():
    stats = PokemonStats(
        hp=35, attack=55, defense=40, 
        special_attack=50, special_defense=50, speed=90
    )
    detail = PokemonDetail(
        id=25,
        name="Pikachu",
        height=4,
        weight=60,
        types=["Electric"],
        stats=stats
    )
    assert detail.id == 25
    assert detail.stats.hp == 35
    assert detail.types == ["Electric"]

    # Teste de estrutura aninhada inválida:
    with pytest.raises(ValidationError):
        PokemonDetail(
            id=25, name="Pikachu", height=4, weight=60, 
            types=["Electric"], 
            stats={"hp": -5} # Um dicionário de estatísticas inválido deve gerar um erro a partir de um modelo aninhado.
        )
