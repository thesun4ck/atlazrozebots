#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atlas Rose Bot - Telegram бот для магазина букетов
"""

import logging
from telegram.ext import Application
from config import BOT_TOKEN
from handlers import client, admin

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Запуск бота"""
    logger.info("🌹 Запуск Atlas Rose Bot...")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики клиента
    client.register_handlers(application)
    
    # Регистрируем обработчики админа
    admin.register_handlers(application)
    
    # Запускаем бота
    logger.info("✅ Бот запущен и готов к работе!")
    application.run_polling(
        allowed_updates=["message", "callback_query", "inline_query"],
        drop_pending_updates=True
    )

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
