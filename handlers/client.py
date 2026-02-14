from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from database import db
from config import CONTACT_USERNAME, ADMIN_ID
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# States
(CHOOSING_QUANTITY, CHOOSING_PACKAGING, CHOOSING_EXTRAS, 
 CARD_TEXT, CHOOSING_DATE, CHOOSING_TIME, CHOOSING_PICKUP, ENTERING_ADDRESS) = range(8)

def get_main_menu():
    """Главное меню"""
    keyboard = [
        ["🌹 Каталог", "🛒 Корзина"],
        ["⭐️ Избранное", "📦 Мои заказы"],
        ["💬 Связаться со мной"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    db.save_user(user.id, user.username, user.first_name, user.last_name or "")
    
    await update.message.reply_text(
        "🌹 *Добро пожаловать в Flower Shop!*\n\n"
        "Мы создаем уникальные букеты из атласных роз ручной работы.\n"
        "Каждый букет - это произведение искусства!\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )

async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать каталог"""
    bouquets = db.get_bouquets()
    
    if not bouquets:
        await update.message.reply_text(
            f"На данный момент каталог пуст, но можете написать и уточнить информацию @{CONTACT_USERNAME}"
        )
        return
    
    favorites = db.get_favorites(update.effective_user.id)
    
    for bouquet in bouquets:
        is_fav = bouquet['id'] in favorites
        # БЕЗ описания, только название и цена
        caption = (
            f"{'🔥 ' if bouquet.get('is_popular') else ''}"
            f"*{bouquet['name']}*\n\n"
            f"💰 Цена от: *{bouquet['base_price']}₽*"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🛒 Заказать", callback_data=f"order:{bouquet['id']}"),
                InlineKeyboardButton("❤️" if is_fav else "♡", callback_data=f"fav:{bouquet['id']}")
            ]
        ]
        
        try:
            with open(bouquet['image_path'], 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Photo error: {e}")

async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать заказ"""
    query = update.callback_query
    await query.answer()
    
    bouquet_id = query.data.split(":")[1]
    bouquet = db.get_bouquet_by_id(bouquet_id)
    
    if not bouquet:
        await query.message.reply_text("Букет не найден")
        return ConversationHandler.END
    
    context.user_data['bouquet'] = bouquet
    context.user_data['order'] = {}
    
    # Сразу количество (БЕЗ цвета)
    keyboard = []
    for qty in bouquet.get('quantities', []):
        val = qty['value']
        mult = qty['multiplier']
        price = int(bouquet['base_price'] * mult)
        keyboard.append([InlineKeyboardButton(
            f"{val} роз - {price}₽",
            callback_data=f"qty:{val}:{price}"
        )])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
    
    await query.message.reply_text(
        f"*{bouquet['name']}*\n\nВыберите количество роз:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return CHOOSING_QUANTITY

async def choose_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор количества"""
    query = update.callback_query
    await query.answer()
    
    _, qty, price = query.data.split(":")
    context.user_data['order']['quantity'] = int(qty)
    context.user_data['order']['base_price'] = int(price)
    
    bouquet = context.user_data['bouquet']
    
    # Упаковка
    keyboard = []
    for pkg in bouquet.get('packaging', []):
        label = pkg['name']
        if pkg['price'] > 0:
            label += f" (+{pkg['price']}₽)"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"pkg:{pkg['type']}:{pkg['price']}")])
    
    await query.message.edit_text(
        "Выберите упаковку:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CHOOSING_PACKAGING

async def choose_packaging(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор упаковки"""
    query = update.callback_query
    await query.answer()
    
    _, pkg_type, pkg_price = query.data.split(":")
    context.user_data['order']['packaging'] = {'type': pkg_type, 'price': int(pkg_price)}
    
    # Дополнительные услуги
    keyboard = [
        [InlineKeyboardButton("⚡️ Срочно за 1 день (+1000₽)", callback_data="extra:urgent")],
        [InlineKeyboardButton("💌 Открытка (+100₽)", callback_data="extra:card")],
        [InlineKeyboardButton("✅ Продолжить", callback_data="extra:none")]
    ]
    
    await query.message.edit_text(
        "Дополнительные услуги:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CHOOSING_EXTRAS

async def choose_extras(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор дополнительных услуг"""
    query = update.callback_query
    await query.answer()
    
    extra_type = query.data.split(":")[1]
    
    if 'extras' not in context.user_data['order']:
        context.user_data['order']['extras'] = {}
    
    if extra_type == "urgent":
        context.user_data['order']['extras']['urgent'] = True
        await query.answer("Срочный заказ добавлен")
        return CHOOSING_EXTRAS
    elif extra_type == "card":
        await query.message.reply_text("Введите текст для открытки (до 200 символов):")
        return CARD_TEXT
    else:
        # Переходим к дате
        return await show_date_selection(query, context)

async def card_text_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Текст открытки"""
    text = update.message.text[:200]
    context.user_data['order']['extras']['card_text'] = text
    
    # Создаём fake query для show_date_selection
    class FakeQuery:
        def __init__(self, msg):
            self.message = msg
        async def answer(self): pass
        async def edit_text(self, *args, **kwargs):
            return await self.message.reply_text(*args, **kwargs)
    
    fake_query = FakeQuery(update.message)
    return await show_date_selection(fake_query, context)

async def show_date_selection(query, context):
    """Показать выбор даты"""
    quantity = context.user_data['order']['quantity']
    today = datetime.now()
    
    # Если > 51 - минимум +4 дня, иначе +2
    start_day = 4 if quantity > 51 else 2
    
    keyboard = []
    for i in range(start_day, start_day + 7):
        date = today + timedelta(days=i)
        keyboard.append([InlineKeyboardButton(
            date.strftime("%d.%m"),
            callback_data=f"date:{date.strftime('%Y-%m-%d')}"
        )])
    
    await query.message.reply_text(
        "На какую дату нужен букет?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CHOOSING_DATE

async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор даты"""
    query = update.callback_query
    await query.answer()
    
    date = query.data.split(":")[1]
    context.user_data['order']['date'] = date
    
    # Время (с 12:00)
    keyboard = [
        [InlineKeyboardButton("12:00", callback_data="time:12:00"), 
         InlineKeyboardButton("14:00", callback_data="time:14:00")],
        [InlineKeyboardButton("16:00", callback_data="time:16:00"), 
         InlineKeyboardButton("18:00", callback_data="time:18:00")],
        [InlineKeyboardButton("20:00", callback_data="time:20:00")]
    ]
    
    await query.message.edit_text(
        "К какому времени?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CHOOSING_TIME

async def choose_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор времени"""
    query = update.callback_query
    await query.answer()
    
    time = query.data.split(":")[1] + ":" + query.data.split(":")[2]
    context.user_data['order']['time'] = time
    
    # Способ получения
    keyboard = [
        [InlineKeyboardButton("🏠 Самовывоз", callback_data="pickup:self")],
        [InlineKeyboardButton("📍 Встреча в городе", callback_data="pickup:meeting")]
    ]
    
    await query.message.edit_text(
        "Как будете получать?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CHOOSING_PICKUP

async def choose_pickup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор способа получения"""
    query = update.callback_query
    await query.answer()
    
    method = query.data.split(":")[1]
    context.user_data['order']['pickup'] = method
    
    if method == "meeting":
        await query.message.reply_text("Введите адрес встречи:")
        return ENTERING_ADDRESS
    else:
        context.user_data['order']['address'] = "Самовывоз"
        return await show_summary(update, context)

async def enter_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ввод адреса"""
    context.user_data['order']['address'] = update.message.text
    return await show_summary(update, context)

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать итог"""
    bouquet = context.user_data['bouquet']
    order = context.user_data['order']
    
    # Расчет цены
    total = order['base_price'] + order['packaging']['price']
    
    extras_text = ""
    if order.get('extras', {}).get('urgent'):
        total += 1000
        extras_text += "⚡️ Срочный заказ: Да\n"
    
    if order.get('extras', {}).get('card_text'):
        total += 100
        extras_text += f"💌 Открытка: {order['extras']['card_text']}\n"
    
    order['total_price'] = total
    
    summary = (
        f"*📋 Ваш заказ:*\n\n"
        f"🌹 {bouquet['name']}\n"
        f"🔢 Количество: {order['quantity']} роз\n"
        f"📦 Упаковка: {order['packaging']['type']}\n"
        f"{extras_text}"
        f"📅 Дата: {order['date']}\n"
        f"⏰ Время: {order['time']}\n"
        f"📍 Получение: {order['pickup']} - {order['address']}\n\n"
        f"💰 *Итого: {total}₽*"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Добавить в корзину", callback_data="confirm_cart")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            summary,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            summary,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    return ConversationHandler.END

async def confirm_add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить в корзину"""
    query = update.callback_query
    await query.answer("Добавлено!")
    
    bouquet = context.user_data['bouquet']
    order = context.user_data['order']
    
    item = {
        'bouquet_id': bouquet['id'],
        'bouquet_name': bouquet['name'],
        'quantity': order['quantity'],
        'packaging': order['packaging'],
        'extras': order.get('extras', {}),
        'date': order['date'],
        'time': order['time'],
        'pickup': order['pickup'],
        'address': order['address'],
        'total_price': order['total_price']
    }
    
    db.add_to_cart(update.effective_user.id, item)
    await query.message.edit_text("✅ Товар добавлен в корзину!")
    context.user_data.clear()

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Корзина"""
    cart = db.get_user_cart(update.effective_user.id)
    
    if not cart:
        await update.message.reply_text("Корзина пуста")
        return
    
    total = 0
    for i, item in enumerate(cart):
        total += item['total_price']
        
        extras = []
        if item.get('extras', {}).get('urgent'):
            extras.append("⚡️ Срочно")
        if item.get('extras', {}).get('card_text'):
            extras.append("💌 Открытка")
        
        extras_text = " • " + " • ".join(extras) if extras else ""
        
        text = (
            f"🌹 *{item['bouquet_name']}*\n"
            f"🔢 {item['quantity']} роз{extras_text}\n"
            f"📅 {item['date']} {item['time']}\n"
            f"📍 {item['pickup']}: {item['address']}\n"
            f"💰 {item['total_price']}₽"
        )
        
        keyboard = [[InlineKeyboardButton("🗑 Удалить", callback_data=f"remove:{i}")]]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить", callback_data="checkout")],
        [InlineKeyboardButton("💬 Связаться", url=f"https://t.me/{CONTACT_USERNAME}")],
        [InlineKeyboardButton("🗑 Очистить", callback_data="clear_cart")]
    ]
    
    await update.message.reply_text(
        f"*💰 Итого: {total}₽*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def remove_from_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить из корзины"""
    query = update.callback_query
    await query.answer("Удалено")
    
    index = int(query.data.split(":")[1])
    db.remove_from_cart(update.effective_user.id, index)
    await query.message.edit_text("🗑 Товар удален")

async def clear_cart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очистить корзину"""
    query = update.callback_query
    await query.answer()
    
    db.clear_cart(update.effective_user.id)
    await query.message.edit_text("🗑 Корзина очищена")

async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оплата"""
    query = update.callback_query
    await query.answer()
    
    cart = db.get_user_cart(update.effective_user.id)
    total = sum(item['total_price'] for item in cart)
    
    keyboard = [
        [InlineKeyboardButton("✅ Я оплатил", callback_data="payment_confirm")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    
    await query.message.edit_text(
        f"*💳 Оплата заказа*\n\n"
        f"Сумма: *{total}₽*\n\n"
        f"Реквизиты:\n"
        f"💳 Карта: `2200 7007 1234 5678`\n"
        f"👤 Flower Shop\n\n"
        f"После оплаты нажмите кнопку:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def payment_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение оплаты"""
    query = update.callback_query
    
    user = update.effective_user
    cart = db.get_user_cart(user.id)
    
    # Показываем "Ожидание оплаты"
    await query.message.edit_text(
        "⏳ *Ожидание подтверждения оплаты...*\n\n"
        "Ваш заказ отправлен менеджеру.",
        parse_mode='Markdown'
    )
    
    # Сохраняем заказ
    order_id = db.create_order(user.id, user.full_name, cart)
    
    # Формируем сообщение для админа
    items_text = "\n".join([
        f"🌹 {item['bouquet_name']} ({item['quantity']} шт) - {item['total_price']}₽"
        for item in cart
    ])
    
    total = sum(item['total_price'] for item in cart)
    username_tag = f"@thesun4ck" if user.username else user.full_name
    
    admin_msg = (
        f"🔔 *Новый заказ!*\n\n"
        f"Заказ #{order_id}\n"
        f"От: {username_tag}\n\n"
        f"{items_text}\n\n"
        f"💰 *Итого: {total}₽*\n\n"
        f"Пришло ли поступление?"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, оплачено", callback_data=f"admin_confirm:{order_id}:{user.id}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"admin_reject:{order_id}:{user.id}")
        ]
    ]
    
    # Отправляем админу
    try:
        await context.bot.send_message(
            ADMIN_ID,
            admin_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

async def admin_confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ подтверждает оплату"""
    query = update.callback_query
    await query.answer("Подтверждено")
    
    _, order_id, user_id = query.data.split(":")
    user_id = int(user_id)
    
    # Очищаем корзину
    db.clear_cart(user_id)
    
    # Уведомляем пользователя
    try:
        await context.bot.send_message(
            user_id,
            f"✅ *Заказ #{order_id} подтвержден!*\n\n"
            f"Оплата получена. Мы приступили к изготовлению вашего букета!",
            parse_mode='Markdown'
        )
    except:
        pass
    
    await query.message.edit_text(
        f"✅ Заказ #{order_id} подтвержден\nПользователь уведомлен"
    )

async def admin_reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ отклоняет оплату"""
    query = update.callback_query
    await query.answer("Отклонено")
    
    _, order_id, user_id = query.data.split(":")
    user_id = int(user_id)
    
    # Уведомляем пользователя
    try:
        await context.bot.send_message(
            user_id,
            f"❌ *Оплата не подтверждена*\n\n"
            f"Заказ #{order_id}\n"
            f"Оплата не поступила. Проверьте реквизиты и попробуйте снова.",
            parse_mode='Markdown'
        )
    except:
        pass
    
    await query.message.edit_text(
        f"❌ Заказ #{order_id} отклонен\nПользователь уведомлен"
    )

async def toggle_fav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Избранное"""
    query = update.callback_query
    
    bouquet_id = query.data.split(":")[1]
    db.toggle_favorite(update.effective_user.id, bouquet_id)
    
    favorites = db.get_favorites(update.effective_user.id)
    is_fav = bouquet_id in favorites
    
    await query.answer("❤️ Добавлено" if is_fav else "Удалено")

async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать избранное"""
    favorites = db.get_favorites(update.effective_user.id)
    
    if not favorites:
        await update.message.reply_text("Избранное пусто")
        return
    
    for bid in favorites:
        bouquet = db.get_bouquet_by_id(bid)
        if bouquet:
            caption = f"⭐️ *{bouquet['name']}*\n{bouquet['base_price']}₽"
            
            keyboard = [[InlineKeyboardButton("🛒 Заказать", callback_data=f"order:{bouquet['id']}")]]
            
            try:
                with open(bouquet['image_path'], 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=caption,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
            except:
                pass

async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать заказы (БЕЗ кнопки Детали и статуса)"""
    orders = db.get_user_orders(update.effective_user.id)
    
    if not orders:
        await update.message.reply_text("У вас пока нет заказов")
        return
    
    for order in orders[-10:]:
        text = (
            f"📦 *Заказ #{order['order_id']}*\n"
            f"📅 {order['created_at'][:16]}\n"
            f"💰 {order['total_price']}₽"
        )
        
        await update.message.reply_text(text, parse_mode='Markdown')

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация"""
    text = (
        "📞 Telegram: @thesun4ck\n"
        "⏰ 12:00 - 21:00\n"
        "🌐 ТГК: https://t.me/satinflowersali"
    )
    await update.message.reply_text(text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text("❌ Отменено")
    else:
        await update.message.reply_text("❌ Отменено")
    
    context.user_data.clear()
    return ConversationHandler.END

def register_handlers(application):
    """Регистрация"""
    application.add_handler(CommandHandler("start", start))
    
    application.add_handler(MessageHandler(filters.Regex("🌹 Каталог"), catalog))
    application.add_handler(MessageHandler(filters.Regex("🛒 Корзина"), show_cart))
    application.add_handler(MessageHandler(filters.Regex("⭐️ Избранное"), show_favorites))
    application.add_handler(MessageHandler(filters.Regex("📦 Мои заказы"), show_orders))
    application.add_handler(MessageHandler(filters.Regex("💬 Связаться со мной"), info))
    
    # ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_order, pattern="^order:")],
        states={
            CHOOSING_QUANTITY: [CallbackQueryHandler(choose_quantity, pattern="^qty:")],
            CHOOSING_PACKAGING: [CallbackQueryHandler(choose_packaging, pattern="^pkg:")],
            CHOOSING_EXTRAS: [CallbackQueryHandler(choose_extras, pattern="^extra:")],
            CARD_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, card_text_entered)],
            CHOOSING_DATE: [CallbackQueryHandler(choose_date, pattern="^date:")],
            CHOOSING_TIME: [CallbackQueryHandler(choose_time, pattern="^time:")],
            CHOOSING_PICKUP: [CallbackQueryHandler(choose_pickup, pattern="^pickup:")],
            ENTERING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_address)]
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")]
    )
    
    application.add_handler(conv_handler)
    
    application.add_handler(CallbackQueryHandler(confirm_add_to_cart, pattern="^confirm_cart$"))
    application.add_handler(CallbackQueryHandler(remove_from_cart, pattern="^remove:"))
    application.add_handler(CallbackQueryHandler(clear_cart_handler, pattern="^clear_cart$"))
    application.add_handler(CallbackQueryHandler(checkout, pattern="^checkout$"))
    application.add_handler(CallbackQueryHandler(payment_confirm, pattern="^payment_confirm$"))
    application.add_handler(CallbackQueryHandler(toggle_fav, pattern="^fav:"))
    application.add_handler(CallbackQueryHandler(admin_confirm_payment, pattern="^admin_confirm:"))
    application.add_handler(CallbackQueryHandler(admin_reject_payment, pattern="^admin_reject:"))
