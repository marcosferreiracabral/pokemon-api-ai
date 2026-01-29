import streamlit as st
import os
import sys
import json
import requests
import pandas as pd
from openai import OpenAI
import sys
from pathlib import Path
from agent.tools import tools_schema, available_functions
from common.config import get_openai_api_key, API_BASE_URL
from common.logger import get_logger, set_correlation_id
from agent.prompts import SYSTEM_PROMPT

# Adicionar a raiz do projeto ao sys.path:
# Pressupõe-se que este arquivo esteja em <raiz_do_projeto>/scripts/:
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Inicializar o registrador do logger:
logger = get_logger("app")

# Configuração da página:
st.set_page_config(
    page_title="PokéAPI Agent",
    page_icon="🔮",
    layout="wide"
)

# Personaliza o CSS:
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #2b313e;
    }
    .assistant-message {
        background-color: #1a1c24;
    }
    h1 {
        color: #FFCB05;
        text-shadow: 2px 2px #3c5aa6;
    }
</style>
""", unsafe_allow_html=True)

# Inicializa o OpenAI Client:
if "openai_client" not in st.session_state:
    api_key = get_openai_api_key()
    if api_key:
        st.session_state.openai_client = OpenAI(api_key=api_key)
        logger.info("Cliente OpenAI inicializado com sucesso.")
    else:
        st.warning("OPENAI_API_KEY não encontrada nas variáveis de ambiente.")
        logger.error("OPENAI_API_KEY ausente.")

if "session_id" not in st.session_state:
    st.session_state.session_id = os.urandom(4).hex()
    logger.info(f"Nova sessão iniciada: {st.session_state.session_id}")

# Defina o contexto para esta execução (ID de correlação):
set_correlation_id(st.session_state.session_id)

# Prompt do sistema importado de agent.prompts:

def run_chat_turn(user_input, messages_history):
    client = st.session_state.openai_client
    
    # Adiciona a mensagem do usuário ao contexto temporário para esta execução.
    # Se 'messages_history' já contém a mensagem atual, não duplicar.
    # Ajuste: O chamador agora passa 'messages' completo, incluindo a ultima pergunta.
    
    # Construir mensagens: System Prompt + Histórico
    current_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages_history
    
    try:
        # Primeiro contato com o LLM:
        response = client.chat.completions.create(
            model="gpt-5.2",
            messages=current_messages,
            tools=tools_schema,
            tool_choice="auto",
            frequency_penalty=0.5  # Penalizar repetição
        )
        
        response_message = response.choices[0].message
        
        # Verifique as chamadas de ferramentas:
        if response_message.tool_calls:
            current_messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"Agent Tool Call: {function_name} Args={function_args}")
                
                if function_name in available_functions:
                    function_to_call = available_functions[function_name]
                    with st.status(f"Consultando Pokedex: {function_name}...", expanded=False) as status:
                        st.write(f"Args: {function_args}")
                        function_response = function_to_call(**function_args)
                        status.update(label="Consulta concluída!", state="complete")
                    
                    current_messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    })
            
            # Segunda chamada ao LLM com resultados da ferramenta:
            second_response = client.chat.completions.create(
                model="gpt-5.2",
                messages=current_messages,
                frequency_penalty=0.5
            )
            return second_response.choices[0].message.content
            
        else:
            return response_message.content
            
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return f"Ocorreu um erro: {str(e)}"

# --- UI Layout ---

st.title("🔮 PokéAPI AI Agent")

# Barra lateral para acesso direto aos dados:
with st.sidebar:
    st.header("Acesso direto aos dados 🚀")
    if st.button("Verificar integridade da API"):
        try:
            logger.info("Verificando integridade da API...")
            res = requests.get(f"{API_BASE_URL}/integrity", timeout=5)
            st.success(f"API Online! Status: 📡")
        except Exception as e:
            st.error(f"API Offline: {e}")
            logger.error(f"Falha na verificação de integridade da API: {e}")
            
    st.divider()
    
    st.subheader("📊 Estatísticas rápidas")
    
    # Mapa de tradução para estatísticas
    stats_map = {
        "Vida (HP)": "hp",
        "Ataque": "attack",
        "Defesa": "defense",
        "Ataque Especial": "special_attack",
        "Defesa Especial": "special_defense",
        "Velocidade": "speed"
    }
    
    selected_stat_label = st.selectbox("📝Tipo de classificação", list(stats_map.keys()))
    stat_type = stats_map[selected_stat_label]
    
    if st.button("Confira os 5 melhores🏆"):
        try:
            res = requests.get(f"{API_BASE_URL}/v1/stats/ranking", params={"stat": stat_type, "limit": 5}, timeout=10)
            if res.status_code == 200:
                df = pd.DataFrame(res.json())
                # Traduzir colunas para exibição
                df.columns = ["Ranking", "Nome", "Valor"]
                st.dataframe(df)
            else:
                st.error("Erro ao obter estatísticas")
                logger.error(f"Erro nas Estatísticas Rápidas: {res.status_code}")
        except Exception as e:
            st.error(f"Erro: {e}")
            logger.error(f"Erro nas Estatísticas Rápidas: {e}")

    st.divider()

    st.subheader("📂 Dados Locais (Offline)")
    if st.button("Carregar Dados Locais"):
        try:
            data_path = project_root / "data" / "raw" / "pokemon_data.json"
            if data_path.exists():
                with open(data_path, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                
                df_local = pd.DataFrame(local_data)
                st.success(f"Carregados {len(df_local)} Pokémons do arquivo local!")
                st.dataframe(df_local[["id", "name", "url"]])
            else:
                st.warning("Arquivo de dados local não encontrado. Execute scripts/fetch_pokemon_data.py primeiro.")
        except Exception as e:
            st.error(f"Erro ao carregar dados locais: {e}")
            logger.error(f"Erro ao carregar dados locais: {e}")

# Interface do Chat:
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibir histórico do chat:
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada do usuário:
if prompt := st.chat_input("Pergunte algo sobre Pokémons ⁉️..."):
    # Log interação
    logger.info(f"Entrada do usuário: {prompt}")

    # Exibir mensagem do usuário imediatamente:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Processo com Agente
    if "openai_client" in st.session_state:
        with st.chat_message("assistant"):
            # CORREÇÃO: Passar o histórico COMPLETO, incluindo a mensagem do usuário recém adicionada (prompt)
            response_text = run_chat_turn(prompt, st.session_state.messages)
            st.markdown(response_text)
        
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        logger.info(f"🤖 Resposta do agente: {response_text[:50]}...")
    else:
        st.error("Cliente OpenAI não inicializado. Verifique a chave da API.")
