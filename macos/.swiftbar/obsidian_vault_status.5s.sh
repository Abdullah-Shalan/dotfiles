#!/bin/bash

VAULT_PATH="${VAULT:-/Users/abdullah/Documents/Obsidian-Vault}"
DIR_NAME=$(dirname "$0")

cd "$VAULT_PATH"

if [ -n "$(git status --porcelain)" ]; then
    echo " | sfimage=pencil.line"
    echo "---" # Separator: head above - body below
    echo "Vault Has Changes | color=yellow"    
else 
    echo " | sfimage=checkmark.shield.fill"
    echo "---"
    echo "Vault up to date | color=green"

fi

echo "---"
echo "Open Obsidian | bash='open' param1='-a' param2='Obsidian' terminal=false"
echo "Open This Script | bash='code' param1='$DIR_NAME' terminal=false"
echo "Refresh | refresh=True"
echo "---"
echo "Remove changes | shell=/Users/abdullah/.swiftbar/restore_helper.sh terminal=false"