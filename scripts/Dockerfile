FROM python:3.9-slim

WORKDIR /app

# Copiar requirements do frontend (assumindo que estão na pasta scripts ou na raiz, ajustando conforme necessidade):
COPY scripts/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar o diretório agent para /app/agent (necessário para imports):
COPY agent /app/agent

# Copiar o diretório common para /app/common:
COPY common /app/common

# Copiar o diretório scripts para /app/scripts:
COPY scripts /app/scripts

# Copiar dados locais (opcional, caso queira embutir na imagem):
COPY data /app/data

# Define a variável de ambiente PYTHONPATH para incluir /app:
ENV PYTHONPATH=/app

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "scripts/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
