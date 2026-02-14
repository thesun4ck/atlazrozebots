from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import (
    is_admin, get_statistics, get_all_orders, get_user_orders,
    update_order_status, save_bouquet, delete_bouquet_by_id,
    get_bouquets, get_bouquet_by_id, update_bouquet
)
from keyboards.admin_kb import (
    get_admin_menu, get_admin_order_keyboard, get_bouquet_management_keyboard
)

router = Router()

class AddBouquet(StatesGroup):
    entering_name = State()
    entering_description = State()
    entering_price = State()
    uploading_photo = State()
    choosing_popular = State()

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if await is_admin(message.from_user.id):
        await message.answer("Добро пожаловать в админ-панель!", reply_markup=get_admin_menu())
    else:
        await message.answer("У вас нет прав администратора.")

@router.message(F.text == "📊 Статистика")
async def show_stats_handler(message: Message):
    if not await is_admin(message.from_user.id): return
    stats = await get_statistics()
    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Пользователи: {stats['total_users']}\n"
        f"📦 Заказы: {stats['total_orders']}\n"
        f"💰 Выручка: {stats['total_revenue']}₽\n\n"
        f"📅 Сегодня: {stats['today_orders']} заказов на {stats['today_revenue']}₽\n"
        f"🌹 Букетов: {stats['total_bouquets']} (🔥 {stats['popular_bouquets']})"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📦 Заказы")
async def show_orders_handler(message: Message):
    if not await is_admin(message.from_user.id): return
    orders = await get_all_orders(limit=10)
    if not orders:
        await message.answer("Заказов нет.")
        return
        
    for order in orders:
        status_icon = "✅" if order['payment_status'] == "paid" else "⏳"
        text = (
            f"📦 <b>Заказ #{order['order_id']}</b>\n"
            f"👤 {order['user_name']} (ID: {order['user_id']})\n"
            f"💰 {order['total_order_price']}₽\n"
            f"Статус: {status_icon} {order['payment_status']}"
        )
        await message.answer(
            text, 
            reply_markup=get_admin_order_keyboard(order['order_id'], order['payment_status'], order['user_id']),
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("admin_order_confirm:"))
async def confirm_order_handler(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    await update_order_status(order_id, "paid")
    await callback.message.edit_text(f"✅ Заказ #{order_id} подтвержден!")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_order_cancel:"))
async def cancel_order_handler(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    await update_order_status(order_id, "cancelled")
    await callback.message.edit_text(f"❌ Заказ #{order_id} отменен!")
    await callback.answer()

@router.message(F.text == "➕ Добавить букет")
async def add_bouquet_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    await message.answer("Введите название букета:")
    await state.set_state(AddBouquet.entering_name)

@router.message(AddBouquet.entering_name)
async def bouquet_name_entered(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание:")
    await state.set_state(AddBouquet.entering_description)

@router.message(AddBouquet.entering_description)
async def bouquet_desc_entered(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите базовую цену (число):")
    await state.set_state(AddBouquet.entering_price)

@router.message(AddBouquet.entering_price)
async def bouquet_price_entered(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число.")
        return
    await state.update_data(base_price=int(message.text))
    await message.answer("Загрузите фото букета:")
    await state.set_state(AddBouquet.uploading_photo)

@router.message(AddBouquet.uploading_photo, F.photo)
async def bouquet_photo_uploaded(message: Message, state: FSMContext, bot: Bot):
    photo = message.photo[-1]
    file_id = photo.file_id
    file = await bot.get_file(file_id)
    file_path = f"images/{file_id}.jpg"
    await bot.download_file(file.file_path, file_path)
    
    await state.update_data(image_path=file_path)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔥 Да, популярный", callback_data="popular_yes")
    builder.button(text="Нет", callback_data="popular_no")
    
    await message.answer("Сделать популярным?", reply_markup=builder.as_markup())
    await state.set_state(AddBouquet.choosing_popular)

@router.callback_query(AddBouquet.choosing_popular)
async def bouquet_popular_chosen(callback: CallbackQuery, state: FSMContext):
    is_popular = callback.data == "popular_yes"
    data = await state.get_data()
    data['is_popular'] = is_popular
    
    # Save to DB
    bid = await save_bouquet(data)
    await state.clear()
    await callback.message.answer(f"✅ Букет добавлен! ID: {bid}")
    await callback.answer()

@router.message(F.text == "🌹 Управление букетами")
async def manage_bouquets_handler(message: Message):
    if not await is_admin(message.from_user.id): return
    bouquets = await get_bouquets()
    for b in bouquets:
        caption = f"🌹 <b>{b['name']}</b>\n{b['base_price']}₽\nID: {b['id']}"
        try:
            photo = FSInputFile(b['image_path'])
            await message.answer_photo(
                photo=photo,
                caption=caption,
                reply_markup=get_bouquet_management_keyboard(b['id'], b.get('is_popular', False)),
                parse_mode="HTML"
            )
        except:
            await message.answer(caption, parse_mode="HTML")

@router.callback_query(F.data.startswith("delete_bouquet:"))
async def delete_bouquet_handler(callback: CallbackQuery):
    bid = callback.data.split(":")[1]
    await delete_bouquet_by_id(bid)
    await callback.message.answer("🗑 Букет удален.")
    await callback.answer()

@router.callback_query(F.data.startswith("make_popular:"))
async def make_popular_handler(callback: CallbackQuery):
    bid = callback.data.split(":")[1]
    await update_bouquet(bid, {'is_popular': True})
    await callback.answer("✅ Отмечен как популярный")

@router.callback_query(F.data.startswith("unpopular:"))
async def make_unpopular_handler(callback: CallbackQuery):
    bid = callback.data.split(":")[1]
    await update_bouquet(bid, {'is_popular': False})
    await callback.answer("❌ Снята отметка популярности")
