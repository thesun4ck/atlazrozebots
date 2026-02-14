import yaml
import os
from datetime import datetime
from typing import List, Dict, Optional

DATA_DIR = "data"

def _ensure_file(filename, default_data):
    """Создать файл если не существует"""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(default_data, f, allow_unicode=True)

def load_yaml(filename):
    """Загрузить YAML файл"""
    filepath = os.path.join(DATA_DIR, filename)
    _ensure_file(filename, {})
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def save_yaml(filename, data):
    """Сохранить в YAML файл"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True)

# ============ БУКЕТЫ ============

def get_bouquets():
    """Получить все букеты"""
    data = load_yaml('bouquets.yaml')
    return data.get('bouquets', [])

def get_bouquet_by_id(bouquet_id):
    """Получить букет по ID"""
    bouquets = get_bouquets()
    for b in bouquets:
        if b['id'] == bouquet_id:
            return b
    return None

def save_bouquet(bouquet):
    """Сохранить новый букет"""
    data = load_yaml('bouquets.yaml')
    if 'bouquets' not in data:
        data['bouquets'] = []
    
    # Генерируем ID
    max_id = 0
    for b in data['bouquets']:
        try:
            bid = int(b['id'].replace('b', ''))
            if bid > max_id:
                max_id = bid
        except:
            pass
    
    bouquet['id'] = f"b{max_id + 1}"
    data['bouquets'].append(bouquet)
    save_yaml('bouquets.yaml', data)
    return bouquet['id']

def update_bouquet(bouquet_id, updates):
    """Обновить букет"""
    data = load_yaml('bouquets.yaml')
    bouquets = data.get('bouquets', [])
    
    for i, b in enumerate(bouquets):
        if b['id'] == bouquet_id:
            bouquets[i].update(updates)
            break
    
    data['bouquets'] = bouquets
    save_yaml('bouquets.yaml', data)

def delete_bouquet(bouquet_id):
    """Удалить букет"""
    data = load_yaml('bouquets.yaml')
    bouquets = [b for b in data.get('bouquets', []) if b['id'] != bouquet_id]
    data['bouquets'] = bouquets
    save_yaml('bouquets.yaml', data)

# ============ КОРЗИНА ============

def get_user_cart(user_id):
    """Получить корзину пользователя"""
    data = load_yaml('carts.yaml')
    carts = data.get('carts', {})
    return carts.get(str(user_id), [])

def add_to_cart(user_id, item):
    """Добавить в корзину"""
    data = load_yaml('carts.yaml')
    if 'carts' not in data:
        data['carts'] = {}
    
    user_key = str(user_id)
    if user_key not in data['carts']:
        data['carts'][user_key] = []
    
    data['carts'][user_key].append(item)
    save_yaml('carts.yaml', data)

def remove_from_cart(user_id, index):
    """Удалить товар из корзины"""
    data = load_yaml('carts.yaml')
    carts = data.get('carts', {})
    user_key = str(user_id)
    
    if user_key in carts and 0 <= index < len(carts[user_key]):
        carts[user_key].pop(index)
        data['carts'] = carts
        save_yaml('carts.yaml', data)

def clear_cart(user_id):
    """Очистить корзину"""
    data = load_yaml('carts.yaml')
    carts = data.get('carts', {})
    carts[str(user_id)] = []
    data['carts'] = carts
    save_yaml('carts.yaml', data)

# ============ ИЗБРАННОЕ ============

def get_favorites(user_id):
    """Получить избранное"""
    data = load_yaml('favorites.yaml')
    favs = data.get('favorites', {})
    return favs.get(str(user_id), [])

def toggle_favorite(user_id, bouquet_id):
    """Добавить/удалить из избранного"""
    data = load_yaml('favorites.yaml')
    if 'favorites' not in data:
        data['favorites'] = {}
    
    user_key = str(user_id)
    if user_key not in data['favorites']:
        data['favorites'][user_key] = []
    
    if bouquet_id in data['favorites'][user_key]:
        data['favorites'][user_key].remove(bouquet_id)
    else:
        data['favorites'][user_key].append(bouquet_id)
    
    save_yaml('favorites.yaml', data)

# ============ ЗАКАЗЫ ============

def create_order(user_id, user_name, items):
    """Создать заказ"""
    data = load_yaml('orders.yaml')
    if 'orders' not in data:
        data['orders'] = []
    
    order = {
        'order_id': f"order_{int(datetime.now().timestamp())}",
        'user_id': user_id,
        'user_name': user_name,
        'created_at': datetime.now().isoformat(),
        'items': items,
        'total_price': sum(item.get('total_price', 0) for item in items),
        'status': 'pending'
    }
    
    data['orders'].append(order)
    save_yaml('orders.yaml', data)
    return order['order_id']

def get_user_orders(user_id):
    """Получить заказы пользователя"""
    data = load_yaml('orders.yaml')
    orders = data.get('orders', [])
    return [o for o in orders if o['user_id'] == user_id]

def get_all_orders():
    """Получить все заказы"""
    data = load_yaml('orders.yaml')
    return data.get('orders', [])

# ============ АДМИНЫ ============

def is_admin(user_id):
    """Проверить админа"""
    data = load_yaml('admins.yaml')
    admins = data.get('admins', [])
    return user_id in admins

# ============ ПОЛЬЗОВАТЕЛИ ============

def save_user(user_id, username, first_name, last_name=""):
    """Сохранить пользователя"""
    data = load_yaml('users.yaml')
    if 'users' not in data:
        data['users'] = []
    
    # Проверяем существует ли
    for u in data['users']:
        if u['user_id'] == user_id:
            return
    
    user = {
        'user_id': user_id,
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'registered_at': datetime.now().isoformat()
    }
    
    data['users'].append(user)
    save_yaml('users.yaml', data)

def get_stats():
    """Получить статистику"""
    orders = get_all_orders()
    bouquets = get_bouquets()
    users_data = load_yaml('users.yaml')
    
    total_orders = len(orders)
    total_revenue = sum(o['total_price'] for o in orders)
    total_users = len(users_data.get('users', []))
    total_bouquets = len(bouquets)
    
    # Сегодняшние заказы
    today = datetime.now().date()
    today_orders = [o for o in orders if datetime.fromisoformat(o['created_at']).date() == today]
    today_count = len(today_orders)
    today_revenue = sum(o['total_price'] for o in today_orders)
    
    return {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_users': total_users,
        'total_bouquets': total_bouquets,
        'today_orders': today_count,
        'today_revenue': today_revenue
    }
