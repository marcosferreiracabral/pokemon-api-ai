import logging
import json
import sys
import contextvars
import os
from typing import Optional, Any
from opentelemetry import trace
from common.config import APP_ENV, ENABLE_JSON_LOGS

# Constantes
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

# ContextVar para ID de Correlação
correlation_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("correlation_id", default=None)

def get_correlation_id() -> Optional[str]:
    return correlation_id_ctx.get()

def set_correlation_id(c_id: str):
    return correlation_id_ctx.set(c_id)

class JsonFormatter(logging.Formatter):
    def __init__(self, service_name: str, **kwargs):
        super().__init__(**kwargs)
        self.service_name = service_name

    def format(self, record):
        # Redação de dados sensíveis nos argumentos
        if isinstance(record.args, dict):
             record.args = _redact_sensitive_data(record.args)
        
        # Objeto de log estruturado
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": self.service_name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
            "correlation_id": get_correlation_id()
        }
        
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        # Contexto OpenTelemetry
        span = trace.get_current_span()
        if span:
            span_context = span.get_span_context()
            if span_context.is_valid:
                log_obj["trace_id"] = f"{span_context.trace_id:032x}"
                log_obj["span_id"] = f"{span_context.span_id:016x}"

        return json.dumps(log_obj)

class CorrelationFormatter(logging.Formatter):
    def format(self, record):
        cid = get_correlation_id()
        prefix = f"[{cid}] " if cid else ""
        return prefix + super().format(record)

def get_logger(name: str):
    return logging.getLogger(name)

def configure_logging(service_name: str = "pokemon-service"):
    """
    Configura o logger raiz.
    """
    use_json = ENABLE_JSON_LOGS or APP_ENV == "production"
    
    handler = logging.StreamHandler(sys.stdout)
    if use_json:
        handler.setFormatter(JsonFormatter(service_name=service_name, datefmt="%Y-%m-%dT%H:%M:%SZ"))
    else:
        handler.setFormatter(CorrelationFormatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', 
            datefmt="%Y-%m-%dT%H:%M:%SZ"
        ))
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(handler)
    
    # Ajuste de níveis para bibliotecas ruidosas
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
