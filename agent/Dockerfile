# Etapa 1: Verificação de segurança com o Trivy:
FROM aquasec/trivy:latest AS security
COPY requirements.txt .
# Analisar o arquivo de requisitos em busca de vulnerabilidades de alta/crítica gravidade.
# Usamos --exit-code 0 por padrão para não interromper a compilação durante esta demonstração,
# mas em produção você pode querer usar --exit-code 1.
RUN trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 0 requirements.txt

# Etapa 2: Construtor
FROM python:3.10-slim AS construtor
WORKDIR /app
ENV PYTHONIOENCODING=utf-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Etapa 3: Imagem Final:
FROM python:3.10-slim
WORKDIR /app

# Configuração de Locale para pt_BR.UTF-8:
RUN apt-get update && apt-get install -y locales && \
    sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=pt_BR.UTF-8
ENV LC_ALL=pt_BR.UTF-8
ENV PYTHONIOENCODING=utf-8

# Copia artefatos do construtor:
COPY --from=construtor /app/wheels /wheels
COPY --from=construtor /app/requirements.txt .

# Instalar dependências:
RUN pip install --no-cache-dir /wheels/*

# Copiar código da aplicação:
COPY common /app/common
COPY agent /app/agent

# Adicionar common e agent ao PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Copiar e configurar entrypoint:
COPY agent/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# A flag -u é mantida no ponto de entrada para saída sem buffer:
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-u", "agent_app.py"]
