# --- Etapa 1: Construtor ---
FROM python:3.11-slim as builder

WORKDIR /app

# Impede que o Python escreva arquivos pyc e armazene stdout/stderr em buffer:
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependências de compilação:
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Criar ambiente virtual:
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Etapa 2: Tempo de execução ---
FROM python:3.11-slim

WORKDIR /app

# Impede que o Python escreva arquivos pyc e armazene stdout/stderr em buffer:
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependências de tempo de execução (curl para verificação de integridade):
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar ambiente virtual do construtor:
COPY --from=builder /opt/venv /opt/venv

# Criar usuário não-root:
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copiar código do aplicativo (incluindo módulo compartilhado 'common')
COPY --chown=appuser:appuser common ./common
COPY --chown=appuser:appuser api ./api


# Alternar para usuário não root
USER appuser

# Expor porta:
EXPOSE 8000

# Healthcheck:
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Executar aplicativo:
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
