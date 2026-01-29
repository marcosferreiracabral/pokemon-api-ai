# DOCUMENTAÇÃO TÉCNICA - POKÉMON API AI PLATFORM
# Autor: Marcos Ferreira Cabral
# Data: 28/01/2026
# Versão: 1.1.0

## 1. VISÃO EXECUTIVA
Esta Prova de Conceito (PoC) demonstra uma arquitetura de dados moderna e escalável, integrando engenharia de dados (ETL), orquestração de workflows e Inteligência Artificial Generativa. O sistema ingere dados da PokéAPI, normaliza-os em um Data Warehouse relacional e democratiza o acesso através de uma API RESTful e de um Assistente Virtual conversacional.

O diferencial deste projeto é a adesão a padrões "Senior Level" de engenharia, incluindo:
*   **Clean Architecture**: Separação clara de responsabilidades na API (Controller, Service, Repository).
*   **Hibridismo de Dados**: Consumo flexível via API (Online) ou Cache Local JSON (Offline).
*   **Orquestração Robusta**: Apache Airflow para gerenciamento de dependências.
*   **Modularidade**: Arquitetura de microsserviços com código compartilhado (`common`).
*   **Observabilidade**: Logs estruturados em Português e Tracing via OpenTelemetry.
*   **Qualidade de Dados**: Schemas rigorosos com Pydantic e Pandera.

---

## 2. ARQUITETURA DE SOLUÇÃO

### 2.1. Diagrama Lógico
[Apache Airflow] --(Trigger)--> [ETL CLI (Docker)] -> (Write) <-> [Pydantic Models]
                                          |
                                       (Write)
                                          v
                                   [PostgreSQL DW]
                                          ^
                                       (Read)
                                          |
                               [API Repository Layer]
                                          ^
                                          |
                                [API Service Layer]
                                          ^
                                          |
[Streamlit Frontend] <--(Switch)--> [FastAPI Backend] <-> [Redis Cache]
            |
            +--(Offline Fallback)--> [Local JSON Cache (data/raw)]
            |
            v
       [AI Agent] <-> [OpenAI GPT-4]

### 2.2. Componentes Principais

#### A. Camada de Infraestrutura e Compartilhamento (`common`):
- **Localização**: `/common` e `docker-compose.yml`.
- **Função**: Prover utilitários transversais para todos os serviços.
- **Destaques**:
    - **Configuração Unificada**: Módulo `common.config` centraliza segredos.
    - **Scripts DevOps**: Scripts em `/scripts` para setup de ambiente (`setup_dev_env.sh`) e gestão Git (`sync_repo.sh`).

#### B. Camada de Orquestração (Airflow):
- **Localização**: `/airflow`
- **Função**: Agendamento e gerenciamento de dependências.
- **Destaque**: DAG (`airflow/dags/etl_dag.py`) modular.

#### C. Camada de Ingestão (ETL CLI):
- **Localização**: `/etl`
- **Tecnologia**: Python + Typer + Pandas.
- **Funcionalidade**: CLI granular (`run-pipeline`).
- **Qualidade**: Validação forte de tipos. Logs padronizados.

#### D. Camada de Persistência (Database & Cache):
- **Localização**: `/db` (PostgreSQL) e `/data` (JSON Local).
- **Tecnologia**: PostgreSQL 15 e Sistema de Arquivos (JSON).
- **Modelagem**: Star Schema no banco; Raw Data no cache local para acesso offline rápido.

#### E. Camada de API (Backend):
- **Localização**: `/api`
- **Tecnologia**: FastAPI (Async) + Redis + SQLAlchemy.
- **Arquitetura**: Clean Architecture (Repository/Service/Controller).
- **Observabilidade**: Logger JSON com `trace_id`.

#### F. Camada de Aplicação (Frontend/Agent):
- **Localização**: `/agent` e `/scripts`.
- **Tecnologia**: Streamlit + OpenAI GPT-5.2.
- **Funcionalidade**: Agente ReAct Híbrido. Pode consultar a API ou usar dados locais (`data/raw`) se a API estiver indisponível ou para performance.

---

## 3. ESTRUTURA DO PROJETO ATUALIZADA

```
project-root/
├── .openai_config.txt       # [SEGURANÇA] Gestão de Segredos Local
├── docker-compose.yml       # [INFRA] Orquestração de Serviços
├── common/                  # [SHARED] Código compartilhado
│   ├── config.py            
│   └── __init__.py
├── data/                    # [DADOS] Armazenamento Local
│   └── raw/                 # Cache JSON bruto (ex: pokemon_data.json)
├── airflow/                 # [ORQUESTRAÇÃO] Configuração do Airflow
├── agent/                   # [IA] Agente Inteligente
├── api/                     # [BACKEND] API RESTful
│   ├── main.py              
│   ├── services/            
│   └── repositories/        
├── db/                      # [Banco] Schemas e Migrations
├── etl/                     # [ENGENHARIA] CLI de ETL 
├── tests/                   # [QA] Testes Automatizados
│   ├── load_test_ws_async.py
│   └── test_schemas.py
└── scripts/                 # [UTILITÁRIOS] Automação e Runbooks
    ├── app.py               # Interface Streamlit (Frontend)
    ├── etl.py               # Script de Teste/Verificação de Logs ETL
    ├── fetch_pokemon_data.py# Script para popular cache local (data/raw)
    ├── init_git_repo.sh     # Inicialização de repositório Git
    ├── setup_dev_env.sh     # Configuração de ambiente dev
    ├── sync_repo.sh         # Sincronização com Remote Git
    └── run_pipeline.sh      # Atalho para execução do pipeline
```

---

## 4. PROCEDIMENTOS OPERACIONAIS (RUNBOOKS)

### 4.1. Configuração Inicial e Infraestrutura
```bash
# 1. Configurar ambiente de desenvolvimento (Linux/WSL/GitBash)
./scripts/setup_dev_env.sh

# 2. Subir infraestrutura Docker
docker-compose up --build -d
```

### 4.2. Carga de Dados (Estratégia Híbrida)

**Opção A: Pipeline Completo (DW + API)**
```bash
# Executa o pipeline ETL via Airflow ou direto pelo container/script
python etl/main.py run-pipeline --limit 50
```

**Opção B: Cache Local (Rápido/Offline)**
```bash
# Baixa dados da PokéAPI e salva em data/raw/pokemon_data.json
python scripts/fetch_pokemon_data.py
```

### 4.3. Monitoramento e Controle de Versão
**Sincronizar Repositório:**
```bash
./scripts/sync_repo.sh
```

**Verificação de Logs ETL:**
```bash
python scripts/etl.py
```

---

## 5. RECOMENDAÇÕES DO DESENVOLVEDOR (ROADMAP)

1.  **Segurança**: Migrar credenciais do `.openai_config.txt` para Vault/AWS Secrets Manager.
2.  **Testes**: Expandir suite em `tests/` para cobertura da Camada de Serviço (API) e testes E2E do Agente.
3.  **CI/CD**: Pipeline GitHub Actions para lint (`ruff`) e testes (`pytest`).
4.  **Escalabilidade**: Avaliar migração para MWAA (Airflow Gerenciado).

---

## 6. REFERÊNCIAS

### Bibliotecas e Ferramentas

| Biblioteca | URL de Referência Oficial |
| :--- | :--- |
| **docker** | [docker-py.readthedocs.io](https://docker-py.readthedocs.io/en/stable/) |
| **fastapi** | [fastapi.tiangolo.com](https://fastapi.tiangolo.com) |
| **openai** (Python SDK) | [platform.openai.com/docs/libraries](https://platform.openai.com/docs/libraries) |
| **opentelemetry** | [opentelemetry.io](https://opentelemetry.io/) |
| **pandas** | [pandas.pydata.org/docs](https://pandas.pydata.org/docs/) |
| **pandera** | [pandera.readthedocs.io](https://pandera.readthedocs.io/en/stable/) |
| **pydantic** | [docs.pydantic.dev](https://docs.pydantic.dev/latest/) |
| **pytest** | [docs.pytest.org](https://docs.pytest.org/en/stable/) |
| **streamlit** | [docs.streamlit.io](https://docs.streamlit.io/) |
| **sqlalchemy** | [docs.sqlalchemy.org](https://docs.sqlalchemy.org/en/20/) |
