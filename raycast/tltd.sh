#!/bin/bash

# @raycast.schemaVersion 1
# @raycast.title tltd
# @raycast.mode silent
# @raycast.packageName TLTD

osascript -e 'tell application "Terminal"
    do script "~/.local/bin/tltd"
    activate
end tell'
