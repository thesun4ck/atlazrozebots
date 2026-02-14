from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def get_admin_menu() -> ReplyKeyboardMarkup:
    # Главное меню для админов
    builder = ReplyKeyboardBuilder()
    builder.button(text="📊 Статистика")
    builder.button(text="📦 Заказы")
    builder.button(text="🌹 Управление букетами")
    builder.button(text="👥 Пользователи")
    builder.button(text="➕ Добавить букет")
    builder.button(text="ℹ️ Информация")
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_admin_order_keyboard(order_id: str, status: str, user_id: int) -> InlineKeyboardMarkup:
    # Управление заказом для админа
    builder = InlineKeyboardBuilder()
    if status == "pending":
        builder.button(text="✅ Подтвердить", callback_data=f"admin_order_confirm:{order_id}")
        builder.button(text="❌ Отменить", callback_data=f"admin_order_cancel:{order_id}")
    builder.button(text="📋 Детали", callback_data=f"admin_order_details:{order_id}")
    builder.button(text="💬 Написать клиенту", url=f"tg://user?id={user_id}")
    builder.adjust(2, 2)
    return builder.as_markup()

def get_bouquet_management_keyboard(bouquet_id: str, is_popular: bool) -> InlineKeyboardMarkup:
    # Управление букетом (редактирование/удаление)
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=f"edit_bouquet:{bouquet_id}")
    builder.button(text="🗑 Удалить", callback_data=f"delete_bouquet:{bouquet_id}")
    
    if is_popular:
        builder.button(text="🔥 Снять популярность", callback_data=f"unpopular:{bouquet_id}")
    else:
        builder.button(text="⭐️ Сделать популярным", callback_data=f"make_popular:{bouquet_id}")
    
    builder.adjust(2, 1)
    return builder.as_markup()
