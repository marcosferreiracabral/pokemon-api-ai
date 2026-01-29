#!/usr/bin/env bash

set -eo pipefail

# ================= CONFIGURAÇÃO =================
readonly APP_NAME="pokemon-agent"
readonly ALLOWED_COMMANDS=("python" "uvicorn" "gunicorn")
readonly REQUIRED_VARS=("OPENAI_API_KEY" "APP_ENV")
readonly ALLOWED_ENVS=("production" "development" "staging")

# ================= FUNÇÕES =================
should_use_json_logs() {
    if [[ "${ENABLE_JSON_LOGS}" == "true" ]]; then
        return 0
    elif [[ -z "${ENABLE_JSON_LOGS}" && "${APP_ENV}" == "production" ]]; then
        return 0
    fi
    return 1
}

log() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    if should_use_json_logs; then
        # Escapar aspas na mensagem para segurança JSON (implementação básica):
        local safe_message="${message//\"/\\\"}"
        printf '{"timestamp":"%s","level":"%s","service":"%s","message":"%s"}\n' \
               "$timestamp" "$level" "$APP_NAME" "$safe_message"
    else
        printf '[%s] [%s] [%s] %s\n' "$timestamp" "$level" "$APP_NAME" "$message"
    fi
}

validate_environment() {
    log "INFO" "Validando ambiente..."
    
    local missing=()
    for var in "${REQUIRED_VARS[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing+=("$var")
        else
            log "DEBUG" " $var está definido"
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log "ERROR" "Variáveis obrigatórias não definidas: ${missing[*]}"
        log "INFO" "Verifique se o arquivo .openai_config.txt está montado em /app/.openai_config.txt"
        exit 1
    fi
    
    # Validação APP_ENV:
    if [[ ! " ${ALLOWED_ENVS[@]} " =~ " ${APP_ENV} " ]]; then
        log "ERROR" "APP_ENV inválido: '$APP_ENV'. Valores permitidos: ${ALLOWED_ENVS[*]}"
        exit 1
    fi

    # Validação de chave OpenAI (formato básico):
    if [[ ! "$OPENAI_API_KEY" =~ ^sk-[a-zA-Z0-9_-]+$ ]]; then
        log "WARN" "Formato de OPENAI_API_KEY pode ser inválido (esperado cair no pattern sk-...)"
    fi
}

load_secrets() {
    local config_file="${1:-/app/.openai_config.txt}"
    
    if [[ -f "$config_file" ]]; then
        log "INFO" "Carregando configurações de $config_file"
        while IFS= read -r line || [[ -n "$line" ]]; do
            # Ignorar comentários e linhas vazias:
            [[ "$line" =~ ^#.*$ ]] && continue
            [[ -z "$line" ]] && continue
            
            # Corresponder KEY="VALUE":
            if [[ "$line" =~ ^([A-Z_]+)=\"(.*)\"$ ]]; then
                export "${BASH_REMATCH[1]}=${BASH_REMATCH[2]}"
            # Corresponder KEY=VALUE:
            elif [[ "$line" =~ ^([A-Z_]+)=(.*)$ ]]; then
                export "${BASH_REMATCH[1]}=${BASH_REMATCH[2]}"
            fi
        done < "$config_file"
    else
        log "WARN" "Arquivo de configuração não encontrado: $config_file"
    fi
}

validate_command() {
    local cmd="$1"
    
    if [[ ! " ${ALLOWED_COMMANDS[@]} " =~ " $cmd " ]]; then
        log "ERROR" "Comando não permitido: $cmd"
        log "INFO" "Comandos permitidos: ${ALLOWED_COMMANDS[*]}"
        return 1
    fi
    return 0
}

setup_brazil_environment() {
    export TZ="${TZ:-America/Sao_Paulo}"
    export LC_ALL="${LC_ALL:-pt_BR.UTF-8}"
    
    log "INFO" "Configurado para Brasil: Timezone=$TZ, Locale=$LC_ALL"
}

start_health_endpoint() {
    if [[ "$ENABLE_HEALTH_CHECK" == "true" ]]; then
        python -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import sys

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

try:
    server = HTTPServer(('0.0.0.0', 8080), HealthHandler)
    server.timeout = 5 # Add timeout
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    print('Health check endpoint iniciado na porta 8080 (timeout=5s)')
except Exception as e:
    print(f'Falha ao iniciar health check: {e}', file=sys.stderr)
        " &
    fi
}

# ================= EXECUÇÃO PRINCIPAL =================
main() {
    log "INFO" "Inicializando $APP_NAME"
    
    load_secrets
    setup_brazil_environment
    validate_environment
    
    if [[ $# -gt 0 ]]; then
        if ! validate_command "$1"; then
            exit 1
        fi
    fi
    
    start_health_endpoint
    
    log "INFO" "Todas validações passaram"
    log "INFO" "Executando: $*"
    
    trap 'kill -TERM $PID; wait $PID' TERM INT
    
    exec "$@"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
