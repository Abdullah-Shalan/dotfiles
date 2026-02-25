#!/bin/bash

# Only run when explicitly invoked with --confirm (e.g. from SwiftBar menu click).
# Stops accidental runs when script is executed without the flag (e.g. at login).
[[ " $* " = *" --confirm "* ]] || exit 0

# Confirmation Dialog
osascript -e 'display dialog "Discard all local changes?" with icon caution buttons {"Cancel", "Confirm"} default button "Cancel"' || exit 0

# If OK was pressed, run the restore
/usr/bin/git -C "/Users/abdullah/Documents/Obsidian-Vault" restore .
