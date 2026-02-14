from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def get_main_menu() -> ReplyKeyboardMarkup:
    # Главное меню для клиентов
    builder = ReplyKeyboardBuilder()
    builder.button(text="🌹 Каталог")
    builder.button(text="🛒 Корзина")
    builder.button(text="⭐️ Избранное")
    builder.button(text="📦 Мои заказы")
    builder.button(text="ℹ️ Информация")
    builder.button(text="💬 Связаться с нами")
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_catalog_keyboard(bouquet_id: str, is_favorite: bool) -> InlineKeyboardMarkup:
    # Клавиатура для карточки товара в каталоге
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 В корзину", callback_data=f"quick_add:{bouquet_id}")
    builder.button(
        text="❌ Из избранного" if is_favorite else "⭐️ В избранное",
        callback_data=f"fav_toggle:{bouquet_id}"
    )
    builder.button(text="📤 Поделиться", switch_inline_query=f"bouquet_{bouquet_id}")
    builder.button(text="👁 Подробнее", callback_data=f"details:{bouquet_id}")
    builder.adjust(2, 2)
    return builder.as_markup()

def get_catalog_navigation(page: int, has_next: bool) -> InlineKeyboardMarkup:
    # Навигация по каталогу
    builder = InlineKeyboardBuilder()
    if page > 0:
        builder.button(text="⬅️ Назад", callback_data=f"catalog_page:{page-1}")
    if has_next:
        builder.button(text="➡️ Далее", callback_data=f"catalog_page:{page+1}")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_cart_item_keyboard(index: int) -> InlineKeyboardMarkup:
    # Управление товаром в корзине
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить", callback_data=f"cart_remove:{index}")
    builder.button(text="✏️ Изменить", callback_data=f"cart_edit:{index}")
    builder.adjust(2)
    return builder.as_markup()

def get_cart_summary_keyboard(username: str) -> InlineKeyboardMarkup:
    # Действия с корзиной (оплата, очистка)
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить", callback_data="checkout")
    builder.button(text="💬 Связаться с нами", url=f"https://t.me/{username}")
    builder.button(text="🗑 Очистить корзину", callback_data="cart_clear")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_order_item_keyboard(order_id: str) -> InlineKeyboardMarkup:
    # Действия с заказом в истории
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Детали заказа", callback_data=f"order_details:{order_id}")
    builder.button(text="🔄 Заказать снова", callback_data=f"reorder:{order_id}")
    builder.adjust(1)
    return builder.as_markup()
