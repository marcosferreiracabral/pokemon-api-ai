import pytest
from unittest.mock import MagicMock

def test_initialization(pokemon_agent):
    """Inicialização do agente de teste com ambiente simulado."""
    assert pokemon_agent.api_key == "sk-test-key"
    assert pokemon_agent.model == "gpt-5.2"

def test_process_message_simple_response(pokemon_agent, mock_openai):
    """Teste o processamento de mensagens simples sem chamadas de ferramentas."""
    response = pokemon_agent.process_message("Quem é Pikachu?")
    assert response == "Pikachu é um Pokémon elétrico."
    mock_openai.chat.completions.create.assert_called_once()

def test_process_message_with_tool_call(pokemon_agent, mock_openai, mocker):
    """Teste o processamento de mensagens com chamadas de ferramentas."""
    # Funções disponíveis simuladas:
    mock_tool_func = MagicMock(return_value='{"name": "pikachu", "type": "elétrico"}')
    mocker.patch.dict('agent.core.available_functions', {'get_pokemon_details': mock_tool_func})

    # Resposta simulada para LLM 1: Chamada de ferramentas:
    mock_msg_1 = MagicMock()
    mock_msg_1.content = None
    mock_msg_1.tool_calls = [
        MagicMock(
            id="call_123",
            function=MagicMock(
                name="get_pokemon_details",
                arguments='{"name": "pikachu"}'
            )
        )
    ]

    # Resposta simulada para o LLM 2: Resposta final:
    mock_msg_2 = MagicMock()
    mock_msg_2.content = "Pikachu é elétrico."
    mock_msg_2.tool_calls = None

    # Efeito colateral da configuração:
    mock_response_1 = MagicMock()
    mock_response_1.choices[0].message = mock_msg_1

    mock_response_2 = MagicMock()
    mock_response_2.choices[0].message = mock_msg_2

    mock_openai.chat.completions.create.side_effect = [mock_response_1, mock_response_2]

    response = pokemon_agent.process_message("Conte-me sobre Pikachu")

    assert response == "Pikachu é elétrico."
    assert mock_openai.chat.completions.create.call_count == 2
    mock_tool_func.assert_called_with(name="pikachu")

def test_tool_execution_error(pokemon_agent, mock_openai, mocker):
    """Test handling of tool execution errors."""
    # Função simulada que gera exceção:
    mock_tool_func = MagicMock(side_effect=Exception("Database error"))
    mocker.patch.dict('agent.core.available_functions', {'get_pokemon_details': mock_tool_func})

    # Resposta simulada para LLM 1: Chamada de ferramentas:
    mock_msg_1 = MagicMock()
    mock_msg_1.content = None
    mock_msg_1.tool_calls = [
        MagicMock(
            id="call_error",
            function=MagicMock(
                name="get_pokemon_details",
                arguments='{"name": "unknown"}'
            )
        )
    ]
    
    # Resposta simulada para o LLM 2: Resposta final após erro (o agente geralmente explica o erro):
    mock_msg_2 = MagicMock()
    mock_msg_2.content = "Desculpe, ocorreu um erro ao buscar o Pokémon."
    mock_msg_2.tool_calls = None

    mock_response_1 = MagicMock()
    mock_response_1.choices[0].message = mock_msg_1
    
    mock_response_2 = MagicMock()
    mock_response_2.choices[0].message = mock_msg_2

    mock_openai.chat.completions.create.side_effect = [mock_response_1, mock_response_2]

    response = pokemon_agent.process_message("Erro no banco")
    
    # Verifique se a saída da ferramenta enviada de volta para o LLM contém erros:
    call_args = mock_openai.chat.completions.create.call_args_list[1]
    messages = call_args[1]['messages']
    tool_message = messages[-1]
    
    assert tool_message['role'] == 'tool'
    assert "Database error" in tool_message['content']
