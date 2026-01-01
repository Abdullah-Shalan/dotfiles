#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Update Obsidian Vault
# @raycast.mode compact
# @raycast.argument1 { "type": "text", "placeholder": "Commit Message", "optional": false }

# Optional parameters:
# @raycast.icon 🖥️

# Documentation:
# @raycast.description Commits and pushes new changes in Obsidian Vault to Github
# @raycast.author Abdullah

msg="$1"

echo "Update script starting!"
cd '/Users/abdullah/Documents/Obsidian-Vault' || { echo "Directory not found"; exit 1; }

git add --all
if git diff --cached --quiet; then
  printf "No changes detected. Vault is up to date"
  exit 0
fi

printf "\e[36mChanges Made:\e[0m"
git status -s

git commit -m "$msg"

git push
printf "Vault Updated Successfully"

