import pytest
from unittest.mock import MagicMock
from agent.core import PokemonAgent

@pytest.fixture
def mock_openai(mocker):
    """Simule o cliente OpenAI."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Pikachu é um Pokémon elétrico."
    mock_response.choices[0].message.tool_calls = None
    mock_client.chat.completions.create.return_value = mock_response
    
    # Corrija a classe OpenAI em agent.core:
    mocker.patch("agent.core.OpenAI", return_value=mock_client)
    return mock_client

@pytest.fixture
def mock_env(monkeypatch):
    """Configure as variáveis ​​de ambiente para os testes."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("APP_ENV", "test")

@pytest.fixture
def pokemon_agent(mock_env, mock_openai):
    """Inicialize um PokemonAgent com dependências simuladas."""
    return PokemonAgent()
