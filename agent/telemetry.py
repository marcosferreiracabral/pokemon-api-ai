# Importar do módulo compartilhado:
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from agent.logger import get_logger

logger = get_logger(__name__)

def configure_telemetry(service_name: str = "pokemon-agent"):
    """
    Configura o rastreamento do OpenTelemetry para o agente.
    """
    resource = Resource.create(attributes={
        "service.name": service_name
    })

    provider = TracerProvider(resource=resource)
    
    # Verifique se o endpoint OTLP está configurado:
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    
    if otlp_endpoint:
        # Utilize o exportador OTLP se o endpoint for fornecido:
        try:
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            logger.info(f"Telemetry: Configuring OTLP exporter to {otlp_endpoint}")
        except Exception as e:
            logger.error(f"Failed to configure OTLP exporter: {e}")
            exporter = ConsoleSpanExporter()
    else:
        # Para desenvolvimento, utilize o Console Exporter como alternativa:
        exporter = ConsoleSpanExporter()
        logger.info("Telemetry: OTLP endpoint not set, using Console exporter.")

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    
    # Defina o provedor de rastreamento global:
    trace.set_tracer_provider(provider)
    
    return provider
