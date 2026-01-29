#!/bin/bash
set -e

# ===============================
# CONFIGURAÇÕES
# ===============================
REPO_URL="https://github.com/marcosferreiracabral/pokemon-api-ai.git"
BRANCH_NAME="sync-local-project"

# Identifica diretórios dinamicamente
# PROJECT_ROOT assume que este script está em ./scripts/sync_repo.sh
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Define diretório temporário fixo mas seguro (fora do project root para evitar recursão do tar)
# Usamos '../temp_sync_build' para garantir que criamos ao lado da pasta do projeto
TEMP_DIR="${PROJECT_ROOT}/../temp_sync_build_$(date +%s)"

echo "🚀 Iniciando sincronização do projeto..."
echo "📂 Origem (Local): $PROJECT_ROOT"
echo "📂 Temp Dir: $TEMP_DIR"
echo "📂 Destino (Branch): $BRANCH_NAME"

# ===============================
# PREPARAÇÃO (Workspace Limpo)
# ===============================
# Garante limpeza ao sair (trap para sempre remover o temp, sucesso ou falha)
cleanup() {
    echo "🧹 Limpando arquivos temporários..."
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

if [ -d "$TEMP_DIR" ]; then
  rm -rf "$TEMP_DIR"
fi
mkdir -p "$TEMP_DIR"

# ===============================
# CÓPIA DO PROJETO
# ===============================
echo "📂 Copiando arquivos..."

# Usamos tar para copiar preservando permissões e excluindo arquivos indesejados
# Excluímos explicitamente pastas de ambiente e git
EXCLUDES="--exclude='./.git' --exclude='./.venv' --exclude='./venv' --exclude='./__pycache__' --exclude='*.pyc' --exclude='./.idea' --exclude='./.vscode' --exclude='./*.log'"

# Executa tar. O pipe envia os arquivos de PROJECT_ROOT para TEMP_DIR
# O uso de '.' no tar refere-se ao diretório atual (PROJECT_ROOT)
cd "$PROJECT_ROOT"
tar $EXCLUDES -cf - . | (cd "$TEMP_DIR" && tar xf -)

# ===============================
# GIT INIT & PUSH (Snapshot)
# ===============================
cd "$TEMP_DIR"

echo "🔥 Inicializando repositório temporário para snapshot..."
git init
git checkout -b "$BRANCH_NAME"
git add .
git commit -m "chore: sincroniza estado local completo (snapshot)"

echo "🔗 Conectando ao remoto..."
git remote add origin "$REPO_URL"

echo "🚀 Enviando atualizações (Force Push)..."
# Force push é necessário pois estamos recriando o histórico da branch de sync a cada envio
git push -u origin "$BRANCH_NAME" --force

# ===============================
# PÓS-PROCESSAMENTO
# ===============================
echo ""
echo "✅ Finalizado com sucesso!"
echo "🔗 Pull Request Link: https://github.com/marcosferreiracabral/pokemon-api-ai/compare/$BRANCH_NAME?expand=1"

# Executa o script de instalação se solicitado
# Voltamos ao diretório original para executar scripts
cd "$PROJECT_ROOT"
if [ -f "scripts/install_project.sh" ]; then
    echo "🔄 Executando script de instalação e validação..."
    bash scripts/install_project.sh
fi

# A função cleanup será chamada automaticamente pelo trap EXIT
