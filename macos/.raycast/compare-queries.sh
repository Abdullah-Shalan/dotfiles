#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Compare Queries
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 🤖
# @raycast.argument1 { "type": "text", "placeholder": "Query file 1", "optional": false }
# @raycast.argument2 { "type": "text", "placeholder": "Query file 2", "optional": false }

# Documentation:
# @raycast.author Abdullah
# @raycast.description Compare two query files or TOML/YAML configs (extracts query from configs). Same canonical form = same version.

SCRIPT_DIR="${0%/*}"
PY_SCRIPT="$SCRIPT_DIR/compare-queries-extract.py"

# Prefer .venv in this directory (create with: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt)
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python3"
if [ -x "$VENV_PYTHON" ]; then
  PYTHON="$VENV_PYTHON"
else
  PYTHON="python3"
fi

if [ ! -f "$PY_SCRIPT" ]; then
  echo "Error: Python script not found: $PY_SCRIPT" >&2
  exit 2
fi

"$PYTHON" "$PY_SCRIPT" "$1" "$2"
