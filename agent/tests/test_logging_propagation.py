
import pytest
import logging
import json
import uuid
from io import StringIO
from agent.logger import get_logger, set_correlation_id

def test_correlation_id_propagation_text_format():
    """
    Verifica se o ID de correlação está sendo propagado corretamente nos registros em formato de texto.
    """
    # 1. Captura stdout:
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    
    # Configure manualmente o formatador personalizado para simular um ambiente não JSON:
    from agent.logger import get_correlation_id
    class CorrelationFormatter(logging.Formatter):
        def format(self, record):
            cid = get_correlation_id()
            prefix = f"[{cid}] " if cid else ""
            return prefix + super().format(record)

    handler.setFormatter(CorrelationFormatter('%(message)s'))
    
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # 2. Definir ID de correlação:
    test_cid = str(uuid.uuid4())
    set_correlation_id(test_cid)

    # 3. Registre algo:
    logger = get_logger("test_logger")
    logger.info("Test message with correlation ID")

    # 4. Verificar saída:
    log_output = stream.getvalue()
    assert test_cid in log_output
    assert "Test message with correlation ID" in log_output

def test_correlation_id_propagation_json_format():
    """
    Verifica se o ID de correlação está sendo propagado corretamente nos registros em formato JSON.
    """
    # 1. Capturar stdout:
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    
    # Configurar formatador JSON:
    from agent.logger import JsonFormatter
    handler.setFormatter(JsonFormatter())
    
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # 2. Definir ID de correlação
    test_cid = str(uuid.uuid4())
    set_correlation_id(test_cid)

    # 3. Registre algo
    logger = get_logger("test_logger_json")
    logger.info("Test JSON message")

    # 4. Verificar saída:
    log_output = stream.getvalue()
    try:
        log_json = json.loads(log_output)
    except json.JSONDecodeError:
        pytest.fail(f"Could not decode JSON: {log_output}")
        
    assert log_json["correlation_id"] == test_cid
    assert log_json["message"] == "Test JSON message"
    assert log_json["level"] == "INFO"

def test_missing_correlation_id():
    """
    Verifica o comportamento quando o ID de correlação não está definido.
    """
    # Redefinir variável de contexto:
    set_correlation_id(None)
    
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s")) # Formatador básico:
    
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    
    logger = get_logger("test_no_cid")
    logger.info("No CID message")
    
    assert "No CID message" in stream.getvalue()
