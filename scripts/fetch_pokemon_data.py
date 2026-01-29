import sys
import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any

# Adicionar raiz do projeto ao PYTHONPATH para permitir imports do módulo 'agent':
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from common.logger import configure_logging, get_logger

# Configurar logs:
configure_logging()
logger = get_logger("fetch_pokemon_data")

POKEAPI_URL = "https://pokeapi.co/api/v2/pokemon"

def buscar_dados_pokemon(limite: int = 150) -> Optional[List[Dict[str, Any]]]:
    """
    Busca dados de Pokémon da PokéAPI.
    
    Args:
        limite (int): Número máximo de Pokémons a buscar.
        
    Returns:
        Optional[List[Dict[str, Any]]]: Lista de dados de Pokémon processados ou None em caso de erro.
    """
    url = f"{POKEAPI_URL}?limit={limite}"
    
    logger.info(f"Buscando dados de {url}...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        dados = response.json()
        
        lista_pokemon = dados.get("results", [])
        
        dados_processados = []
        for item in lista_pokemon:
            # Exemplo de item: {'name': 'bulbasaur', 'url': 'https://pokeapi.co/api/v2/pokemon/1/'}
            partes_url = item['url'].strip('/').split('/')
            try:
                pokemon_id = int(partes_url[-1])
            except ValueError:
                logger.warning(f"Não foi possível extrair ID da URL: {item['url']}")
                continue

            dados_processados.append({
                "id": pokemon_id,
                "name": item['name'],
                "url": item['url'],
                "image_url": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_id}.png"
            })
            
        logger.info(f"{len(dados_processados)} Pokémons processados com sucesso.")
        return dados_processados

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao buscar dados da API: {e}")
        return None
    except Exception as e:
        logger.exception(f"Erro inesperado ao processar dados: {e}")
        return None

def salvar_dados(dados: List[Dict[str, Any]], nome_arquivo: str = "data/raw/pokemon_data.json") -> None:
    """
    Salva a lista de dados em um arquivo JSON.
    
    Args:
        dados (List[Dict[str, Any]]): Dados a serem salvos.
        nome_arquivo (str): Caminho relativo ou absoluto do arquivo de destino.
    """
    if not dados:
        logger.warning("Nenhum dado para salvar.")
        return

    caminho_arquivo = Path(nome_arquivo)
    
    # Se o caminho for relativo, considere relativo à raiz do projeto (para facilitar execução via scripts/):
    if not caminho_arquivo.is_absolute():
        caminho_arquivo = project_root / caminho_arquivo

    try:
        # Criar diretório se não existir
        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Dados salvos com sucesso em {caminho_arquivo}")
        
    except IOError as e:
        logger.error(f"Erro ao salvar arquivo em {caminho_arquivo}: {e}")

if __name__ == "__main__":
    # Execução principal:
    logger.info("Iniciando script de busca de dados...")
    
    dados_pokemon = buscar_dados_pokemon(limite=150)
    
    if dados_pokemon:
        salvar_dados(dados_pokemon, nome_arquivo="data/raw/pokemon_data.json")
    else:
        logger.error("Falha na execução do script.")
