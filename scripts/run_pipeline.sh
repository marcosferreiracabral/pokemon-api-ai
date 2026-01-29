#!/bin/bash
# Script para executar o pipeline ETL.
# Uso: ./scripts/run_pipeline.sh

# Certifique-se de estar na raiz do projeto.
cd "$(dirname "$0")/.."

echo "Running ETL Pipeline..."
python etl/main.py
