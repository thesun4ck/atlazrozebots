from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from database import db
from config import CONTACT_USERNAME, ADMIN_ID
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# States
(CHOOSING_QUANTITY, CHOOSING_PACKAGING, CHOOSING_EXTRAS, 
 CARD_TEXT, CHOOSING_DATE, CUSTOM_DATE, CHOOSING_TIME, CUSTOM_TIME,
 CHOOSING_PICKUP, ENTERING_ADDRESS) = range(10)

def get_main_menu():
    keyboard = [
        ["🌹 Каталог", "🛒 Корзина"],
        ["⭐️ Избранное", "📦 Мои заказы"],
        ["💬 Связаться со мной"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.save_user(user.id, user.username, user.first_name, user.last_name or "")
    
    await update.message.reply_text(
        "🌹 *Добро пожаловать в Flower Shop!*\n\n"
        "Мы создаем уникальные букеты из атласных роз ручной работы.\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )

async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bouquets = db.get_bouquets()
    
    if not bouquets:
        await update.message.reply_text(
            f"На данный момент каталог пуст, но можете написать и уточнить информацию @{CONTACT_USERNAME}"
        )
        return
    
    favorites = db.get_favorites(update.effective_user.id)
    
    for bouquet in bouquets:
        is_fav = bouquet['id'] in favorites
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
    query = update.callback_query
    await query.answer()
    
    bouquet_id = query.data.split(":")[1]
    bouquet = db.get_bouquet_by_id(bouquet_id)
    
    if not bouquet:
        await query.message.reply_text("Букет не найден")
        return ConversationHandler.END
    
    context.user_data['bouquet'] = bouquet
    context.user_data['order'] = {}
    
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
    query = update.callback_query
    await query.answer()
    
    _, qty, price = query.data.split(":")
    context.user_data['order']['quantity'] = int(qty)
    context.user_data['order']['base_price'] = int(price)
    
    bouquet = context.user_data['bouquet']
    
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
    query = update.callback_query
    await query.answer()
    
    _, pkg_type, pkg_price = query.data.split(":")
    context.user_data['order']['packaging'] = {'type': pkg_type, 'price': int(pkg_price)}
    
    # Инициализируем extras
    if 'extras' not in context.user_data['order']:
        context.user_data['order']['extras'] = {'urgent': False, 'card': False}
    
    keyboard = [
        [InlineKeyboardButton(
            "✅ Срочно (+1000₽)" if context.user_data['order']['extras'].get('urgent') else "⚡️ Срочно (+1000₽)",
            callback_data="extra:urgent"
        )],
        [InlineKeyboardButton(
            "✅ Открытка (+100₽)" if context.user_data['order']['extras'].get('card') else "💌 Открытка (+100₽)",
            callback_data="extra:card"
        )],
        [InlineKeyboardButton("Продолжить ➡️", callback_data="extra:done")]
    ]
    
    await query.message.edit_text(
        "Дополнительные услуги:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CHOOSING_EXTRAS

async def choose_extras(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    extra_type = query.data.split(":")[1]
    
    if extra_type == "urgent":
        context.user_data['order']['extras']['urgent'] = not context.user_data['order']['extras'].get('urgent', False)
        await query.answer("✅ Срочный заказ " + ("добавлен" if context.user_data['order']['extras']['urgent'] else "убран"))
        
        # Обновляем кнопки
        keyboard = [
            [InlineKeyboardButton(
                "✅ Срочно (+1000₽)" if context.user_data['order']['extras'].get('urgent') else "⚡️ Срочно (+1000₽)",
                callback_data="extra:urgent"
            )],
            [InlineKeyboardButton(
                "✅ Открытка (+100₽)" if context.user_data['order']['extras'].get('card') else "💌 Открытка (+100₽)",
                callback_data="extra:card"
            )],
            [InlineKeyboardButton("Продолжить ➡️", callback_data="extra:done")]
        ]
        
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        return CHOOSING_EXTRAS
        
    elif extra_type == "card":
        context.user_data['order']['extras']['card'] = True
        await query.message.reply_text("Введите текст для открытки (до 200 символов):")
        await query.answer()
        return CARD_TEXT
    else:
        await query.answer()
        return await show_date_selection(query.message, context)

async def card_text_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text[:200]
    context.user_data['order']['extras']['card_text'] = text
    
    return await show_date_selection(update.message, context)

async def show_date_selection(message, context):
    quantity = context.user_data['order']['quantity']
    today = datetime.now()
    
    start_day = 4 if quantity > 51 else 2
    
    keyboard = []
    for i in range(start_day, start_day + 5):
        date = today + timedelta(days=i)
        keyboard.append([InlineKeyboardButton(
            date.strftime("%d.%m"),
            callback_data=f"date:{date.strftime('%Y-%m-%d')}"
        )])
    keyboard.append([InlineKeyboardButton("📅 Своя дата", callback_data="date:custom")])
    
    await message.reply_text(
        "На какую дату нужен букет?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CHOOSING_DATE

async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    date_str = query.data.split(":")[1]
    
    if date_str == "custom":
        quantity = context.user_data['order']['quantity']
        min_days = 4 if quantity > 51 else 2
        min_date = (datetime.now() + timedelta(days=min_days)).strftime("%d.%m")
        
        await query.message.reply_text(
            f"Введите дату в формате ДД.ММ\n"
            f"Минимальная дата: {min_date}"
        )
        return CUSTOM_DATE
    
    context.user_data['order']['date'] = date_str
    
    keyboard = [
        [InlineKeyboardButton("12:00", callback_data="time:12:00"), 
         InlineKeyboardButton("14:00", callback_data="time:14:00")],
        [InlineKeyboardButton("16:00", callback_data="time:16:00"), 
         InlineKeyboardButton("18:00", callback_data="time:18:00")],
        [InlineKeyboardButton("20:00", callback_data="time:20:00")],
        [InlineKeyboardButton("🕐 Своё время", callback_data="time:custom")]
    ]
    
    await query.message.edit_text(
        "К какому времени?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CHOOSING_TIME

async def custom_date_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Парсим дату
        day, month = update.message.text.split(".")
        year = datetime.now().year
        date = datetime(year, int(month), int(day))
        
        # Проверяем минимальные сроки
        quantity = context.user_data['order']['quantity']
        min_days = 4 if quantity > 51 else 2
        min_date = datetime.now() + timedelta(days=min_days)
        
        if date < min_date:
            await update.message.reply_text(
                f"❌ Слишком ранняя дата!\n"
                f"Минимум: {min_date.strftime('%d.%m')}"
            )
            return CUSTOM_DATE
        
        context.user_data['order']['date'] = date.strftime('%Y-%m-%d')
        
        keyboard = [
            [InlineKeyboardButton("12:00", callback_data="time:12:00"), 
             InlineKeyboardButton("14:00", callback_data="time:14:00")],
            [InlineKeyboardButton("16:00", callback_data="time:16:00"), 
             InlineKeyboardButton("18:00", callback_data="time:18:00")],
            [InlineKeyboardButton("20:00", callback_data="time:20:00")],
            [InlineKeyboardButton("🕐 Своё время", callback_data="time:custom")]
        ]
        
        await update.message.reply_text(
            "К какому времени?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return CHOOSING_TIME
    except:
        await update.message.reply_text(
            "❌ Неверный формат! Используйте ДД.ММ\n"
            "Например: 20.02"
        )
        return CUSTOM_DATE

async def choose_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    time_str = query.data.split(":", 1)[1]
    
    if time_str == "custom":
        await query.message.reply_text(
            "Введите время в формате ЧЧ:ММ\n"
            "Доступно: 12:00 - 20:00"
        )
        return CUSTOM_TIME
    
    context.user_data['order']['time'] = time_str
    
    keyboard = [
        [InlineKeyboardButton("🏠 Самовывоз", callback_data="pickup:self")],
        [InlineKeyboardButton("📍 Встреча в городе", callback_data="pickup:meeting")]
    ]
    
    await query.message.edit_text(
        "Как будете получать?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CHOOSING_PICKUP

async def custom_time_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        time_str = update.message.text.strip()
        hour, minute = map(int, time_str.split(":"))
        
        if not (12 <= hour <= 20 and 0 <= minute < 60):
            await update.message.reply_text(
                "❌ Неверное время!\n"
                "Доступно: 12:00 - 20:00"
            )
            return CUSTOM_TIME
        
        context.user_data['order']['time'] = f"{hour:02d}:{minute:02d}"
        
        keyboard = [
            [InlineKeyboardButton("🏠 Самовывоз", callback_data="pickup:self")],
            [InlineKeyboardButton("📍 Встреча в городе", callback_data="pickup:meeting")]
        ]
        
        await update.message.reply_text(
            "Как будете получать?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return CHOOSING_PICKUP
    except:
        await update.message.reply_text(
            "❌ Неверный формат! Используйте ЧЧ:ММ\n"
            "Например: 14:30"
        )
        return CUSTOM_TIME

async def choose_pickup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    method = query.data.split(":")[1]
    context.user_data['order']['pickup'] = method
    
    if method == "meeting":
        await query.message.reply_text("Введите адрес встречи:")
        return ENTERING_ADDRESS
    else:
        context.user_data['order']['address'] = "Самовывоз"
        await show_summary(query.message, context)
        return ConversationHandler.END

async def enter_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order']['address'] = update.message.text
    await show_summary(update.message, context)
    return ConversationHandler.END

async def show_summary(message, context):
    bouquet = context.user_data['bouquet']
    order = context.user_data['order']
    
    total = order['base_price'] + order['packaging']['price']
    
    extras_text = ""
    if order.get('extras', {}).get('urgent'):
        total += 1000
        extras_text += "⚡️ Срочный заказ\n"
    
    if order.get('extras', {}).get('card_text'):
        total += 100
        extras_text += f"💌 Открытка: {order['extras']['card_text']}\n"
    
    order['total_price'] = total
    
    summary = (
        f"*📋 Ваш заказ:*\n\n"
        f"🌹 {bouquet['name']}\n"
        f"🔢 {order['quantity']} роз\n"
        f"📦 {order['packaging']['type']}\n"
        f"{extras_text}"
        f"📅 {order['date']} в {order['time']}\n"
        f"📍 {order.get('address', 'Самовывоз')}\n\n"
        f"💰 *Итого: {total}₽*"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ В корзину", callback_data="confirm_cart")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    
    await message.reply_text(
        summary,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def confirm_add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        'pickup': order.get('pickup', 'self'),
        'address': order.get('address', 'Самовывоз'),
        'total_price': order['total_price']
    }
    
    db.add_to_cart(update.effective_user.id, item)
    await query.message.edit_text("✅ Товар добавлен в корзину!")
    context.user_data.clear()

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart = db.get_user_cart(update.effective_user.id)
    
    if not cart:
        await update.message.reply_text("Корзина пуста")
        return
    
    total = 0
    for i, item in enumerate(cart):
        total += item['total_price']
        
        extras = []
        if item.get('extras', {}).get('urgent'):
            extras.append("⚡️")
        if item.get('extras', {}).get('card_text'):
            extras.append("💌")
        
        extras_text = " " + "".join(extras) if extras else ""
        
        text = (
            f"🌹 *{item['bouquet_name']}*\n"
            f"🔢 {item['quantity']} роз{extras_text}\n"
            f"📅 {item['date']} в {item['time']}\n"
            f"📍 {item.get('address', 'Самовывоз')}\n"
            f"💰 {item['total_price']}₽"
        )
        
        keyboard = [[InlineKeyboardButton("🗑 Удалить", callback_data=f"remove:{i}")]]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    keyboard = [
        [InlineKeyboardButton("💬 Связаться об оплате", url=f"https://t.me/{CONTACT_USERNAME}")],
        [InlineKeyboardButton("🗑 Очистить", callback_data="clear_cart")]
    ]
    
    await update.message.reply_text(
        f"*💰 Итого: {total}₽*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def remove_from_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Удалено")
    
    index = int(query.data.split(":")[1])
    db.remove_from_cart(update.effective_user.id, index)
    await query.message.edit_text("🗑 Товар удален")

async def clear_cart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    db.clear_cart(update.effective_user.id)
    await query.message.edit_text("🗑 Корзина очищена")

async def toggle_fav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    bouquet_id = query.data.split(":")[1]
    db.toggle_favorite(update.effective_user.id, bouquet_id)
    
    favorites = db.get_favorites(update.effective_user.id)
    is_fav = bouquet_id in favorites
    
    await query.answer("❤️ Добавлено" if is_fav else "Удалено")

async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    text = (
        "📞 Telegram: @thesun4ck\n"
        "⏰ 12:00 - 21:00\n"
        "🌐 ТГК: https://t.me/satinflowersali"
    )
    await update.message.reply_text(text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text("❌ Отменено")
    else:
        await update.message.reply_text("❌ Отменено")
    
    context.user_data.clear()
    return ConversationHandler.END

def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    
    application.add_handler(MessageHandler(filters.Regex("🌹 Каталог"), catalog))
    application.add_handler(MessageHandler(filters.Regex("🛒 Корзина"), show_cart))
    application.add_handler(MessageHandler(filters.Regex("⭐️ Избранное"), show_favorites))
    application.add_handler(MessageHandler(filters.Regex("📦 Мои заказы"), show_orders))
    application.add_handler(MessageHandler(filters.Regex("💬 Связаться со мной"), info))
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_order, pattern="^order:")],
        states={
            CHOOSING_QUANTITY: [CallbackQueryHandler(choose_quantity, pattern="^qty:")],
            CHOOSING_PACKAGING: [CallbackQueryHandler(choose_packaging, pattern="^pkg:")],
            CHOOSING_EXTRAS: [CallbackQueryHandler(choose_extras, pattern="^extra:")],
            CARD_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, card_text_entered)],
            CHOOSING_DATE: [CallbackQueryHandler(choose_date, pattern="^date:")],
            CUSTOM_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_date_entered)],
            CHOOSING_TIME: [CallbackQueryHandler(choose_time, pattern="^time:")],
            CUSTOM_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_time_entered)],
            CHOOSING_PICKUP: [CallbackQueryHandler(choose_pickup, pattern="^pickup:")],
            ENTERING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_address)]
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    application.add_handler(CallbackQueryHandler(confirm_add_to_cart, pattern="^confirm_cart$"))
    application.add_handler(CallbackQueryHandler(remove_from_cart, pattern="^remove:"))
    application.add_handler(CallbackQueryHandler(clear_cart_handler, pattern="^clear_cart$"))
    application.add_handler(CallbackQueryHandler(toggle_fav, pattern="^fav:"))
