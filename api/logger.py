import logging
import os
import json
import sys
import contextvars
from typing import Optional, Any
from opentelemetry import trace

# Constantes - adaptando do estilo de agent/config.py se não estiverem presentes,
# ou codificando diretamente por enquanto, já que não temos uma configuração compartilhada.
# Em um cenário real, poderíamos querer uma biblioteca de configuração compartilhada ou importar de api.config.
SERVICE_NAME = "pokemon-api"
SENSITIVE_KEYS = {'password', 'token', 'key', 'secret', 'authorization', 'api_key', 'access_token'}

def _redact_sensitive_data(data: Any) -> Any:
    """
    Redige recursivamente dados sensíveis em dicionários e listas.
    """
    if isinstance(data, dict):
        return {
            k: ("***REDIGIDA***" if k.lower() in SENSITIVE_KEYS else _redact_sensitive_data(v))
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [_redact_sensitive_data(item) for item in data]
    else:
        return data

# ContextVar para ID de Correlação:
correlation_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("correlation_id", default=None)

def get_correlation_id() -> Optional[str]:
    return correlation_id_ctx.get()

def set_correlation_id(c_id: str):
    return correlation_id_ctx.set(c_id)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        # Tentar ocultar os argumentos se forem um dicionário (estilo de registro estruturado):
        if isinstance(record.args, dict):
             record.args = _redact_sensitive_data(record.args)
        
        # Construa o objeto de log:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": SERVICE_NAME,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
            "correlation_id": get_correlation_id()
        }
        
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        # Adicione contexto de rastreamento do OpenTelemetry se disponível:
        span = trace.get_current_span()
        if span:
            span_context = span.get_span_context()
            if span_context.is_valid:
                log_obj["trace_id"] = f"{span_context.trace_id:032x}"
                log_obj["span_id"] = f"{span_context.span_id:016x}"

        return json.dumps(log_obj)

def get_logger(name: str):
    return logging.getLogger(name)

def configure_logging():
    """Configura o logger raiz."""
    # Forçar logs JSON para consistência ou com base em variáveis ​​de ambiente:
    use_json = os.getenv("ENABLE_JSON_LOGS", "true").lower() == "true"
    
    handler = logging.StreamHandler(sys.stdout)
    if use_json:
        handler.setFormatter(JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%SZ"))
    else:
        # Formato alternativo:
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', 
            datefmt="%Y-%m-%dT%H:%M:%SZ"
        ))
    
    # Configura o logger raiz:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remova os manipuladores existentes
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(handler)
    
    # Ajuste os níveis para algumas bibliotecas ruidosas
    logging.getLogger("uvicorn.access").handlers = [] # Desative o logger de acesso padrão do uvicorn para evitar duplicatas/confusão,
    # se quisermos controle total, ou deixe como está.
    # Por agora, vamos apenas acalmar alguns liberais:
    logging.getLogger("httpx").setLevel(logging.WARNING)
