import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "my_database.db")

# 13) Базовый список услуг для автодобавления
BASE_SERVICES = [
    "оформление салюта",
    "декорация",
    "доп. еда",
    "фотографы",
    "аниматоры",
    "тамада"
]

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Таблица локаций (площадок) - нужна для привязки услуг
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS venues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                capacity INTEGER NOT NULL
            )
        ''')
        
        # Таблица услуг
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venue_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL DEFAULT 0.0,
                contact_phone TEXT,     -- 14) Контактный номер ответственного лица
                FOREIGN KEY (venue_id) REFERENCES venues(id)
            )
        ''')

# ==================== ЛОКАЦИИ ====================
def create_venue(name, address, capacity):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO venues (name, address, capacity) VALUES (?, ?, ?)', 
            (name, address, capacity)
        )
        venue_id = cursor.lastrowid
        
    # 13) Автоматическое добавление базовых услуг при создании локации
    add_base_services(venue_id)
    return venue_id

def get_venues():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, address, capacity FROM venues')
        return [{"id": r[0], "name": r[1], "address": r[2], "capacity": r[3]} for r in cursor.fetchall()]

# ==================== УСЛУГИ (CRUD) ====================
def add_base_services(venue_id):
    """13) Автоматическое добавление базовых услуг"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Проверяем, есть ли уже услуги у этой локации, чтобы не дублировать
        cursor.execute('SELECT COUNT(*) FROM services WHERE venue_id = ?', (venue_id,))
        if cursor.fetchone()[0] > 0:
            return False
            
        for name in BASE_SERVICES:
            cursor.execute('''
                INSERT INTO services (venue_id, name, contact_phone)
                VALUES (?, ?, ?)
            ''', (venue_id, name, "Не указан"))
        return True

def create_service(venue_id, name, description, price, contact_phone):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO services (venue_id, name, description, price, contact_phone)
            VALUES (?, ?, ?, ?, ?)
        ''', (venue_id, name, description, price, contact_phone))
        return cursor.lastrowid

def get_services(venue_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if venue_id:
            cursor.execute('SELECT id, venue_id, name, description, price, contact_phone FROM services WHERE venue_id = ?', (venue_id,))
        else:
            cursor.execute('SELECT id, venue_id, name, description, price, contact_phone FROM services')
        
        return [
            {"id": r[0], "venue_id": r[1], "name": r[2], "description": r[3], "price": r[4], "contact_phone": r[5]}
            for r in cursor.fetchall()
        ]

def update_service(service_id, name, description, price, contact_phone):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Проверяем существование
        cursor.execute('SELECT id FROM services WHERE id = ?', (service_id,))
        if not cursor.fetchone():
            return False
            
        cursor.execute('''
            UPDATE services 
            SET name = ?, description = ?, price = ?, contact_phone = ?
            WHERE id = ?
        ''', (name, description, price, contact_phone, service_id))
        return True

def delete_service(service_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM services WHERE id = ?', (service_id,))
        return cursor.rowcount > 0

def update_contact_phone(service_id, phone):
    """14) Отдельный метод для быстрой смены контакта"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE services SET contact_phone = ? WHERE id = ?', (phone, service_id))
        return cursor.rowcount > 0

init_db()