from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import pytest
from agent.agent_app import app

client = TestClient(app)

@pytest.fixture
def mock_app_agent(mocker):
    """Simule a instância do agente global em agent_app."""
    mock_agent = MagicMock()
    # Configure o mock para retornar uma resposta previsível:
    mock_agent.process_message.return_value = "Pika pika!"
    
    # Corrija a variável 'agent' no módulo agent_app:
    mocker.patch("agent.agent_app.agent", mock_agent)
    return mock_agent

def test_websocket_connection(mock_app_agent):
    """Teste de conexão WebSocket bem-sucedido."""
    with client.websocket_connect("/ws") as websocket:
        # A simples conexão deve funcionar sem problemas:
        pass

def test_websocket_message_flow(mock_app_agent):
    """Teste o envio de uma mensagem e o recebimento de uma resposta."""
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("Hello agent")
        response = websocket.receive_text()
        assert response == "Pika pika!"
        
        # O agente de verificação foi chamado:
        mock_app_agent.process_message.assert_called_once()
        args = mock_app_agent.process_message.call_args
        assert args[0][0] == "Hello agent" # O primeiro argumento é user_input:

def test_websocket_agent_not_initialized(mocker):
    """Comportamento do teste quando o agente não inicializa."""
    # Defina o agente como Nenhum:
    mocker.patch("agent.agent_app.agent", None)
    
    with client.websocket_connect("/ws") as websocket:
        response = websocket.receive_text()
        assert "Erro: Agente não inicializado" in response
        # A conexão deve ser fechada:
        with pytest.raises(Exception): # starlette.websockets.WebSocketDisconnect ou similar
             websocket.receive_text()

def test_websocket_disconnect(mock_app_agent):
    """Teste que a desconexão é tratada de forma graciosamente (nenhum erro levantado)."""
    with client.websocket_connect("/ws") as websocket:
        # Fechar imediatamente:
        websocket.close()
# Se o aplicativo não travar, o teste passa.
# Não podemos verificar os logs facilmente aqui sem capturá-los,
# mas o objetivo principal é garantir que o servidor não retorne 500.
