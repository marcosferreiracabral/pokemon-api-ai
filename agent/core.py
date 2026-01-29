# Importar do módulo compartilhado:
import os
import json
import logging
from typing import Optional, List, Dict, Any
from openai import OpenAI

from agent.tools import tools_schema, available_functions
from common.config import get_openai_api_key
from agent.prompts import SYSTEM_PROMPT
from common.logger import get_logger

logger = get_logger(__name__)

class PokemonAgent:
    def __init__(self, model: str = "gpt-5.2"):
        self.api_key = get_openai_api_key()
        if not self.api_key:
            logger.warning("OPENAI_API_KEY Not found during agent initialization. Using mock key for testing.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("DEFAULT_MODEL", model)
        self.system_prompt = SYSTEM_PROMPT

    def process_message(self, user_input: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Processa uma mensagem do usuário e retorna a resposta do assistente.
        Lida com chamadas de ferramentas automaticamente.
        """
        if history is None:
            history = []

        messages = [{"role": "system", "content": self.system_prompt}] + history
        messages.append({"role": "user", "content": user_input})
        
        logger.debug(f"Input processing: {user_input}")

        try:
            # Primeira chamada para o LLM:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools_schema,
                tool_choice="auto", 
            )
            
            response_message = response.choices[0].message
            
            # Verifique as chamadas de ferramentas:
            if response_message.tool_calls:
                # Adicione a solicitação do assistente à conversa:
                messages.append(response_message)
                
                # Executar ferramentas:
                self._execute_tool_calls(response_message.tool_calls, messages)
                
                # Segunda chamada para o LLM:
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
                return second_response.choices[0].message.content
            else:
                return response_message.content

        except Exception as e:
            logger.error(f"Error processing input: {e}", exc_info=True)
            return f"Erro ao processar sua solicitação: {str(e)}"

    def _execute_tool_calls(self, tool_calls: List[Any], messages: List[Dict[str, Any]]) -> None:
        """
        Execute as chamadas de ferramenta detectadas e anexe os resultados à lista de mensagens.
        """
        logger.info(f"O agente decidiu chamar {len(tool_calls)} ferramentas")
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            function_to_call = available_functions.get(function_name)
            
            if not function_to_call:
                logger.error(f"Ferramenta {function_name} não encontrada.")
                function_response = json.dumps({"error": f"Tool {function_name} not found"})
            else:
                logger.info(f"Executing tool: {function_name} with args: {function_args}")
                try:
                    function_response = function_to_call(**function_args)
                except Exception as e:
                    logger.error(f"Falha na execução da ferramenta: {e}")
                    function_response = json.dumps({"error": str(e)})
            
            logger.debug(f"Tool response: {function_response}")
            
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )
