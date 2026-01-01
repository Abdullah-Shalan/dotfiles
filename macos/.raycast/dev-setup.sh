#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Setup Development Environment
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 🖥️

# Documentation:
# @raycast.description Automatically aligns both Vscode and Terminal
# @raycast.author Abdullah

open -a Visual\ Studio\ Code
sleep 1
open -g raycast://extensions/raycast/window-management/first-two-thirds

open -a Terminal
sleep 1
open -g raycast://extensions/raycast/window-management/last-third

echo "Activated dev workspace"