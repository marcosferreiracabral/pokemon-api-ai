import os
import sys

# Importar do módulo compartilhado
# Assumindo PYTHONPATH configurado corretamente
try:
    from common.config import load_config as _load_config_common
    from common.config import get_openai_api_key as _get_openai_api_key_common
except ImportError:
    sys.stderr.write("Aviso: Não foi possível importar common.config na pasta scripts.\n")
    _load_config_common = None
    _get_openai_api_key_common = None

def load_config():
    """
    Facade para common.config.load_config.
    """
    if _load_config_common:
        return _load_config_common()
    return {}

def get_openai_api_key():
    """
    Facade para common.config.get_openai_api_key.
    """
    if _get_openai_api_key_common:
        return _get_openai_api_key_common()
    return os.getenv("OPENAI_API_KEY")
