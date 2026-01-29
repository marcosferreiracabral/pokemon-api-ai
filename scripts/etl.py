import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import logging
import main as etl_main
import load as etl_load
from agent.logger import get_logger, configure_logging

# Certifique-se de que o diretório raiz do projeto e o diretório ETL estejam no PATH:
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../'))
etl_dir = os.path.abspath(os.path.join(current_dir, '../etl'))

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if etl_dir not in sys.path:
    sys.path.insert(0, etl_dir)

# Configurar registro de logs:
configure_logging()
logger = get_logger(__name__)

class TestETLLogging(unittest.TestCase):
    @patch('extract.requests.get')
    @patch('extract.requests.Session')
    @patch('load.get_db_engine')
    @patch('load.load_data')
    def test_pipeline_runs_with_logging(self, mock_load, mock_engine, mock_session, mock_get):
        logger.info("\n--- Iniciando a verificação de registro ETL ---")
        
        # 1. Resposta simulada da lista:
        mock_list_response = MagicMock()
        mock_list_response.json.return_value = {
            "results": [
                {"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon/1/"}
            ]
        }
        mock_list_response.raise_for_status.return_value = None
        mock_get.return_value = mock_list_response
        
        # 2. Resposta detalhada simulada:
        mock_detail_response = MagicMock()
        mock_detail_response.json.return_value = {
            "id": 1,
            "name": "bulbasaur",
            "height": 7,
            "weight": 69,
            "stats": [
                {"base_stat": 45, "stat": {"name": "hp"}},
                {"base_stat": 49, "stat": {"name": "attack"}},
                {"base_stat": 49, "stat": {"name": "defense"}},
                {"base_stat": 65, "stat": {"name": "special-attack"}},
                {"base_stat": 65, "stat": {"name": "special-defense"}},
                {"base_stat": 45, "stat": {"name": "speed"}}
            ],
            "types": [
                {"slot": 1, "type": {"name": "grass"}},
                {"slot": 2, "type": {"name": "poison"}}
            ]
        }
        mock_detail_response.raise_for_status.return_value = None
        
        # A sessão simulada retorna uma resposta detalhada:
        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_detail_response
        mock_session_instance.__enter__.return_value = mock_session_instance
        mock_session.return_value = mock_session_instance

        # Executar principal:
        try:
            etl_main.main()
            logger.info("--- Verificação ETL concluída com sucesso ---")
        except SystemExit:
            self.fail("O processo ETL foi encerrado indiscriminadamente.")
        except Exception as e:
            logger.error(f"ETL failed with error: {e}", exc_info=True)
            self.fail(f"ETL falhou com erro: {e}")

        # Afirmações básicas:
        mock_load.assert_called_once()
        logger.info("Verificado que load_data foi chamado..")

if __name__ == "__main__":
    try:
        # Use um executor de testes que nos permita sair com o código 1 em caso de falha.
        # unittest.makeSuite foi removido em versões mais recentes do Python.
        suite = unittest.TestLoader().loadTestsFromTestCase(TestETLLogging)
        result = unittest.TextTestRunner().run(suite)
        if not result.wasSuccessful():
            sys.exit(1)
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unexpected error in test script: {e}", exc_info=True)
        sys.exit(1)
