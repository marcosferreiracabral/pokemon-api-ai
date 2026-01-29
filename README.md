# Pokémon API AI Platform

**Uma plataforma moderna de Engenharia de Dados e Inteligência Artificial para análise do universo Pokémon.**

Este projeto demonstra uma arquitetura escalável e robusta, integrando pipelines de dados (ETL), orquestração, APIs RESTful com **Clean Architecture** e Agentes de IA Generativa com capacidades híbridas (Online/Offline).

---

## Arquitetura

O sistema adota uma abordagem de microsserviços modulares e "Clean Architecture":

*   **Ingestão (ETL)**: CLI Granular (`etl/`) que consome dados da [PokéAPI](https://pokeapi.co/), valida schemas com `Pydantic`/`Pandera` e normaliza para um Data Warehouse (PostgreSQL).
*   **Orquestração**: Apache Airflow (`airflow/`) para agendamento e gerenciamento de dependências com DAGs modulares.
*   **API (Backend)**: Desenvolvida em **FastAPI** (Async) seguindo o padrão **Repository/Service**, garantindo isolamento de regras de negócio.
*   **Aplicação Híbrida (Frontend/Agent)**: Interface **Streamlit** com um **Agente AI (GPT-5.2)**. O sistema opera em modo híbrido:
    *   **Online**: Consulta a API interna para dados processados e analytics.
    *   **Offline/Rápido**: Acessa um cache local JSON (`data/raw`) para fallback e alta performance.
*   **Infraestrutura Compartilhada**: Módulo `common/` para configuração centralizada (DRY) e utilitários.
*   **Observabilidade**: Logs estruturados (JSON) e Tracing distribuído via **OpenTelemetry**.

---

## Estrutura do Projeto

```bash
project-root/
├── .openai_config.txt        # [SEGURANÇA] Gestão de Segredos (Ignorado pelo Git)
├── docker-compose.yml        # [INFRA] Stack completa (Airflow, Postgres, Redis, API)
├── common/                   # [SHARED] Configuração e Logger unificados
├── data/                     # [DATA] Camada de dados local
│   └── raw/                  # Cache JSON (ex: pokemon_data.json)
├── airflow/                  # [ORQUESTRAÇÃO] DAGs e Configs do Airflow
├── agent/                    # [IA] Agente ReAct e Lógica do Chatbot
├── api/                      # [BACKEND] API RESTful (Clean Architecture)
│   ├── main.py               # Entrypoint / Controllers
│   ├── services/             # Serviços de Domínio
│   └── repositories/         # Acesso a Dados (SQLAlchemy)
├── db/                       # [DATABASE] Schemas e Migrations SQL
├── etl/                      # [ENGENHARIA] CLI de Extração e Carga
├── tests/                    # [QA] Suite de Testes
└── scripts/                  # [OPS] Runbooks e Automação
    ├── setup_dev_env.sh      # Setup inicial do ambiente
    ├── sync_repo.sh          # Sincronização segura Git
    ├── fetch_pokemon_data.py # Carga do Cache Local
    └── app.py                # Interface Streamlit
```

---

## Como Executar

### Pré-requisitos
- Docker Engine & Docker Compose.
- Python 3.10+ (para execução local de scripts).
- Chave de API da OpenAI.

### Configuração Inicial

1.  **Chave da OpenAI**:
    Crie o arquivo `.openai_config.txt` na raiz:
    ```ini
    OPENAI_API_KEY=sk-sua-chave-aqui
    ```

2.  **Ambiente de Desenvolvimento**:
    Execute o script de setup (Linux/WSL/GitBash) para criar venv e instalar dependências:
    ```bash
    ./scripts/setup_dev_env.sh
    ```

### Modos de Execução

#### A. Stack Completa (Recomendado para Dev/Prod)
Sobe Airflow, Banco de Dados, API e Frontend via Docker.

```bash
docker-compose up --build -d
```
*   **Web App**: [http://localhost:8501](http://localhost:8501)
*   **Airflow**: [http://localhost:8080/home](http://localhost:8080) (`airflow`/`airflow`)
*   **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

#### B. Modo Leve / Dados Locais
Para testar o Frontend ou analisar dados sem subir a infraestrutura completa de Containers.

1.  **Popular Cache Local**:
    ```bash
    python scripts/fetch_pokemon_data.py
    ```
2.  **Rodar App Streamlit**:
    ```bash
    streamlit run scripts/app.py
    ```

---

## Manutenção e Operações (SRE)

**Sincronização de Código (Git):**
Para atualizar seu repositório local com segurança (Stash -> Pull -> Pop):
```bash
./scripts/sync_repo.sh
```

**Verificação de Logs e Integridade:**
```bash
python scripts/etl.py
```

---

## Detalhes Técnicos

*   **Pydantic & Pandera**: Validação rigorosa de contratos de dados na entrada e saída.
*   **Tracing Context**: O `trace_id` é gerado na requisição do usuário e propagado por todos os microsserviços e logs.
*   **Repository Pattern**: A camada de dados (`api/repositories`) é desacoplada da regras de negócio, facilitando Mocks e Testes Unitários.
