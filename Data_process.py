import os
import json

# File paths
ACCOUNT_FILE = "account.json"
PRODUCT_FILE = "products.json"
CATEGORY_FILE = "product_types.json"
ORDER_FILE = "orders.json"

# ======= COMMON LOAD/SAVE UTILITIES =======
def _load_json(path, default=[]):
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except json.JSONDecodeError:
        pass
    return default

def _save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======= ACCOUNT HANDLING =======
def load_users():
    data = _load_json(ACCOUNT_FILE, {"accounts": []})
    return {acc["username"]: acc for acc in data.get("accounts", [])}

def save_users(users_dict):
    accounts = list(users_dict.values())
    data = {"accounts": accounts}
    _save_json(ACCOUNT_FILE, data)

def get_user_by_username(username):
    users = load_users()
    return users.get(username)

# ======= PRODUCT HANDLING =======
def load_products():
    return _load_json(PRODUCT_FILE, [])

def save_products(products):
    _save_json(PRODUCT_FILE, products)

def get_product_by_id(pid):
    products = load_products()
    return next((p for p in products if p.get("id") == pid), None)

# ======= CATEGORY HANDLING =======
def load_categories():
    return _load_json(CATEGORY_FILE, [])

def save_categories(categories):
    _save_json(CATEGORY_FILE, categories)

def get_category_name_by_id(type_id):
    categories = load_categories()
    return next((c["type_name"] for c in categories if c["type_id"] == type_id), "Không xác định")

# ======= ORDER HANDLING =======
def load_orders():
    return _load_json(ORDER_FILE, [])

def save_orders(orders):
    _save_json(ORDER_FILE, orders)

def get_next_order_id():
    orders = load_orders()
    return max((order["id"] for order in orders), default=0) + 1
