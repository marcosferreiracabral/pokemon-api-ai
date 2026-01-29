from pydantic import BaseModel, Field
from typing import List

class PokemonStats(BaseModel):
    hp: int = Field(..., gt=0, description="Os Pontos de Vida (PV) do Pokémon, que determinam quanto dano ele pode receber.")
    attack: int = Field(..., gt=0, description="O ataque base do Pokémon, que determina o dano causado por ataques físicos.")
    defense: int = Field(..., gt=0, description="A defesa base do Pokémon, que determina a resistência a ataques físicos.")
    special_attack: int = Field(..., gt=0, description="O ataque especial base do Pokémon, que determina o dano causado por ataques especiais.")
    special_defense: int = Field(..., gt=0, description="A defesa especial base do Pokémon, que determina a resistência a ataques especiais.")
    speed: int = Field(..., gt=0, description="A velocidade base do Pokémon, que determina a ordem de ataques em batalha.")

    class Config:
        from_attributes = True

class PokemonDetail(BaseModel):
    id: int = Field(..., description="O identificador único do Pokémon na Dex Nacional.")
    name: str = Field(..., description="O nome do Pokémon.")
    height: int = Field(..., gt=0, description="A altura do Pokémon em decímetros.")
    weight: int = Field(..., gt=0, description="O peso do Pokémon em hectogramas.")
    types: List[str] = Field(..., description="Uma lista de tipos elementais associados ao Pokémon (por exemplo, 'Fogo', 'Água').")
    stats: PokemonStats = Field(..., description="As estatísticas base de batalha do Pokémon.")

    class Config:
        from_attributes = True

class PokemonRank(BaseModel):
    rank: int = Field(..., gt=0, description="A posição de classificação do Pokemon para o específico stat.")
    name: str = Field(..., description="O nome do Pokemon.")
    value: int = Field(..., description="O valor do stat sendo classificado.")

    class Config:
        from_attributes = True
