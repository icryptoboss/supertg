#!/bin/bash

cd /home/chapter_3_kgf/supertg || exit

# Fetch and compare Git versions
git fetch origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

# If new commits found
if [ "$LOCAL" != "$REMOTE" ]; then
    echo "🔁 Update found, pulling and restarting bot..."
    git pull origin main
    sudo systemctl restart tgbot.service
else
    echo "✅ No update. Bot is current."
fi
