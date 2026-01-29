import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from common.logger import get_logger

logger = get_logger(__name__)

def configure_telemetry(service_name: str):
    """
    Configura o rastreamento e as métricas do OpenTelemetry.
    """
    resource = Resource.create(attributes={
        "service.name": service_name
    })

    # --- Rastreamento ---
    tracer_provider = TracerProvider(resource=resource)
    
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    
    if otlp_endpoint:
        try:
            span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            logger.info(f"Telemetry: Configuring OTLP/Trace exporter to {otlp_endpoint}")
        except Exception as e:
            logger.error(f"Failed to configure OTLP/Trace exporter: {e}")
            span_exporter = ConsoleSpanExporter()
    else:
        span_exporter = ConsoleSpanExporter()
        logger.info("Telemetry: OTLP endpoint not set, using Console/Trace exporter.")

    span_processor = BatchSpanProcessor(span_exporter)
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)

    # --- Métricas ---
    if otlp_endpoint:
        try:
            metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
            logger.info(f"Telemetry: Configuring OTLP/Metric exporter to {otlp_endpoint}")
            reader = PeriodicExportingMetricReader(metric_exporter)
        except Exception as e:
            logger.error(f"Failed to configure OTLP/Metric exporter: {e}")
            reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
    else:
        reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
        logger.info("Telemetry: OTLP endpoint not set, using Console/Metric exporter.")

    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)
    
    return tracer_provider, meter_provider
