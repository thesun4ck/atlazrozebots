import yaml
import aiofiles
from typing import List, Dict, Optional
from datetime import datetime
import os

DATA_DIR = "data"

# ============ БУКЕТЫ ============

async def get_bouquets() -> List[Dict]:
    # Получить все букеты из файла
    async with aiofiles.open(f"{DATA_DIR}/bouquets.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content)
        return data.get('bouquets', [])

async def get_bouquet_by_id(bouquet_id: str) -> Optional[Dict]:
    # Найти букет по ID
    bouquets = await get_bouquets()
    return next((b for b in bouquets if b['id'] == bouquet_id), None)

async def get_bouquets_by_ids(bouquet_ids: List[str]) -> List[Dict]:
    # Получить список букетов по их ID
    bouquets = await get_bouquets()
    return [b for b in bouquets if b['id'] in bouquet_ids]

async def save_bouquet(bouquet_data: Dict) -> str:
    # Сохранить новый букет
    bouquets = await get_bouquets()
    
    # Генерируем ID
    max_id = 0
    for b in bouquets:
        try:
            bid = int(b['id'].replace('b', ''))
            if bid > max_id:
                max_id = bid
        except ValueError:
            pass
            
    bouquet_id = f"b{max_id + 1}"
    
    new_bouquet = {
        'id': bouquet_id,
        'name': bouquet_data['name'],
        'description': bouquet_data['description'],
        'base_price': bouquet_data['base_price'],
        'image_path': bouquet_data['image_path'],
        'is_popular': bouquet_data['is_popular'],
        'colors': ["pink", "red", "blue", "white", "mix"],
        'quantities': [
            {'value': 15, 'multiplier': 0.6},
            {'value': 25, 'multiplier': 1.0},
            {'value': 51, 'multiplier': 1.8},
            {'value': 101, 'multiplier': 3.2}
        ],
        'packaging': [
            {'type': 'standard', 'name': 'Стандарт', 'price': 0},
            {'type': 'premium', 'name': 'Премиум', 'price': 300},
            {'type': 'black', 'name': 'Черная', 'price': 500}
        ]
    }
    
    bouquets.append(new_bouquet)
    
    async with aiofiles.open(f"{DATA_DIR}/bouquets.yaml", "w", encoding="utf-8") as f:
        await f.write(yaml.dump({'bouquets': bouquets}, allow_unicode=True))
    
    return bouquet_id

async def update_bouquet(bouquet_id: str, updates: Dict):
    # Обновить данные существующего букета
    bouquets = await get_bouquets()
    
    for bouquet in bouquets:
        if bouquet['id'] == bouquet_id:
            bouquet.update(updates)
            break
    
    async with aiofiles.open(f"{DATA_DIR}/bouquets.yaml", "w", encoding="utf-8") as f:
        await f.write(yaml.dump({'bouquets': bouquets}, allow_unicode=True))

async def delete_bouquet_by_id(bouquet_id: str):
    # Удалить букет по ID
    bouquets = await get_bouquets()
    bouquets = [b for b in bouquets if b['id'] != bouquet_id]
    
    async with aiofiles.open(f"{DATA_DIR}/bouquets.yaml", "w", encoding="utf-8") as f:
        await f.write(yaml.dump({'bouquets': bouquets}, allow_unicode=True))

# ============ КОРЗИНА ============

async def get_user_cart(user_id: int) -> List[Dict]:
    # Получить содержимое корзины пользователя
    async with aiofiles.open(f"{DATA_DIR}/carts.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content) or {'carts': {}}
        return data.get('carts', {}).get(str(user_id), [])

async def add_to_cart(user_id: int, item: Dict):
    # Добавить товар в корзину пользователя
    async with aiofiles.open(f"{DATA_DIR}/carts.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content) or {'carts': {}}
    
    if 'carts' not in data:
        data['carts'] = {}
        
    user_id_str = str(user_id)
    if user_id_str not in data['carts']:
        data['carts'][user_id_str] = []
    
    data['carts'][user_id_str].append(item)
    
    async with aiofiles.open(f"{DATA_DIR}/carts.yaml", "w", encoding="utf-8") as f:
        await f.write(yaml.dump(data, allow_unicode=True))

async def remove_from_cart(user_id: int, index: int):
    # Удалить товар из корзины по индексу
    async with aiofiles.open(f"{DATA_DIR}/carts.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content) or {'carts': {}}
    
    user_id_str = str(user_id)
    if user_id_str in data.get('carts', {}) and 0 <= index < len(data['carts'][user_id_str]):
        data['carts'][user_id_str].pop(index)
    
    async with aiofiles.open(f"{DATA_DIR}/carts.yaml", "w", encoding="utf-8") as f:
        await f.write(yaml.dump(data, allow_unicode=True))

async def clear_cart(user_id: int):
    # Очистить всю корзину пользователя
    async with aiofiles.open(f"{DATA_DIR}/carts.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content) or {'carts': {}}
    
    user_id_str = str(user_id)
    if 'carts' in data:
        data['carts'][user_id_str] = []
    
    async with aiofiles.open(f"{DATA_DIR}/carts.yaml", "w", encoding="utf-8") as f:
        await f.write(yaml.dump(data, allow_unicode=True))

# ============ ИЗБРАННОЕ ============

async def get_favorites(user_id: int) -> List[str]:
    # Получить список ID избранных букетов
    async with aiofiles.open(f"{DATA_DIR}/favorites.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content) or {'favorites': {}}
        return data.get('favorites', {}).get(str(user_id), [])

async def toggle_favorite(user_id: int, bouquet_id: str):
    # Добавить или убрать букет из избранного
    async with aiofiles.open(f"{DATA_DIR}/favorites.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content) or {'favorites': {}}
    
    if 'favorites' not in data:
        data['favorites'] = {}
        
    user_id_str = str(user_id)
    if user_id_str not in data['favorites']:
        data['favorites'][user_id_str] = []
    
    if bouquet_id in data['favorites'][user_id_str]:
        data['favorites'][user_id_str].remove(bouquet_id)
    else:
        data['favorites'][user_id_str].append(bouquet_id)
    
    async with aiofiles.open(f"{DATA_DIR}/favorites.yaml", "w", encoding="utf-8") as f:
        await f.write(yaml.dump(data, allow_unicode=True))

# ============ ЗАКАЗЫ ============

async def create_order(user_id: int, user_name: str) -> str:
    # Создать новый заказ на основе корзины
    cart = await get_user_cart(user_id)
    
    order_id = f"order_{int(datetime.now().timestamp())}"
    
    order = {
        'order_id': order_id,
        'user_id': user_id,
        'user_name': user_name,
        'created_at': datetime.now().isoformat(),
        'items': cart,
        'total_order_price': sum(item['total_price'] for item in cart),
        'payment_status': 'pending'
    }
    
    async with aiofiles.open(f"{DATA_DIR}/orders.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content) or {'orders': []}
    
    if 'orders' not in data:
        data['orders'] = []
        
    data['orders'].append(order)
    
    async with aiofiles.open(f"{DATA_DIR}/orders.yaml", "w", encoding="utf-8") as f:
        await f.write(yaml.dump(data, allow_unicode=True))
    
    # Обновляем статистику пользователя
    await update_user_stats(user_id, user_name, order['total_order_price'])
    
    return order_id

async def get_user_orders(user_id: int) -> List[Dict]:
    # Получить историю заказов пользователя
    async with aiofiles.open(f"{DATA_DIR}/orders.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content) or {'orders': []}
        return [o for o in data.get('orders', []) if o['user_id'] == user_id]

async def get_all_orders(limit: int = 50) -> List[Dict]:
    # Получить все заказы (для админа)
    async with aiofiles.open(f"{DATA_DIR}/orders.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content) or {'orders': []}
        return data.get('orders', [])[-limit:]

async def update_order_status(order_id: str, status: str):
    # Обновить статус оплаты заказа
    async with aiofiles.open(f"{DATA_DIR}/orders.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content) or {'orders': []}
    
    for order in data.get('orders', []):
        if order['order_id'] == order_id:
            order['payment_status'] = status
            break
            
    async with aiofiles.open(f"{DATA_DIR}/orders.yaml", "w", encoding="utf-8") as f:
        await f.write(yaml.dump(data, allow_unicode=True))

# ============ ПОЛЬЗОВАТЕЛИ ============

async def update_user_stats(user_id: int, username: str, amount: int):
    # Обновить статистику пользователя после заказа
    async with aiofiles.open(f"{DATA_DIR}/users.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content) or {'users': []}
    
    if 'users' not in data:
        data['users'] = []
        
    user_found = False
    for user in data['users']:
        if user['user_id'] == user_id:
            user['total_orders'] += 1
            user['total_spent'] += amount
            user_found = True
            break
            
    if not user_found:
        data['users'].append({
            'user_id': user_id,
            'username': username,
            'registered_at': datetime.now().isoformat(),
            'total_orders': 1,
            'total_spent': amount
        })
        
    async with aiofiles.open(f"{DATA_DIR}/users.yaml", "w", encoding="utf-8") as f:
        await f.write(yaml.dump(data, allow_unicode=True))

async def ensure_user_exists(user_id: int, username: str, first_name: str, last_name: str = ""):

    async def ensure_user_exists(user_id: int, username: str, first_name: str, last_name: str = ""):
    file_path = f"{DATA_DIR}/users.yaml"

    # 1. Проверяем, существует ли папка data. Если нет — создаем.
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # 2. Проверяем, существует ли файл users.yaml. Если нет — создаем пустой.
    if not os.path.exists(file_path):
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(yaml.dump({'users': []}))

    # 3. Теперь, когда файл точно есть, открываем его для чтения (твоя 271 строка)
    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content) or {'users': []}
        
    # Проверить существование пользователя и добавить если нет
    async with aiofiles.open(f"{DATA_DIR}/users.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content) or {'users': []}
        
    if 'users' not in data:
        data['users'] = []
    
    if not any(u['user_id'] == user_id for u in data['users']):
        data['users'].append({
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'registered_at': datetime.now().isoformat(),
            'total_orders': 0,
            'total_spent': 0
        })
        
        async with aiofiles.open(f"{DATA_DIR}/users.yaml", "w", encoding="utf-8") as f:
            await f.write(yaml.dump(data, allow_unicode=True))

# ============ АДМИНЫ ============

async def is_admin(user_id: int) -> bool:
    # Проверка прав администратора
    async with aiofiles.open(f"{DATA_DIR}/admins.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        data = yaml.safe_load(content)
        return user_id in data.get('admins', [])

# ============ СТАТИСТИКА ============

async def get_statistics() -> Dict:
    # Сбор общей статистики для админ-панели
    # Пользователи
    async with aiofiles.open(f"{DATA_DIR}/users.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        users_data = yaml.safe_load(content) or {'users': []}
        total_users = len(users_data.get('users', []))
    
    # Заказы
    async with aiofiles.open(f"{DATA_DIR}/orders.yaml", "r", encoding="utf-8") as f:
        content = await f.read()
        orders_data = yaml.safe_load(content) or {'orders': []}
        orders = orders_data.get('orders', [])
        
        total_orders = len(orders)
        total_revenue = sum(o['total_order_price'] for o in orders)
        
        # Сегодняшние заказы
        today = datetime.now().date()
        today_orders = [o for o in orders if datetime.fromisoformat(o['created_at']).date() == today]
        today_count = len(today_orders)
        today_revenue = sum(o['total_order_price'] for o in today_orders)
    
    # Букеты
    bouquets = await get_bouquets()
    total_bouquets = len(bouquets)
    popular_bouquets = sum(1 for b in bouquets if b['is_popular'])
    
    return {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'today_orders': today_count,
        'today_revenue': today_revenue,
        'total_bouquets': total_bouquets,
        'popular_bouquets': popular_bouquets
    }
