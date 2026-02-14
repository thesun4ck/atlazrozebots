from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import (
    get_bouquets, get_bouquet_by_id, get_favorites, toggle_favorite,
    get_user_cart, add_to_cart, remove_from_cart, clear_cart,
    create_order, get_user_orders, is_admin, ensure_user_exists
)
from keyboards.client_kb import (
    get_main_menu, get_catalog_keyboard, get_catalog_navigation,
    get_cart_item_keyboard, get_cart_summary_keyboard, get_order_item_keyboard
)

router = Router()

class BouquetConstructor(StatesGroup):
    choosing_color = State()
    choosing_quantity = State()
    choosing_packaging = State()
    choosing_extras = State()
    entering_card_text = State()
    choosing_date = State()
    choosing_time = State()
    choosing_pickup = State()
    entering_address = State()
    confirming = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # Приветствие и создание записи пользователя
    print(f"Start command from {message.from_user.id}")
    user = message.from_user
    await ensure_user_exists(user.id, user.username, user.first_name, user.last_name or "")
    
    # Deep linking check
    args = message.text.split()[1] if len(message.text.split()) > 1 else None
    if args and args.startswith("bouquet_"):
        bouquet_id = args.split("_")[1]
        # Skip to details
        await message.answer("Переход к букету...")
        # Simulate callback logic or just show it
        # Simplified: just show catalog item logic
        return

    await message.answer(
        f"🌹 Добро пожаловать в <b>Flower Shop</b>!\n\n"
        f"Мы создаем уникальные букеты из атласных роз ручной работы. "
        f"Каждый букет - это произведение искусства!\n\n"
        f"Выберите действие:",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )

@router.message(F.text == "🌹 Каталог")
async def show_catalog(message: Message, state: FSMContext):
    # Показать каталог букетов
    print(f"Catalog requested by {message.from_user.id}")
    bouquets = await get_bouquets()
    if not bouquets:
        await message.answer("Каталог пуст.")
        return

    user_id = message.from_user.id
    favorites = await get_favorites(user_id)
    
    # Показываем постранично, тут упростим и покажем первые 5
    page_size = 5
    page = 0 
    
    start = page * page_size
    end = start + page_size
    
    for bouquet in bouquets[start:end]:
        is_favorite = bouquet['id'] in favorites
        caption = (
            f"{'🔥 ' if bouquet.get('is_popular') else ''}<b>{bouquet['name']}</b>\n\n"
            f"{bouquet['description']}\n\n"
            f"💰 Цена от: <b>{bouquet['base_price']}₽</b>"
        )
        try:
            photo = FSInputFile(bouquet['image_path'])
            await message.answer_photo(
                photo=photo,
                caption=caption,
                reply_markup=get_catalog_keyboard(bouquet['id'], is_favorite),
                parse_mode="HTML"
            )
        except Exception as e:
            await message.answer(f"Ошибка загрузки фото: {e}\n\n{caption}")
    
    # Навигация (упрощенная)
    if len(bouquets) > page_size:
        await message.answer(
            "Навигация:", 
            reply_markup=get_catalog_navigation(page, len(bouquets) > end)
        )

@router.callback_query(F.data.startswith("details:"))
async def bouquet_details(callback: CallbackQuery, state: FSMContext):
    # Начинаем процесс заказа (конструктор)
    bouquet_id = callback.data.split(":")[1]
    bouquet = await get_bouquet_by_id(bouquet_id)
    
    await state.update_data(bouquet_id=bouquet_id, bouquet_name=bouquet['name'], base_price=bouquet['base_price'])
    
    # Шаг 1: Цвет
    builder = InlineKeyboardBuilder()
    color_map = {
        "pink": ("🩷", "Розовый"),
        "red": ("❤️", "Красный"),
        "blue": ("💙", "Синий"),
        "white": ("🤍", "Белый"),
        "mix": ("🌈", "Микс")
    }
    
    for color in bouquet.get('colors', []):
        emoji, name = color_map.get(color, ("🎨", color))
        builder.button(text=f"{emoji} {name}", callback_data=f"color:{color}")
    
    builder.button(text="◀️ Отмена", callback_data="cancel_order")
    builder.adjust(2)
    
    await callback.message.answer("Выберите цвет роз:", reply_markup=builder.as_markup())
    await state.set_state(BouquetConstructor.choosing_color)
    await callback.answer()

@router.callback_query(BouquetConstructor.choosing_color, F.data.startswith("color:"))
async def color_chosen(callback: CallbackQuery, state: FSMContext):
    # Цвет выбран, далее количество
    color = callback.data.split(":")[1]
    await state.update_data(color=color)
    
    data = await state.get_data()
    bouquet = await get_bouquet_by_id(data['bouquet_id'])
    
    builder = InlineKeyboardBuilder()
    for qty in bouquet.get('quantities', []):
        val = qty['value']
        mult = qty['multiplier']
        price = int(bouquet['base_price'] * mult)
        builder.button(text=f"{val} роз - {price}₽", callback_data=f"qty:{val}:{price}")
        
    builder.button(text="◀️ Назад", callback_data="back_to_color")
    builder.adjust(1)
    
    await callback.message.edit_text("Выберите количество роз:", reply_markup=builder.as_markup())
    await state.set_state(BouquetConstructor.choosing_quantity)

@router.callback_query(BouquetConstructor.choosing_quantity, F.data.startswith("qty:"))
async def quantity_chosen(callback: CallbackQuery, state: FSMContext):
    # Количество выбрано, далее упаковка
    _, qty, price = callback.data.split(":")
    await state.update_data(quantity=int(qty), price=int(price))
    
    data = await state.get_data()
    bouquet = await get_bouquet_by_id(data['bouquet_id'])
    
    builder = InlineKeyboardBuilder()
    for pkg in bouquet.get('packaging', []):
        p_name = pkg['name']
        p_price = pkg['price']
        label = f"{p_name} - {p_price}₽" if p_price > 0 else f"{p_name} - Бесплатно"
        builder.button(text=label, callback_data=f"pkg:{pkg['type']}:{p_price}:{p_name}")
        
    builder.button(text="◀️ Назад", callback_data="back_to_qty")
    builder.adjust(1)
    
    await callback.message.edit_text("Выберите упаковку:", reply_markup=builder.as_markup())
    await state.set_state(BouquetConstructor.choosing_packaging)

@router.callback_query(BouquetConstructor.choosing_packaging, F.data.startswith("pkg:"))
async def packaging_chosen(callback: CallbackQuery, state: FSMContext):
    # Упаковка выбрана, далее допы
    _, pkg_type, pkg_price, pkg_name = callback.data.split(":")
    await state.update_data(packaging={'type': pkg_type, 'price': int(pkg_price), 'name': pkg_name})
    
    builder = InlineKeyboardBuilder()
    builder.button(text="⚡️ Срочно (+1000₽)", callback_data="extra_urgent")
    builder.button(text="💌 Открытка (+100₽)", callback_data="extra_card")
    builder.button(text="✅ Готово / без доп.", callback_data="extra_done")
    builder.button(text="◀️ Назад", callback_data="back_to_pkg")
    builder.adjust(1)
    
    await callback.message.edit_text("Дополнительные услуги:", reply_markup=builder.as_markup())
    await state.set_state(BouquetConstructor.choosing_extras)

@router.callback_query(BouquetConstructor.choosing_extras)
async def extras_chosen(callback: CallbackQuery, state: FSMContext):
    # Обработка допов
    data = await state.get_data()
    extras = data.get('extras', {'urgent': False, 'card': False})
    
    if callback.data == "extra_urgent":
        extras['urgent'] = not extras['urgent']
        await state.update_data(extras=extras)
        await callback.answer("Срочность " + ("добавлена" if extras['urgent'] else "убрана"))
    elif callback.data == "extra_card":
        extras['card'] = not extras['card']
        await state.update_data(extras=extras)
        if extras['card']:
            await callback.message.answer("Введите текст для открытки:")
            await state.set_state(BouquetConstructor.entering_card_text)
            return
        else:
            await callback.answer("Открытка убрана")
    elif callback.data == "extra_done":
        # Переход к дате
        builder = InlineKeyboardBuilder()
        builder.button(text="📅 Сегодня", callback_data="date:today")
        builder.button(text="📅 Завтра", callback_data="date:tomorrow")
        builder.button(text="Ввести дату", callback_data="date:custom")
        builder.adjust(2)
        await callback.message.answer("Когда доставить?", reply_markup=builder.as_markup())
        await state.set_state(BouquetConstructor.choosing_date)
        return

    # Если мы остались в меню допов, обновляем клавиатуру (можно добавить галочки)
    # Для простоты просто ждем нажатия Готово

@router.message(BouquetConstructor.entering_card_text)
async def card_text_entering(message: Message, state: FSMContext):
    # Текст открытки введен
    await state.update_data(card_text=message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Продолжить", callback_data="extra_done")
    await message.answer("Текст сохранен.", reply_markup=builder.as_markup())
    await state.set_state(BouquetConstructor.choosing_extras)

@router.callback_query(BouquetConstructor.choosing_date)
async def date_chosen(callback: CallbackQuery, state: FSMContext):
    # Дата выбрана
    date_val = callback.data.split(":")[1]
    await state.update_data(delivery_date=date_val)
    
    # Время
    builder = InlineKeyboardBuilder()
    times = ["10:00", "12:00", "14:00", "16:00", "18:00", "20:00"]
    for t in times:
        builder.button(text=t, callback_data=f"time:{t}")
    builder.adjust(3)
    await callback.message.answer("Выберите время:", reply_markup=builder.as_markup())
    await state.set_state(BouquetConstructor.choosing_time)

@router.callback_query(BouquetConstructor.choosing_time)
async def time_chosen(callback: CallbackQuery, state: FSMContext):
    # Время выбрано
    time_val = callback.data.split(":")[1]
    await state.update_data(delivery_time=time_val)
    
    # Способ получения
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Самовывоз", callback_data="pickup:shop")
    builder.button(text="📍 Доставка/Встреча", callback_data="pickup:meeting")
    builder.adjust(2)
    await callback.message.answer("Способ получения:", reply_markup=builder.as_markup())
    await state.set_state(BouquetConstructor.choosing_pickup)

@router.callback_query(BouquetConstructor.choosing_pickup)
async def pickup_chosen(callback: CallbackQuery, state: FSMContext):
    # Способ выбран
    method = callback.data.split(":")[1]
    await state.update_data(pickup_method=method)
    
    if method == "meeting":
        await callback.message.answer("Введите адрес доставки/встречи:")
        await state.set_state(BouquetConstructor.entering_address)
    else:
        await state.update_data(address="Самовывоз из магазина")
        await show_order_summary(callback.message, state)

@router.message(BouquetConstructor.entering_address)
async def address_entered(message: Message, state: FSMContext):
    # Адрес введен
    await state.update_data(address=message.text)
    await show_order_summary(message, state)

async def show_order_summary(message: Message, state: FSMContext):
    # Показать итог и добавить в корзину
    data = await state.get_data()
    
    # Расчет цены
    base = data['price']
    pkg = data['packaging']['price']
    extras_price = 0
    extras = data.get('extras', {})
    if extras.get('urgent'): extras_price += 1000
    if extras.get('card'): extras_price += 100
    
    total = base + pkg + extras_price
    await state.update_data(total_price=total)
    
    text = (
        f"📋 <b>Ваш заказ:</b>\n\n"
        f"🌹 {data['bouquet_name']}\n"
        f"🎨 Цвет: {data['color']}\n"
        f"🔢 Количество: {data['quantity']} роз\n"
        f"📦 Упаковка: {data['packaging']['name']}\n"
        f"⚡️ Срочно: {'Да' if extras.get('urgent') else 'Нет'}\n"
        f"💌 Открытка: {'Да' if extras.get('card') else 'Нет'}\n"
        f"📅 Дата: {data['delivery_date']} {data['delivery_time']}\n"
        f"📍 {data['pickup_method']}: {data['address']}\n\n"
        f"💰 <b>Итого: {total}₽</b>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ В корзину", callback_data="confirm_add_to_cart")
    builder.button(text="❌ Отмена", callback_data="cancel_order")
    builder.adjust(1)
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.set_state(BouquetConstructor.confirming)

@router.callback_query(BouquetConstructor.confirming, F.data == "confirm_add_to_cart")
async def add_to_cart_confirm(callback: CallbackQuery, state: FSMContext):
    # Добавляем в корзину и сбрасываем стейт
    data = await state.get_data()
    user_id = callback.from_user.id
    
    item = {
        'bouquet_id': data['bouquet_id'],
        'bouquet_name': data['bouquet_name'],
        'color': data['color'],
        'quantity': data['quantity'],
        'packaging': data['packaging'],
        'urgent_order': data.get('extras', {}).get('urgent', False),
        'greeting_card': {
            'enabled': data.get('extras', {}).get('card', False),
            'text': data.get('card_text', '')
        },
        'delivery_date': data['delivery_date'],
        'ready_time': data['delivery_time'],
        'pickup_method': data['pickup_method'],
        'address': data['address'],
        'total_price': data['total_price']
    }
    
    await add_to_cart(user_id, item)
    await state.clear()
    await callback.message.answer("✅ Товар добавлен в корзину!")
    await callback.answer()

@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Заказ отменен.")
    await callback.answer()

@router.message(F.text == "🛒 Корзина")
async def show_cart_handler(message: Message):
    # Показать корзину
    user_id = message.from_user.id
    cart = await get_user_cart(user_id)
    
    if not cart:
        await message.answer("Корзина пуста.")
        return
        
    total_sum = 0
    for idx, item in enumerate(cart):
        total_sum += item['total_price']
        text = (
            f"🌹 {item['bouquet_name']} ({item['quantity']} шт)\n"
            f"🎨 {item['color']} | 📦 {item['packaging']['name']}\n"
            f"💰 {item['total_price']}₽"
        )
        await message.answer(text, reply_markup=get_cart_item_keyboard(idx))
    
    await message.answer(
        f"💰 <b>Общая сумма: {total_sum}₽</b>",
        reply_markup=get_cart_summary_keyboard(message.from_user.username),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "cart_clear")
async def clear_cart_handler(callback: CallbackQuery):
    await clear_cart(callback.from_user.id)
    await callback.message.answer("Корзина очищена.")
    await callback.answer()

@router.callback_query(F.data.startswith("cart_remove:"))
async def remove_cart_item_handler(callback: CallbackQuery):
    idx = int(callback.data.split(":")[1])
    await remove_from_cart(callback.from_user.id, idx)
    await callback.message.answer("Товар удален.")
    await show_cart_handler(callback.message) # Refresh
    await callback.answer()

@router.callback_query(F.data == "checkout")
async def checkout_handler(callback: CallbackQuery):
    # Оплата (заглушка)
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Я оплатил", callback_data="payment_confirm")
    builder.button(text="❌ Отмена", callback_data="payment_cancel")
    
    await callback.message.answer(
        "Переведите средсва на карту 1234-5678\nНажмите кнопку после оплаты.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "payment_confirm")
async def payment_confirm_handler(callback: CallbackQuery, bot: Bot):
    # Подтверждение оплаты и создание заказа
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name
    order_id = await create_order(user_id, user_name)
    await clear_cart(user_id)
    
    await callback.message.answer(f"✅ Заказ #{order_id} оформлен! Менеджер свяжется с вами.")
    await callback.answer()
    
    # Уведомление админам (нужно реализовать notify_admins)

@router.message(F.text == "⭐️ Избранное")
async def favorites_handler(message: Message):
    # Показать избранное
    user_id = message.from_user.id
    fav_ids = await get_favorites(user_id)
    if not fav_ids:
        await message.answer("В избранном пусто.")
        return
        
    for bid in fav_ids:
        bouquet = await get_bouquet_by_id(bid)
        if bouquet:
            caption = f"⭐️ <b>{bouquet['name']}</b>\n{bouquet['base_price']}₽"
            try:
                photo = FSInputFile(bouquet['image_path'])
                await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML")
            except:
                await message.answer(caption, parse_mode="HTML")

@router.callback_query(F.data.startswith("fav_toggle:"))
async def fav_toggle_handler(callback: CallbackQuery):
    bid = callback.data.split(":")[1]
    await toggle_favorite(callback.from_user.id, bid)
    await callback.answer("Избранное обновлено")

@router.inline_query()
async def inline_share_handler(inline_query: InlineQuery):
    # Поделиться букетом через inline
    query = inline_query.query
    if query.startswith("bouquet_"):
        bid = query.split("_")[1]
        bouquet = await get_bouquet_by_id(bid)
        if bouquet:
            result = InlineQueryResultArticle(
                id=bid,
                title=bouquet['name'],
                description=f"Цена: {bouquet['base_price']}₽",
                thumbnail_url="https://via.placeholder.com/150", # Заглушка, т.к. локальные файлы не работают в inline
                input_message_content=InputTextMessageContent(
                    message_text=f"Посмотри этот букет: {bouquet['name']}!\nЦена: {bouquet['base_price']}₽"
                )
            )
            await inline_query.answer([result], cache_time=1)
