#!/bin/bash
cd /home/chapter_3_kgf/supertg

# Save current HEAD
current_commit=$(git rev-parse HEAD)

# Stash vars.py and pull latest code
git stash push vars.py
git pull
git stash pop

# Get new HEAD
new_commit=$(git rev-parse HEAD)

# Restart only if commit changed
if [ "$current_commit" != "$new_commit" ]; then
  echo "🔁 New update detected. Restarting bot..."
  sudo systemctl restart tgbot
else
  echo "✅ No update found. Bot not restarted."
fi
