#🇳‌🇮‌🇰‌🇭‌🇮‌🇱‌
# Add your details here and then deploy by clicking on HEROKU Deploy button
import os
from os import environ

API_ID = int(environ.get("API_ID", "20842776"))
API_HASH = environ.get("API_HASH", "a5f3a00d014cccf4b1446e9e1a479270")
BOT_TOKEN = environ.get("BOT_TOKEN", "1631815313:AAEWsWX6cY_gSo5TUzHsFxqVlYhs3_hEtdU")
OWNER = int(environ.get("OWNER", "1391520393"))
CREDIT = "RAHUL PATEL"
AUTH_USER = os.environ.get('AUTH_USERS', '1391520393').split(',')
AUTH_USERS = [int(user_id) for user_id in AUTH_USER]
if int(OWNER) not in AUTH_USERS:
    AUTH_USERS.append(int(OWNER))
  
#WEBHOOK = True  # Don't change this
#PORT = int(os.environ.get("PORT", 8080))  # Default to 8000 if not set
