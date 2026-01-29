import os
import unittest
from agent.config import load_config, get_openai_api_key

class TestConfig(unittest.TestCase):
    def test_load_config(self):
        config = load_config()
        self.assertTrue(isinstance(config, dict))
        # Esperamos que a chave OPENAI_API_KEY esteja no arquivo de configuração que criamos:
        self.assertIn("OPENAI_API_KEY", config)
        self.assertTrue(len(config["OPENAI_API_KEY"]) > 20)
        self.assertTrue(config["OPENAI_API_KEY"].startswith("sk-"))

    def test_get_openai_api_key(self):
        # Certifique-se de que estamos testando a chave baseada em arquivo; portanto,
        # remova a variável de ambiente para este teste, se presente:
        original_env_key = os.environ.get("OPENAI_API_KEY")
        if original_env_key:
            del os.environ["OPENAI_API_KEY"]
            
        try:
            key = get_openai_api_key()
            self.assertTrue(len(key) > 20)
            self.assertTrue(key.startswith("sk-"))
        finally:
            if original_env_key:
                os.environ["OPENAI_API_KEY"] = original_env_key

if __name__ == '__main__':
    unittest.main()
