import sqlite3
import os
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "my_database.db")

DEFAULT_PHONE = "Не указан"

# 13) Базовые услуги: добавляются к каждой новой локации автоматически
BASE_SERVICES = [
    ("Оформление салюта", "Организация праздничного салюта", 0),
    ("Декорация", "Оформление зала", 0),
    ("Доп. еда", "Дополнительное меню", 0),
    ("Фотограф", "Фото- и видеосъёмка мероприятия", 0),
    ("Аниматоры", "Развлекательная программа", 0),
    ("Тамада", "Ведущий мероприятия", 0),
]


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    try:
        with connect() as conn:
            cursor = conn.cursor()

            # Локации (площадки): к ним привязываются услуги
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS venues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    capacity INTEGER NOT NULL
                )
            ''')

            # Услуги
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venue_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL DEFAULT 0,
                    contact_phone TEXT NOT NULL DEFAULT 'Не указан',
                    is_base INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE,
                    UNIQUE (venue_id, name)
                )
            ''')
        conn.close()
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())


def service_to_dict(row):
    return {
        "id": row["id"],
        "venue_id": row["venue_id"],
        "name": row["name"],
        "description": row["description"],
        "price": row["price"],
        "contact_phone": row["contact_phone"],
        "is_base": bool(row["is_base"]),
    }


# ==================== ЛОКАЦИИ ====================
def check_venue(venue_id):
    conn = connect()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM venues WHERE id = ?', (venue_id,))
        return cursor.fetchone() is not None
    finally:
        conn.close()


def write_venue(name, address, capacity):
    """Создаёт локацию и сразу добавляет ей базовые услуги (п. 13). Возвращает id локации."""
    conn = connect()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO venues (name, address, capacity) VALUES (?, ?, ?)',
                           (name, address, capacity))
            venue_id = cursor.lastrowid
            add_base_services(venue_id, conn)
        return venue_id
    finally:
        conn.close()


def get_venues():
    conn = connect()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, address, capacity FROM venues ORDER BY id')
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# ==================== БАЗОВЫЕ УСЛУГИ (п. 13) ====================
def add_base_services(venue_id, conn=None):
    """Добавляет локации недостающие базовые услуги. Возвращает, сколько добавлено."""
    own = conn is None
    if own:
        conn = connect()
    try:
        cursor = conn.cursor()
        added = 0
        for name, description, price in BASE_SERVICES:
            cursor.execute('''
                INSERT OR IGNORE INTO services (venue_id, name, description, price, contact_phone, is_base)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (venue_id, name, description, price, DEFAULT_PHONE))
            added += cursor.rowcount
        if own:
            conn.commit()
        return added
    finally:
        if own:
            conn.close()


# ==================== УСЛУГИ (п. 12) ====================
def write_service(venue_id, name, description, price, contact_phone):
    """Возвращает id новой услуги или None, если у локации уже есть услуга с таким названием."""
    conn = connect()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO services (venue_id, name, description, price, contact_phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (venue_id, name, description, price, contact_phone))
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_service(service_id):
    conn = connect()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM services WHERE id = ?', (service_id,))
        row = cursor.fetchone()
        return service_to_dict(row) if row else None
    finally:
        conn.close()


def get_services(venue_id=None):
    conn = connect()
    try:
        cursor = conn.cursor()
        if venue_id is not None:
            cursor.execute('SELECT * FROM services WHERE venue_id = ? ORDER BY id', (venue_id,))
        else:
            cursor.execute('SELECT * FROM services ORDER BY venue_id, id')
        return [service_to_dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def update_service(service_id, name, description, price, contact_phone):
    """True - обновлено, False - услуга не найдена, None - название у этой локации уже занято."""
    conn = connect()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE services
                SET name = ?, description = ?, price = ?, contact_phone = ?
                WHERE id = ?
            ''', (name, description, price, contact_phone, service_id))
            return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def delete_service(service_id):
    conn = connect()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM services WHERE id = ?', (service_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


# ==================== ТЕЛЕФОН ОТВЕТСТВЕННОГО (п. 14) ====================
def update_service_phone(service_id, phone):
    conn = connect()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE services SET contact_phone = ? WHERE id = ?', (phone, service_id))
            return cursor.rowcount > 0
    finally:
        conn.close()


def update_venue_phone(venue_id, phone):
    """Привязывает телефон ответственного ко всем услугам локации. Возвращает, сколько услуг обновлено."""
    conn = connect()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE services SET contact_phone = ? WHERE venue_id = ?', (phone, venue_id))
            return cursor.rowcount
    finally:
        conn.close()


init_db()
