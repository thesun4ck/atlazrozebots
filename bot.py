#!/usr/bin/env python3
import logging
from telegram.ext import Application
from config import BOT_TOKEN
from handlers import client, admin

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    logger.info("🌹 Запуск бота...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    client.register_handlers(application)
    admin.register_handlers(application)
    
    logger.info("✅ Бот запущен!")
    application.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True
    )

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        raise
