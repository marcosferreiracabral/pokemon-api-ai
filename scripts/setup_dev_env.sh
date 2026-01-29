#!/bin/bash

# Script de Setup para Git Bash (Windows)
# Autor: Marcos Ferreira Cabral
# Descrição: Clona o repositório e configura o ambiente de desenvolvimento.

# Configuração
REPO_URL="https://github.com/marcosferreiracabral/pokemon-api-ai.git"
TARGET_DIR="pokemon-api-ai"

# Função para mensagens coloridas
print_msg() {
    echo -e "\033[1;32m>> $1\033[0m"
}

print_error() {
    echo -e "\033[1;31m!! $1\033[0m"
}

# Verifica se estamos rodando no Git Bash
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "cygwin" ]]; then
    print_error "Este script foi projetado para rodar no Git Bash (Windows)."
fi

# 1. Clonar ou Atualizar Repositório
if [ -d "$TARGET_DIR" ]; then
    print_msg "Diretório '$TARGET_DIR' já existe."
    print_msg "Atualizando arquivos do projeto (git pull)..."
    cd "$TARGET_DIR" || exit
    git pull origin main || print_error "Falha ao atualizar. Verifique conflitos."
else
    print_msg "Clonando repositório de $REPO_URL..."
    git clone "$REPO_URL" || { print_error "Falha ao clonar repositório"; exit 1; }
    cd "$TARGET_DIR" || exit
fi

# 2. Configurar Ambiente Virtual
print_msg "Configurando ambiente virtual Python..."
if [ ! -d "venv" ]; then
    python -m venv venv
    print_msg "Ambiente virtual criado."
else
    print_msg "Ambiente virtual já existente encontrado."
fi

# 3. Ativar Ambiente Virtual
# No Windows/Git Bash, o script geralmente está em venv/Scripts/activate
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    print_error "Não foi possível encontrar o script de ativação do venv."
    print_error "Certifique-se de que o python está instalado corretamente."
    exit 1
fi

# 4. Instalar Dependências
if [ -f "requirements.txt" ]; then
    print_msg "Instalando dependências (requirements.txt)..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    print_msg "Arquivo requirements.txt não encontrado."
fi

# 5. Configurar .env
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_msg "Criando arquivo .env a partir de .env.example..."
        cp .env.example .env
    else
        print_msg "Aviso: .env.example não encontrado."
    fi
else
    print_msg "Arquivo .env já existe."
fi

print_msg "Setup concluído com sucesso!"
print_msg "Para começar, digite: source venv/Scripts/activate"
