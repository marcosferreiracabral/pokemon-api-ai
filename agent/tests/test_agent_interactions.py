
import pytest
from unittest.mock import MagicMock, patch
import logging
from agent.core import PokemonAgent

# Configure o registro de logs para testes:
logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def mock_openai_client():
    mock_client = MagicMock()
    return mock_client

@pytest.fixture
def agent(mock_openai_client):
    # Corrija o problema com a função get_openai_api_key caso ela não esteja definida nas variáveis ​​de ambiente:
    with patch('agent.core.get_openai_api_key', return_value="fake-key"):
        agent = PokemonAgent()
        agent.client = mock_openai_client
        return agent

def test_basic_conversation_flow(agent, mock_openai_client):
    """
    Teste um fluxo de conversa básico sem chamadas de ferramentas (Adaptado de reproduce_issue.py):
    """
    # Configurar mocks:
    mock_response_1 = MagicMock()
    mock_response_1.choices = [MagicMock()]
    mock_response_1.choices[0].message.content = "Responder 1"
    mock_response_1.choices[0].message.tool_calls = None

    mock_response_2 = MagicMock()
    mock_response_2.choices = [MagicMock()]
    mock_response_2.choices[0].message.content = "Responder 2"
    mock_response_2.choices[0].message.tool_calls = None

    # Configurar efeito colateral para chamadas consecutivas:
    mock_openai_client.chat.completions.create.side_effect = [mock_response_1, mock_response_2]

    history = []

    # Transformar 1:
    user_input_1 = "Pergunta 1"
    response_1 = agent.process_message(user_input_1, history)
    
    assert response_1 == "Answer 1"
    
    # Verificar argumentos de chamada:
    call_args_1 = mock_openai_client.chat.completions.create.call_args_list[0]
    messages_1 = call_args_1.kwargs['messages']
    assert messages_1[-1]['role'] == 'user'
    assert messages_1[-1]['content'] == "Question 1"
    
    # Histórico de atualizações:
    history.append({"role": "user", "content": user_input_1})
    history.append({"role": "assistant", "content": response_1})

    # Transformar 2:
    user_input_2 = "Question 2"
    response_2 = agent.process_message(user_input_2, history)
    
    assert response_2 == "Answer 2"
    
    # Verificar argumentos de chamada:
    call_args_2 = mock_openai_client.chat.completions.create.call_args_list[1]
    messages_2 = call_args_2.kwargs['messages']
    assert messages_2[-3]['role'] == 'user'
    assert messages_2[-3]['content'] == "Question 1"
    assert messages_2[-2]['role'] == 'assistant'
    assert messages_2[-2]['content'] == "Answer 1"
    assert messages_2[-1]['role'] == 'user'
    assert messages_2[-1]['content'] == "Question 2"

def test_tool_call_execution(agent, mock_openai_client):
    """
    Teste se o agente executa corretamente as chamadas de ferramenta solicitadas pelo LLM.
    """
    # Configurar simulação para resposta de chamada de ferramenta:
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_123"
    mock_tool_call.function.name = "get_pokemon_info" # Supondo que essa ferramenta exista em available_functions:
    mock_tool_call.function.arguments = '{"pokemon_name": "pikachu"}'

    # Primeira resposta da LLM (ferramenta de solicitações).
    mock_response_tool = MagicMock()
    mock_response_tool.choices = [MagicMock()]
    mock_response_tool.choices[0].message.tool_calls = [mock_tool_call]
    mock_response_tool.choices[0].message.content = None # O conteúdo geralmente é nulo quando as chamadas de ferramenta estão presentes.

    # Segunda resposta da LLM (após a execução da ferramenta):
    mock_response_final = MagicMock()
    mock_response_final.choices = [MagicMock()]
    mock_response_final.choices[0].message.content = "Pikachu info: ..."
    mock_response_final.choices[0].message.tool_calls = None

    mock_openai_client.chat.completions.create.side_effect = [mock_response_tool, mock_response_final]

    # Simule a execução da ferramenta de verificação para evitar chamadas externas ou lógica complexa
    # Precisamos modificar as 'available_functions' em agent.core ou a função específica que ela chama
    with patch('agent.core.available_functions') as mock_functions:
        mock_tool_function = MagicMock(return_value='{"name": "pikachu", "type": "electric"}')
        mock_functions.get.return_value = mock_tool_function

        response = agent.process_message("Fale-me sobre Pikachu")

        # A ferramenta de verificação foi chamada:
        mock_functions.get.assert_called_with("get_pokemon_info")
        mock_tool_function.assert_called_with(pokemon_name="pikachu")

        # Verificar fluxo:
        assert response == "Pikachu info: ..."
        
        # Verifique se as mensagens enviadas ao LLM na segunda chamada incluem o resultado da ferramenta:
        second_call_args = mock_openai_client.chat.completions.create.call_args_list[1]
        messages = second_call_args.kwargs['messages']
        
        # Procure a mensagem da ferramenta:
        tool_msg = next((m for m in messages if m.get('role') == 'tool'), None)
        assert tool_msg is not None
        assert tool_msg['tool_call_id'] == "call_123"
        assert 'electric' in tool_msg['content']

def test_openai_api_error_handling(agent, mock_openai_client):
    """
    Testar o tratamento adequado de erros da API OpenAI:
    """
    mock_openai_client.chat.completions.create.side_effect = Exception("API Connection Erro")

    response = agent.process_message("Olá, agente!")

    assert "Erro ao processar sua solicitação" in response
    assert "API Connection Erro" in response
