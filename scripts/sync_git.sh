#!/bin/bash
# Sync local repo with remote
# Usage: ./scripts/sync_git.sh [commit_message]

# Ensure we are in the project root
cd "$(dirname "$0")/.."

echo "Starting sync for branch..."
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

echo "Fetching updates..."
git fetch origin

echo "Pulling latest changes (rebase)..."
git pull origin "$CURRENT_BRANCH" --rebase

if [ -n "$1" ]; then
    echo "Adding all changes..."
    git add .
    
    echo "Committing with message: $1"
    git commit -m "$1"
    
    echo "Pushing changes..."
    git push origin "$CURRENT_BRANCH"
else
    echo "No commit message provided. Only pulled changes."
    echo "To commit and push, run: ./scripts/sync_git.sh \"Your commit message\""
fi

echo "Sync complete."
