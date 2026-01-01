#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Setup Horizontal Monitor
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 🖥️

# Documentation:
# @raycast.description Automatically opens and aligns (Teams and Outlook)  on second monitor
# @raycast.author Abdullah

open -a Microsoft\ Outlook
sleep 1
open -g raycast://extensions/raycast/window-management/first-two-thirds

open -a Microsoft\ Teams
sleep 1
open -g raycast://extensions/raycast/window-management/last-third

echo "Activated secondary workspace"