#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Import to rulebook
# @raycast.mode fullOutput

# Optional parameters:
# @raycast.icon 📠
# @raycast.argument1 { "type": "text", "placeholder": "Kibana rule URL", "optional": false }
# @raycast.argument2 { "type": "text", "placeholder": "Branch name", "optional": false }
# @raycast.argument3 { "type": "text", "placeholder": "Rule name", "optional": false }


# Documentation:
# @raycast.author Abdullah
# @raycast.description Import a Kibana rule to the rulebook repository.

PYTHON_IMPORTER="$(dirname "$0")/import_kibana_rule_to_rulebook.py"

# Prefer local venv from rulebook-deployer if available
VENV_PY="/Users/abdullah/work/cipher/rulebook-deployer/.venv/bin/python"
if [[ -x "${VENV_PY}" ]]; then
  PYTHON_BIN="${VENV_PY}"
else
  PYTHON_BIN="python3"
fi

if [[ ! -f "${PYTHON_IMPORTER}" ]]; then
  echo "Importer script not found at ${PYTHON_IMPORTER}"
  exit 1
fi

echo "Importing Kibana rule to rulebook..."
echo "Kibana rule URL: ${1}"
echo "Branch name: ${2}"
echo "Rule name: ${3}"
"${PYTHON_BIN}" "${PYTHON_IMPORTER}" "${1}" "${2}" "${3}"
echo "Import complete"

