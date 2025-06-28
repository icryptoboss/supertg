import os
import threading
from app import app  # Flask app instance
from main import run_bot  # function that starts your Pyrogram bot

def start_flask():
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

def start_bot():
    run_bot()  # This must call app.run() from Pyrogram inside main.py

if __name__ == "__main__":
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    start_bot()  # Telegram bot runs in main thread (more stable)
