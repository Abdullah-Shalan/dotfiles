#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title New Tune
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 🔧
# @raycast.argument1 { "type": "text", "placeholder": "Elastic Rule URL" }
# @raycast.argument2 { "type": "text", "placeholder": "Rule Name" }

# Documentation:
# @raycast.author Abdullah
# @raycast.description Create a ClickUp subtask for fine-tuning requests from an Elastic rule URL

SCRIPT_PATH="$HOME/work/cipher/docs-worker"
cd "$SCRIPT_PATH" || exit 1

# Activate virtual environment if it exists
if [ -f "$SCRIPT_PATH/.venv/bin/activate" ]; then
    source "$SCRIPT_PATH/.venv/bin/activate"
fi

# Run the Python script with arguments
python scripts/new_tune.py "$1" "$2"

