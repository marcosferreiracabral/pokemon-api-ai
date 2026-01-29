from fastapi import FastAPI, HTTPException, Query, Depends, APIRouter, Request
from sqlalchemy.orm import Session
from typing import List
import uuid
# Removido importação direta de json e text do sqlalchemy pois agora é responsabilidade do repositório/serviço

from prometheus_fastapi_instrumentator import Instrumentator
from api.database import get_db, redis_client
from api.schemas import PokemonDetail, PokemonStats, PokemonRank

# Importações da Nova Arquitetura Clean
from api.repositories.pokemon import PokemonRepository
from api.services.pokemon import PokemonService

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from common.telemetry import configure_telemetry
from common.logger import configure_logging, get_logger, set_correlation_id

# Configurar logs estruturados logo no início:
configure_logging()
logger = get_logger("main")

app = FastAPI(title="API Pokedex")
router_v1 = APIRouter()

# --- Observabilidade ---
# Configurar OpenTelemetry:
configure_telemetry("pokemon-api")

FastAPIInstrumentor.instrument_app(app)

Instrumentator().instrument(app).expose(app)

# --- Middleware de Correlação ---
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    set_correlation_id(correlation_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = correlation_id
    return response

# --- Injeção de Dependência ---
def get_pokemon_service(db: Session = Depends(get_db)) -> PokemonService:
    """
    Factory para criar o serviço de Pokémon com suas dependências.
    """
    repository = PokemonRepository(db)
    return PokemonService(repository, redis_client)

# --- V1 Endpoints ---

@router_v1.get("/pokemons/{name}", response_model=PokemonDetail)
def get_pokemon_details(
    name: str, 
    service: PokemonService = Depends(get_pokemon_service)
) -> PokemonDetail:
    """
    Obtém detalhes específicos de um Pokémon pelo nome.
    """
    result = service.get_pokemon_details(name)
    
    if not result:
        raise HTTPException(status_code=404, detail="Pokémon não encontrado!")
    
    return result

@router_v1.get("/pokemons", response_model=List[str])
def list_pokemons(
    type: str = Query(None, description="Filtrar por tipo de Pokémon (ex: fire, water)"),
    service: PokemonService = Depends(get_pokemon_service)
) -> List[str]:
    """
    Listar nomes de Pokémons, opcionalmente filtrados por tipo.
    """
    return service.list_pokemons(type)

@router_v1.get("/stats/ranking", response_model=List[PokemonRank])
def get_strongest_pokemons(
    stat: str = Query(..., pattern="^(hp|attack|defense|special_attack|special_defense|speed)$"),
    limit: int = 10,
    service: PokemonService = Depends(get_pokemon_service)
) -> List[PokemonRank]:
    """
    Obtenha os 'N' melhores Pokémons para um atributo específico (Com Cache).
    """
    return service.get_ranking(stat, limit)

# --- Composição do aplicativo ---
app.include_router(router_v1, prefix="/v1")

# Suporte ao caminho raiz legado para verificação de integridade:
@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/")
def read_root():
    return {"message": "API Pokedex v1. Use /v1/...", "docs": "/docs"}
