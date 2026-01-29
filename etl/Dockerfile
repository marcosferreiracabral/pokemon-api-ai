# --- Etapa 1: Construtor ---
FROM python:3.10-slim as construtor

WORKDIR /app

# Instalar dependências de compilação (comentado se não for necessário)
# RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# --- Etapa 2: Tempo de execução ---
FROM python:3.10-slim

WORKDIR /app

# Instalar dependências de tempo de execução (libpq para psycopg2):
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário sem privilégios de root:
RUN useradd -m appuser

# Copiar os pacotes instalados do construtor:
COPY --from=construtor /root/.local /home/appuser/.local

# Atualiza o:PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Copiar código do aplicativo:
COPY . .

# Alterar propriedade:
RUN chown -R appuser:appuser /app

# Alternar para usuário sem privilégios de root:
USER appuser

CMD ["python", "main.py"]
