# Importar do módulo compartilhado:
import requests
import json
import time
from typing import Optional, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from common.config import API_BASE_URL, ENABLE_JSON_LOGS, APP_ENV
from common.logger import get_logger

REQUEST_TIMEOUT = 60  # Segundos.

logger = get_logger("pokemon_tools")

# --- Configuração de sessão de rede ---
def create_retry_session(
    retries=3,
    backoff_factor=1,
    status_forcelist=(500, 502, 503, 504),
) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

http_session = create_retry_session()

# --- Função Helper ---
def _safe_request(method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    url = f"{API_BASE_URL}{endpoint}"
    logger.info(f"Solicitando: {method} {url} Params={params}")
    
    try:
        start_time = time.time()
        response = http_session.request(method, url, params=params, timeout=REQUEST_TIMEOUT)
        duration = time.time() - start_time
        
        logger.info(f"Resposta: {response.status_code} Duração={duration:.2f}s")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            logger.warning(f"Recurso não encontrado: {url}")
            return {"error": "Recurso não encontrado."}
        else:
            logger.error(f"Erro da API {response.status_code}: {response.text}")
            return {"error": f"Erro da API: {response.status_code}"}
            
    except requests.exceptions.Timeout:
        logger.error(f"Tempo limite ao conectar a {url}")
        return {"error": "Tempo limite de conexão excedido."}
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de rede: {str(e)}")
        return {"error": f"Falha na conexão: {str(e)}"}
    except Exception as e:
        logger.exception("Erro inesperado")
        return {"error": "Erro interno inesperado."}

# --- Implementações de ferramentas ---
def buscar_pokemon(nome_ou_id: str) -> str:
    """
    Busca detalhes de um Pokémon pelo nome ou ID.
    Retorna stats, tipos, altura, peso, etc.
    """
    result = _safe_request("GET", f"/v1/pokemons/{nome_ou_id}")
    return json.dumps(result)

def listar_por_tipo(tipo: str) -> str:
    """
    Lista todos os pokémons de um determinado tipo (ex: fire, water).
    """
    result = _safe_request("GET", "/v1/pokemons", params={"type": tipo})
    return json.dumps(result)

def top_n_por_stat(stat: str, n: int = 5) -> str:
    """
    Retorna os N pokémons com maior valor no stat especificado.
    Stat deve ser um de: hp, attack, defense, special_attack, special_defense, speed.
    """
    result = _safe_request("GET", "/v1/stats/ranking", params={"stat": stat, "limit": n})
    return json.dumps(result)

def comparar_pokemons(pokemon_a: str, pokemon_b: str) -> str:
    """
    Busca detalhes de dois pokémons para comparação.
    Retorna um objeto com os dados de ambos.
    """
    data_a = _safe_request("GET", f"/v1/pokemons/{pokemon_a}")
    data_b = _safe_request("GET", f"/v1/pokemons/{pokemon_b}")
    
    combined = {
        "pokemon_a": data_a,
        "pokemon_b": data_b
    }
    return json.dumps(combined)


# --- Definição de ferramentas para OpenAI ---
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "buscar_pokemon",
            "description": "Busca detalhes completos de um Pokémon pelo nome (ex: 'pikachu') ou ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_ou_id": {
                        "type": "string",
                        "description": "Nome ou ID do Pokémon."
                    }
                },
                "required": ["nome_ou_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "listar_por_tipo",
            "description": "Lista nomes de Pokémons de um tipo específico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "description": "O tipo do Pokémon (ex: fire, water, grass)."
                    }
                },
                "required": ["tipo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "top_n_por_stat",
            "description": "Retorna o ranking dos N pokémons mais fortes em um atributo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stat": {
                        "type": "string",
                        "enum": ["hp", "attack", "defense", "special_attack", "special_defense", "speed"],
                        "description": "O atributo para classificar."
                    },
                    "n": {
                        "type": "integer",
                        "description": "Quantidade de pokémons no ranking (padrão 5).",
                        "default": 5
                    }
                },
                "required": ["stat"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "comparar_pokemons",
            "description": "Busca dados de dois pokémons simultaneamente para comparação.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pokemon_a": {"type": "string", "description": "Nome do primeiro Pokémon."},
                    "pokemon_b": {"type": "string", "description": "Nome do segundo Pokémon."}
                },
                "required": ["pokemon_a", "pokemon_b"]
            }
        }
    }
]

available_functions = {
    "buscar_pokemon": buscar_pokemon,
    "listar_por_tipo": listar_por_tipo,
    "top_n_por_stat": top_n_por_stat,
    "comparar_pokemons": comparar_pokemons,
}
