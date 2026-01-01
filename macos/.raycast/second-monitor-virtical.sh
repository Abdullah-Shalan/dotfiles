#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Setup Vertical Monitor
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 🖥️

# Documentation:
# @raycast.description Automatically opens and aligns (Teams and Outlook)  on second monitor
# @raycast.author Abdullah

open -a Microsoft\ Outlook
sleep 1
open -g raycast://extensions/raycast/window-management/top-half

open -a Microsoft\ Teams
sleep 1
open -g raycast://extensions/raycast/window-management/bottom-half

echo "Activated secondary workspace"

