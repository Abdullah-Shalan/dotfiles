#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Coffee-Net
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 🖥️

# Documentation:
# @raycast.description Connect to Coffee-Net
# @raycast.author Abdulmalik

# Replace these variables with your network details
SSID="Coffee-Net"
PASSWORD="L@\$tAqu!r3T!m3"
INTERFACE="en0"  # usually 'en0' on Mac, check with `networksetup -listallhardwareports`

# Turn Wi-Fi off and on again to reset
networksetup -setairportpower "$INTERFACE" off
sleep 2
networksetup -setairportpower "$INTERFACE" on
sleep 2

# Attempt to join the hidden Wi-Fi network
networksetup -setairportnetwork "$INTERFACE" "$SSID" "$PASSWORD"
sleep 2

# Double-check internet connection with retries
MAX_RETRIES=5
RETRY_DELAY=2
SUCCESS=0
for ((i=1; i<=MAX_RETRIES; i++)); do
    if /usr/bin/curl -s --head --max-time 5 https://www.google.com | /usr/bin/grep "HTTP/2 200" > /dev/null; then
        echo "✅ Internet connection is active"
        SUCCESS=1
        break
    else
        echo "Attempt $i: No internet connection yet. Retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
    fi

done

if [ $SUCCESS -eq 0 ]; then
    echo "❌ No internet connection after $MAX_RETRIES attempts."
fi



