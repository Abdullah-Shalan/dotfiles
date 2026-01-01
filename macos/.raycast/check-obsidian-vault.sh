#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Check Vault Status
# @raycast.mode inline

# Optional parameters:
# @raycast.icon 📈

# Documentation:
# @raycast.description Tell it the Obsidian Vault has any unsaved changes.
# @raycast.author Abdullah

cd "${VAULT:-$HOME/Documents/Obsidian-Vault}"

if [ -n "$(git status --porcelain)" ]; then
    printf "🚧 \e[33mHas Unsaved Changes 🚧"
    exit 0
fi

printf "\e[0;32mUp To Date\e[0m\n"
