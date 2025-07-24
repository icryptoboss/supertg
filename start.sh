#!/bin/bash

# Set working directory
cd /home/chapter_3_kgf/supertg

# Activate virtual environment (if you use one)
# source venv/bin/activate  # Uncomment if you use a virtualenv

# Pull latest repo updates (optional but useful)
echo "🔄 Updating from GitHub..."
git pull origin main

# Start backend Flask app via gunicorn
echo "🚀 Starting Flask backend..."
gunicorn app:app --daemon

# Start the Telegram bot
echo "🤖 Starting Telegram bot..."
python3 main.py
