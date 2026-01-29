#!/bin/bash

# Script de Instalação, Sincronização e Carga (Clone & Load & Pull)
# Autor: Tech Lead Sênior
# Descrição: Garante que o projeto esteja clonado, sincronizado com o remoto oficial e com dados carregados.

# URL Canônica do Repositório
REPO_URL="https://github.com/marcosferreiracabral/pokemon-api-ai.git"
TARGET_DIR="pokemon-api-ai"

# Cores para Logs
GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

print_msg() {
    echo -e "${GREEN}>> $1${RESET}"
}

print_warn() {
    echo -e "${YELLOW}!! $1${RESET}"
}

print_error() {
    echo -e "${RED}!! $1${RESET}"
}

# Função Para Sincronizar Git (Pull com verificação de Remote)
sync_git() {
    print_msg "Verificando configuração do remoto Git..."
    
    # Verifica se existe remoto 'origin', se não cria, se sim atualiza URL
    if git remote get-url origin &>/dev/null; then
        CURRENT_URL=$(git remote get-url origin)
        if [ "$CURRENT_URL" != "$REPO_URL" ]; then
            print_warn "URL de origem incorreta detectada: $CURRENT_URL"
            print_msg "Corrigindo remote origin para: $REPO_URL"
            git remote set-url origin "$REPO_URL"
        fi
    else
        print_msg "Remote 'origin' não definido. Adicionando: $REPO_URL"
        git remote add origin "$REPO_URL"
    fi

    print_msg "Sincronizando com o repositório remoto (git pull)..."
    git pull origin main || print_warn "Falha no git pull. Verifique se há alterações locais não commitadas."
}

# --- INÍCIO DO FLUXO ---
print_msg "Iniciando script de Clone & Load..."

# 1. Validação de Diretório e Clonagem
if [ -f "pyproject.toml" ] || [ -f "README.md" ]; then
    print_msg "Contexto: Já estamos dentro da raiz do projeto."
    if [ -d ".git" ]; then
        sync_git
    else
        print_warn "Este diretório parecia ser o projeto, mas não tem .git. Inicializando..."
        git init -b main
        sync_git
    fi
else
    # Não estamos na raiz
    if [ -d "$TARGET_DIR" ]; then
        print_msg "Diretório alvo '$TARGET_DIR' já existe."
        cd "$TARGET_DIR" || exit
        # Agora dentro do diretório, sincronizamos
        if [ -d ".git" ]; then
            sync_git
        else
            print_warn "Diretório existe mas não é git. Clonagem forçada necessária ou init."
            print_msg "Tentando inicializar e puxar..."
            git init -b main
            sync_git
        fi
    else
        print_msg "Clonando projeto de $REPO_URL..."
        git clone "$REPO_URL" "$TARGET_DIR" || { print_error "Falha crítica no git clone."; exit 1; }
        cd "$TARGET_DIR" || exit
    fi
fi

# 2. Setup de Ambiente (Venv + Dependências)
print_msg "Verificando Ambiente Virtual..."

# Configurar permissões para scripts auxiliares, se existirem
if [ -d "scripts" ]; then
    chmod +x scripts/*.sh 2>/dev/null
fi

if [ ! -d "venv" ]; then
    print_msg "Criando venv..."
    python -m venv venv
fi

print_msg "Ativando venv e instalando dependências..."
# Suporte multiplataforma para ativação
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Instalação silenciosa mas robusta
pip install --upgrade pip > /dev/null
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt | grep -v "Requirement already satisfied"
else
    print_warn "requirements.txt não encontrado. Pulei instalação de deps."
fi


# 3. Carga de Dados (Load)
print_msg "Executando Carga de Dados (Cache)..."
if [ -f "scripts/fetch_pokemon_data.py" ]; then
    python scripts/fetch_pokemon_data.py
else
    print_error "Script de carga 'scripts/fetch_pokemon_data.py' ausente."
fi

print_msg "============================================="
print_msg " Operação CLONE & LOAD & PULL Finalizada! "
print_msg "============================================="
