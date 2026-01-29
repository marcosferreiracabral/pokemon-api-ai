
# Importar do módulo compartilhado:
import logging
import json
import sys
import contextvars
import uuid
import re
from typing import Optional, Any
from opentelemetry import trace
from agent.config import APP_ENV, ENABLE_JSON_LOGS

# Chaves que indicam dados sensíveis:
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
            "service": "pokemon-agent",
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
            "correlation_id": get_correlation_id()
        }
        
        # Redação adicional no objeto final, se necessário, embora 'message' já seja uma string aqui.
        # Idealmente, não deveríamos colocar segredos brutos em strings de mensagens.
        
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
    """
    Retorna um logger com o nome especificado.
    Dependência da configuração do logger raiz para manipuladores/formatadores.
    """
    return logging.getLogger(name)

def configure_logging():
    """Configura o logger raiz com base nas configurações do ambiente."""
    use_json = ENABLE_JSON_LOGS or APP_ENV == "production"
    
    handler = logging.StreamHandler(sys.stdout)
    if use_json:
        handler.setFormatter(JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%SZ"))
    else:
        # Formato padrão legível por humanos com ID de correlação, se presente:
        class CorrelationFormatter(logging.Formatter):
            def format(self, record):
                cid = get_correlation_id()
                prefix = f"[{cid}] " if cid else ""
                return prefix + super().format(record)

        handler.setFormatter(CorrelationFormatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', 
            datefmt="%Y-%m-%dT%H:%M:%SZ"
        ))
    
    # Configura o logger raiz:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remova os manipuladores existentes para evitar duplicatas caso sejam reconfigurados:
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(handler)
    
    # Ajuste os níveis para algumas bibliotecas ruidosas, se necessário:
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
