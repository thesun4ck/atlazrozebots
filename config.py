import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1063802362  # Основной админ
ADMIN_ID_2 = 1477864632  # Второй админ
ADMIN_IDS = [1063802362, 1477864632]  # Список всех админов
CONTACT_USERNAME = "aliswesh"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден!")
