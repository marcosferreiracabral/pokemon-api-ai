# 1. CONSTRUTOR: Compilar rodas de dependências ("wheels"):
FROM python:3.10-slim AS construtor

COPY requirements.txt .
# Compila dependências em wheels para instalação rápida e offline na etapa final
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# 2. IMAGEM FINAL: Base Airflow limpa
FROM apache/airflow:2.10.2-python3.10

USER root

# Configuração de Localização (PT-BR) e limpeza de apt-lists para reduzir imagem
RUN apt-get update && \
    apt-get install -y --no-install-recommends locales && \
    sed -i 's/# pt_BR.UTF-8/pt_BR.UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure -f noninteractive locales && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Definir variáveis de ambiente para localização
ENV LANG=pt_BR.UTF-8 \
    LC_ALL=pt_BR.UTF-8

# Copiar wheels da etapa de construção
COPY --from=construtor /wheels /wheels
COPY requirements.txt .

# Alternar para o usuário airflow para instalar pacotes Python
USER airflow

# Instalar dependências a partir dos wheels pré-compilados
RUN pip install --no-cache-dir --prefer-binary --find-links=/wheels -r requirements.txt

