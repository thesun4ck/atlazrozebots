from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from database import db
from config import ADMIN_ID
import logging

logger = logging.getLogger(__name__)

ADMIN_NAME, ADMIN_PRICE, ADMIN_PHOTO, ADMIN_POPULAR = range(4)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📦 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton("🌹 Управление букетами", callback_data="admin_bouquets")],
        [InlineKeyboardButton("➕ Добавить букет", callback_data="admin_add")]
    ]
    
    await update.message.reply_text(
        "*👑 Админ-панель*\n\nВыберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    stats = db.get_stats()
    
    text = (
        f"*📊 Статистика*\n\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"📦 Заказов: {stats['total_orders']}\n"
        f"💰 Выручка: {stats['total_revenue']:,}₽\n\n"
        f"*Сегодня:*\n"
        f"📦 Заказов: {stats['today_orders']}\n"
        f"💰 Выручка: {stats['today_revenue']:,}₽\n\n"
        f"🌹 Букетов: {stats['total_bouquets']}"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_back")]]
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    orders = db.get_all_orders()
    
    if not orders:
        await query.message.edit_text("Заказов пока нет")
        return
    
    text = "*📦 Последние 10 заказов:*\n\n"
    
    for order in orders[-10:]:
        text += (
            f"🔹 #{order['order_id']}\n"
            f"👤 {order['user_name']}\n"
            f"💰 {order['total_price']}₽\n"
            f"📅 {order['created_at'][:16]}\n\n"
        )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_back")]]
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_admin_bouquets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    bouquets = db.get_bouquets()
    
    if not bouquets:
        await query.message.edit_text("Букетов пока нет")
        return
    
    for bouquet in bouquets:
        order_count = bouquet.get('order_count', 0)
        text = (
            f"{'🔥 ' if bouquet.get('is_popular') else ''}*{bouquet['name']}*\n\n"
            f"💰 {bouquet['base_price']}₽\n"
            f"📦 Заказов: {order_count}"
        )
        
        keyboard = [
            [InlineKeyboardButton("🗑 Удалить", callback_data=f"delete:{bouquet['id']}")],
            [InlineKeyboardButton(
                "🔥 Снять популярность" if bouquet.get('is_popular') else "⭐️ Сделать популярным",
                callback_data=f"toggle_pop:{bouquet['id']}"
            )]
        ]
        
        try:
            with open(bouquet['image_path'], 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Photo error: {e}")
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_back")]]
    await query.message.reply_text(
        "Управление букетами",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def toggle_popular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    bouquet_id = query.data.split(":")[1]
    bouquet = db.get_bouquet_by_id(bouquet_id)
    
    if bouquet:
        new_status = not bouquet.get('is_popular', False)
        db.update_bouquet(bouquet_id, {'is_popular': new_status})
        
        await query.answer("✅ Обновлено")
        await query.message.delete()

async def delete_bouquet_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    bouquet_id = query.data.split(":")[1]
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"confirm_delete:{bouquet_id}"),
            InlineKeyboardButton("❌ Нет", callback_data="admin_bouquets")
        ]
    ]
    
    await query.message.edit_caption(
        caption="⚠️ Удалить букет?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def delete_bouquet_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Удалено")
    
    bouquet_id = query.data.split(":")[1]
    db.delete_bouquet(bouquet_id)
    await query.message.delete()

async def start_add_bouquet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['new_bouquet'] = {}
    
    await query.message.reply_text(
        "➕ *Новый букет*\n\n"
        "Шаг 1/3: Название:",
        parse_mode='Markdown'
    )
    
    return ADMIN_NAME

async def admin_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_bouquet']['name'] = update.message.text
    await update.message.reply_text("Шаг 2/3: Цена:")
    return ADMIN_PRICE

async def admin_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text)
        context.user_data['new_bouquet']['base_price'] = price
        await update.message.reply_text("Шаг 3/3: Фото:")
        return ADMIN_PHOTO
    except:
        await update.message.reply_text("❌ Введите число!")
        return ADMIN_PRICE

async def admin_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Отправьте фото!")
        return ADMIN_PHOTO
    
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    
    all_bouquets = db.get_bouquets()
    max_id = 0
    for b in all_bouquets:
        try:
            bid = int(b['id'].replace('b', ''))
            if bid > max_id:
                max_id = bid
        except:
            pass
    
    new_id = max_id + 1
    filename = f"images/b{new_id}.jpg"
    
    await file.download_to_drive(filename)
    context.user_data['new_bouquet']['image_path'] = filename
    
    keyboard = [
        [
            InlineKeyboardButton("🔥 Да", callback_data="popular:yes"),
            InlineKeyboardButton("Нет", callback_data="popular:no")
        ]
    ]
    
    await update.message.reply_text(
        "Популярный?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ADMIN_POPULAR

async def admin_popular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    is_popular = query.data.split(":")[1] == "yes"
    bouquet_data = context.user_data['new_bouquet']
    bouquet_data['is_popular'] = is_popular
    bouquet_data['quantities'] = [
        {"value": 15, "multiplier": 0.6},
        {"value": 25, "multiplier": 1.0},
        {"value": 51, "multiplier": 1.8},
        {"value": 101, "multiplier": 3.2}
    ]
    bouquet_data['packaging'] = [
        {"type": "standard", "name": "Стандарт", "price": 0},
        {"type": "premium", "name": "Премиум", "price": 300},
        {"type": "black", "name": "Черная", "price": 500}
    ]
    
    bouquet_id = db.save_bouquet(bouquet_data)
    
    await query.message.edit_text(
        f"✅ *Букет добавлен!*\n\n"
        f"🌹 {bouquet_data['name']}\n"
        f"💰 {bouquet_data['base_price']}₽\n"
        f"ID: {bouquet_id}",
        parse_mode='Markdown'
    )
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Отменено")
    return ConversationHandler.END

async def admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📦 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton("🌹 Управление букетами", callback_data="admin_bouquets")],
        [InlineKeyboardButton("➕ Добавить букет", callback_data="admin_add")]
    ]
    
    await query.message.edit_text(
        "*👑 Админ-панель*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def register_handlers(application):
    application.add_handler(CommandHandler("admin", admin_panel))
    
    application.add_handler(CallbackQueryHandler(show_stats, pattern="^admin_stats$"))
    application.add_handler(CallbackQueryHandler(show_admin_orders, pattern="^admin_orders$"))
    application.add_handler(CallbackQueryHandler(show_admin_bouquets, pattern="^admin_bouquets$"))
    application.add_handler(CallbackQueryHandler(toggle_popular, pattern="^toggle_pop:"))
    application.add_handler(CallbackQueryHandler(delete_bouquet_confirm, pattern="^delete:"))
    application.add_handler(CallbackQueryHandler(delete_bouquet_confirmed, pattern="^confirm_delete:"))
    application.add_handler(CallbackQueryHandler(admin_back, pattern="^admin_back$"))
    
    add_bouquet_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_bouquet, pattern="^admin_add$")],
        states={
            ADMIN_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_name)],
            ADMIN_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_price)],
            ADMIN_PHOTO: [MessageHandler(filters.PHOTO, admin_photo)],
            ADMIN_POPULAR: [CallbackQueryHandler(admin_popular, pattern="^popular:")]
        },
        fallbacks=[CommandHandler("cancel", cancel_add)]
    )
    
    application.add_handler(add_bouquet_conv)
