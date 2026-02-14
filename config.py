import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID админа
ADMIN_ID = 1063802362

# Username для связи
CONTACT_USERNAME = "thesun4ck"

# Валидация
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в переменных окружения! Создайте файл .env")
