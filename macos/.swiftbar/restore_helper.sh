#!/bin/bash
# Confirmation Dialog
osascript -e 'display dialog "Discard all local changes?" with icon caution buttons {"Cancel", "Confirm"} default button "Cancel"' || exit 0

# If OK was pressed, run the restore
/usr/bin/git -C "/Users/abdullah/Documents/Obsidian-Vault" restore .
