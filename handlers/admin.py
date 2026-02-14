from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from database import db
from config import ADMIN_ID
import logging

logger = logging.getLogger(__name__)

# States
ADMIN_NAME, ADMIN_DESC, ADMIN_PRICE, ADMIN_PHOTO = range(4)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ панель"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📦 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton("🌹 Управление букетами", callback_data="admin_bouquets")],
        [InlineKeyboardButton("➕ Добавить букет", callback_data="admin_add_bouquet")]
    ]
    
    await update.message.reply_text(
        "*👑 Админ-панель*\n\nВыберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика"""
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
    
    await query.message.edit_text(text, parse_mode='Markdown')

async def show_admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заказы"""
    query = update.callback_query
    await query.answer()
    
    orders = db.get_all_orders()
    
    if not orders:
        await query.message.edit_text("Заказов пока нет")
        return
    
    text = "*📦 Последние заказы:*\n\n"
    
    for order in orders[-10:]:
        text += (
            f"🔹 #{order['order_id']}\n"
            f"👤 {order['user_name']}\n"
            f"💰 {order['total_price']}₽\n"
            f"📅 {order['created_at'][:16]}\n\n"
        )
    
    await query.message.edit_text(text, parse_mode='Markdown')

async def show_admin_bouquets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление букетами"""
    query = update.callback_query
    await query.answer()
    
    bouquets = db.get_bouquets()
    
    text = "*🌹 Букеты в каталоге:*\n\n"
    
    for b in bouquets:
        text += f"• {b['name']} - {b['base_price']}₽\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_back")]]
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Назад в админку"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📦 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton("🌹 Управление букетами", callback_data="admin_bouquets")],
        [InlineKeyboardButton("➕ Добавить букет", callback_data="admin_add_bouquet")]
    ]
    
    await query.message.edit_text(
        "*👑 Админ-панель*\n\nВыберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def register_handlers(application):
    """Регистрация обработчиков"""
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CallbackQueryHandler(show_stats, pattern="^admin_stats$"))
    application.add_handler(CallbackQueryHandler(show_admin_orders, pattern="^admin_orders$"))
    application.add_handler(CallbackQueryHandler(show_admin_bouquets, pattern="^admin_bouquets$"))
    application.add_handler(CallbackQueryHandler(admin_back, pattern="^admin_back$"))
