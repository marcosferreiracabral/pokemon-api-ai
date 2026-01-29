# Importar do módulo compartilhado:
import os
import sys
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request

# Certifica-se de que a raiz do projeto esteja em PYTHONPATH:
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from common.config import get_openai_api_key
from agent.core import PokemonAgent
from common.logger import get_logger, configure_logging, set_correlation_id

from common.telemetry import configure_telemetry
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Configure o registro de logs explicitamente no ponto de entrada:
configure_logging(service_name="pokemon-agent")

# Configurar Telemetria:
configure_telemetry("pokemon-agent")
RequestsInstrumentor().instrument()

logger = get_logger("PokemonAgentApp")

# Inicialização da API
app = FastAPI(title="Pokemon Agent API")
FastAPIInstrumentor.instrument_app(app)

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    set_correlation_id(correlation_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = correlation_id
    return response

# Inicialização do Agente:
if not get_openai_api_key():
    logger.warning("OPENAI_API_KEY not defined. Agent will likely fail.")

try:
    agent = PokemonAgent()
    logger.info("PokemonAgent initialized successfully.")
except Exception as e:
    logger.critical(f"Failed to initialize the agent: {e}")
    agent = None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Gerar ID de correlação para sessão WebSocket:
    ws_correlation_id = str(uuid.uuid4())
    set_correlation_id(ws_correlation_id)
    
    history = []
    logger.info(f"New WebSocket connection accepted. Correlation ID: {ws_correlation_id}")
    
    if agent is None:
        await websocket.send_text("Erro: Agente não inicializado corretamente no servidor.")
        await websocket.close()
        return

    try:
        while True:
            user_input = await websocket.receive_text()
            
            # Processar mensagem com o agente:
            response = agent.process_message(user_input, history)
            
            # Enviar resposta:
            await websocket.send_text(response)
            
            # Atualizar histórico:
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": response})
            
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error in websocket connection: {e}", exc_info=True)
        try:
            await websocket.close()
        except:
            pass
