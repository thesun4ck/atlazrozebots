import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1063802362
CONTACT_USERNAME = "thesun4ck"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден!")
