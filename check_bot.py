#!/usr/bin/env python3
"""
Скрипт для проверки конфигурации бота
"""

print("🔍 Проверка конфигурации бота...\n")

# 1. Проверка Python версии
import sys
print(f"✓ Python версия: {sys.version}")

# 2. Проверка библиотек
try:
    import telegram
    print(f"✓ python-telegram-bot версия: {telegram.__version__}")
except ImportError as e:
    print(f"❌ Ошибка импорта telegram: {e}")
    print("   Установите: pip install python-telegram-bot==21.0.1")

try:
    import yaml
    print(f"✓ pyyaml установлен")
except ImportError:
    print(f"❌ pyyaml не установлен")
    print("   Установите: pip install pyyaml")

try:
    from dotenv import load_dotenv
    print(f"✓ python-dotenv установлен")
except ImportError:
    print(f"❌ python-dotenv не установлен")

# 3. Проверка .env файла
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN and BOT_TOKEN != "your_bot_token_here":
    print(f"✓ BOT_TOKEN найден: {BOT_TOKEN[:10]}...")
else:
    print(f"❌ BOT_TOKEN не найден или не настроен в .env")
    print(f"   Текущее значение: {BOT_TOKEN}")

# 4. Проверка структуры файлов
print("\n📁 Проверка файлов:")

files = [
    "bot.py",
    "config.py",
    "requirements.txt",
    "Procfile",
    "runtime.txt",
    "handlers/client.py",
    "handlers/admin.py",
    "database/db.py",
    "data/bouquets.yaml",
    "data/admins.yaml"
]

for file in files:
    if os.path.exists(file):
        print(f"  ✓ {file}")
    else:
        print(f"  ❌ {file} - НЕ НАЙДЕН!")

# 5. Проверка данных
print("\n📊 Проверка данных:")

try:
    with open("data/bouquets.yaml", 'r', encoding='utf-8') as f:
        import yaml
        data = yaml.safe_load(f)
        bouquets = data.get('bouquets', [])
        print(f"  ✓ Букетов в базе: {len(bouquets)}")
        for b in bouquets[:3]:
            print(f"    - {b['name']}")
except Exception as e:
    print(f"  ❌ Ошибка чтения bouquets.yaml: {e}")

try:
    with open("data/admins.yaml", 'r', encoding='utf-8') as f:
        import yaml
        data = yaml.safe_load(f)
        admins = data.get('admins', [])
        print(f"  ✓ Админов: {len(admins)}")
        print(f"    ID: {admins}")
except Exception as e:
    print(f"  ❌ Ошибка чтения admins.yaml: {e}")

print("\n" + "="*50)
print("Проверка завершена!")
print("="*50)
