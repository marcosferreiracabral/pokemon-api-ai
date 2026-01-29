# Importar do módulo compartilhado:
import os
import sys

def load_config():
    """
    Carrega a configuração do arquivo .openai_config.txt localizado na raiz do projeto.
    Retorna um dicionário com a configuração.
    """
    # Determina a raiz do projeto.
    # Assumindo que este arquivo está em <root>/common/config.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    config_path = os.path.join(project_root, ".openai_config.txt")
    
    config = {}
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Ignore os comentários e as linhas em branco:
                    if not line or line.startswith("#"):
                        continue
                    
                    if "=" in line:
                        key, value = line.split("=", 1)
                        value = value.strip()
                        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                             value = value[1:-1]
                        config[key.strip()] = value
        except Exception as e:
            sys.stderr.write(f"Erro ao ler o arquivo de configuração: {e}\n")
            
    return config

# Carregar uma vez no nível do módulo (Singleton pattern implícito):
_config = load_config()

def get_openai_api_key():
    """
    Função auxiliar para obter a chave da API OpenAI, priorizando o arquivo de configuração
    e recorrendo a variáveis de ambiente.
    """
    key = _config.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    return key

# Constantes de Configuração Gerais
APP_ENV = os.getenv("APP_ENV", "development")
ENABLE_JSON_LOGS = os.getenv("ENABLE_JSON_LOGS", "false").lower() == "true"
# URL base da API interna (usada pelo Agente e Scripts)
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
