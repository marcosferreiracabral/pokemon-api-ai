
# Importar do módulo compartilhado:
import os
import sys

try:
    from common.config import load_config as _load_config_common
    from common.config import get_openai_api_key as _get_openai_api_key_common
except ImportError:
    # Fallback para execução local sem estrutura de pacote completa ou antes do ajuste do PYTHONPATH:
    sys.stderr.write("Aviso: Não foi possível importar common.config. Verifique o PYTHONPATH.\n")
    _load_config_common = None
    _get_openai_api_key_common = None

# Define constantes de configuração com valores padrão ou a partir de variáveis de ambiente:
APP_ENV = os.getenv("APP_ENV", "development")
ENABLE_JSON_LOGS = os.getenv("ENABLE_JSON_LOGS", "false").lower() == "true"
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

def load_config():
    """
    Facade para common.config.load_config.
    """
    if _load_config_common:
        return _load_config_common()
    return {}

# Carregar uma vez no nível do módulo:
_config = load_config()

def get_openai_api_key():
    """
    Facade para common.config.get_openai_api_key.
    """
    if _get_openai_api_key_common:
        return _get_openai_api_key_common()
    return os.getenv("OPENAI_API_KEY")

# Exponha a chave da API como uma constante:
OPENAI_API_KEY = get_openai_api_key()
