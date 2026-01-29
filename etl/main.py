# Importar do módulo compartilhado:
import sys
import os
import time
import logging
import typer
from opentelemetry import trace, metrics

# Garantir que possamos importar da API:
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import extract
import transform
import load
from api.telemetry import configure_telemetry

# Configurar registro:
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Inicializar a CLI:
app = typer.Typer(help="Pokemon ETL Pipeline CLI")

# Inicializar Telemetria:
tracer_provider, meter_provider = configure_telemetry("pokemon-etl")
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Métricas:
counter_extracted = meter.create_counter("pokemon.extracted.total", description="Total records extracted")
counter_transformed = meter.create_counter("pokemon.transformed.total", description="Total records transformed")
counter_loaded = meter.create_counter("pokemon.loaded.total", description="Total records loaded")
histogram_duration = meter.create_histogram("pokemon.pipeline.duration", description="Pipeline execution duration")

@app.command()
def run_pipeline(limit: int = typer.Option(151, help="Number of Pokemon to process")):
    """
    Executa o pipeline ETL completo (Extrair -> Transformar -> Carregar).
    """
    with tracer.start_as_current_span("run_pipeline") as span:
        span.set_attribute("pipeline.limit", limit)
        logger.info(f"Initializing ETL Pipeline with limit={limit}...")
        start_time = time.time()
        
        try:
            # Extrai:
            with tracer.start_as_current_span("extract"):
                raw_data = extract.fetch_pokemon_data(limit=limit)
                count_extracted = len(raw_data)
                span.set_attribute("pipeline.extracted_count", count_extracted)
                counter_extracted.add(count_extracted)

            # Transforma:
            with tracer.start_as_current_span("transform"):
                df_pokemon, df_dim_type, df_types_link, df_stats = transform.transform_data(raw_data)
                count_transformed = len(df_pokemon)
                span.set_attribute("pipeline.transformed_count", count_transformed)
                counter_transformed.add(count_transformed)
            
            # Carrega:
            with tracer.start_as_current_span("load"):
                load.load_data(df_pokemon, df_dim_type, df_types_link, df_stats)
                counter_loaded.add(count_transformed) # Supondo que todos os dados transformados estejam carregados.
            
            duration = time.time() - start_time
            logger.info(f"ETL pipeline completed in {duration:.2f} seconds.")
            span.set_attribute("pipeline.duration", duration)
            histogram_duration.record(duration)
            
        except Exception as e:
            logger.critical(f"ETL pipeline failed: {e}", exc_info=True)
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            sys.exit(1)

@app.command()
def extract_only(limit: int = 10, output_file: str = "extracted.json"):
    """
    Executa apenas a etapa de extração e salva o resultado em um arquivo (implementação fictícia para demonstração).
    """
    with tracer.start_as_current_span("extract_only"):
        data = extract.fetch_pokemon_data(limit=limit)
        count = len(data)
        counter_extracted.add(count)
        logger.info(f"Extracted {count} records.")

if __name__ == "__main__":
    app()
