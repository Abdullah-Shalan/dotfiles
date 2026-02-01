#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title New Deploy
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 🚀
# @raycast.argument1 { "type": "text", "placeholder": "GitLab MR URL" }

# Documentation:
# @raycast.author Abdullah
# @raycast.description Create a ClickUp subtask for deployment from a GitLab merge request URL

SCRIPT_PATH="$HOME/work/cipher/docs-worker"
cd "$SCRIPT_PATH" || exit 1

# Activate virtual environment if it exists
if [ -f "$SCRIPT_PATH/.venv/bin/activate" ]; then
    source "$SCRIPT_PATH/.venv/bin/activate"
fi

# Run the Python script with arguments
python scripts/new_deploy.py "$1"
