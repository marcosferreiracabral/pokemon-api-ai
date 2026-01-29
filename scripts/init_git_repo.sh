#!/bin/bash

# Script de Inicialização e Correção do Git
# Autor: Tech Marcos Ferreira Cabral
# Descrição: Inicializa a estrutura de repositório aninhado e inicializa git na raiz.

REPO_URL="Altere para seu link do GitHub"

print_msg() {
    echo -e "\033[1;32m>> $1\033[0m"
}

print_error() {
    echo -e "\033[1;31m!! $1\033[0m"
}

# 1. Limpeza de diretório aninhado acidental
if [ -d "pokemon-api-ai" ]; then
    print_msg "Detectado diretório aninhado 'pokemon-api-ai'. Removendo para evitar duplicidade..."
    rm -rf pokemon-api-ai
fi

# 2. Inicializar Git na raiz
if [ -d ".git" ]; then
    print_msg "Repositório Git já inicializado."
else
    print_msg "Inicializando repositório Git..."
    git init -b main
fi

# 3. Configurar Remote
CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null)
if [ "$CURRENT_REMOTE" != "$REPO_URL" ]; then
    if [ -n "$CURRENT_REMOTE" ]; then
        print_msg "Remote 'origin' incorreto. Atualizando..."
        git remote set-url origin "$REPO_URL"
    else
        print_msg "Adicionando remote 'origin'..."
        git remote add origin "$REPO_URL"
    fi
else
    print_msg "Remote configurado corretamente."
fi

# 4. Criar .gitignore padrão se não existir
if [ ! -f ".gitignore" ]; then
    print_msg "Criando .gitignore..."
    echo "venv/" > .gitignore
    echo "__pycache__/" >> .gitignore
    echo ".env" >> .gitignore
    echo ".DS_Store" >> .gitignore
fi

# 5. Adicionar e Commit
print_msg "Preparando commit inicial..."
git add .
git commit -m "chore: Project initialization and structure fix" || print_msg "Nada para commitar."

# 6. Push (com cuidado)
print_msg "Tentando enviar para o remote..."
git push -u origin main --force || print_error "Falha no push. Verifique suas credenciais ou permissões."

print_msg "Setup do Git finalizado!"
