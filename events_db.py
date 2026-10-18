import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "my_database.db")


# ==================== ИНИЦИАЛИЗАЦИЯ БД ====================
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Площадки
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS venues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                description TEXT
            )
        ''')

        # Мероприятия
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL,        -- ISO: YYYY-MM-DDTHH:MM:SS
                location TEXT NOT NULL,
                participants_count INTEGER NOT NULL,
                venue_id INTEGER
            )
        ''')

        # Брони
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venue_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL UNIQUE,
                booked_at TEXT NOT NULL
            )
        ''')


# ==================== ПЛОЩАДКИ ====================
def create_venue(name, address, capacity, description=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO venues (name, address, capacity, description)
            VALUES (?, ?, ?, ?)
        ''', (name, address, capacity, description))
        return cursor.lastrowid


def get_venue(venue_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, address, capacity, description FROM venues WHERE id = ?', (venue_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0], "name": row[1], "address": row[2],
                "capacity": row[3], "description": row[4]
            }
        return None


def list_venues():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, address, capacity, description FROM venues')
        return [
            {"id": r[0], "name": r[1], "address": r[2], "capacity": r[3], "description": r[4]}
            for r in cursor.fetchall()
        ]


# ==================== МЕРОПРИЯТИЯ (CRUD) ====================
def create_event(title, date, location, participants_count, description=None, venue_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO events (title, description, date, location, participants_count, venue_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, date, location, participants_count, venue_id))
        return cursor.lastrowid


def get_event(event_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, description, date, location, participants_count, venue_id
            FROM events WHERE id = ?
        ''', (event_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0], "title": row[1], "description": row[2],
                "date": row[3], "location": row[4],
                "participants_count": row[5], "venue_id": row[6]
            }
        return None


def list_events():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, description, date, location, participants_count, venue_id
            FROM events
        ''')
        return [
            {"id": r[0], "title": r[1], "description": r[2], "date": r[3],
             "location": r[4], "participants_count": r[5], "venue_id": r[6]}
            for r in cursor.fetchall()
        ]


def update_event(event_id, **fields):
    event = get_event(event_id)
    if not event:
        return False

    allowed = {"title", "description", "date", "location", "participants_count", "venue_id"}
    fields = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not fields:
        return False

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [event_id]

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'UPDATE events SET {set_clause} WHERE id = ?', values)
        return True


def delete_event(event_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bookings WHERE event_id = ?', (event_id,))
        cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
        return cursor.rowcount > 0


# ==================== ПОДБОР ПЛОЩАДКИ ====================
def find_suitable_venues(participants_count, event_date):
    """
    event_date: ISO-строка 'YYYY-MM-DDTHH:MM:SS'
    Возвращает площадки, где capacity >= participants_count
    и которые НЕ заняты на этот день.
    """
    day = event_date[:10]  # берём YYYY-MM-DD
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Занятые площадки в этот день
        cursor.execute('''
            SELECT b.venue_id
            FROM bookings b
            JOIN events e ON e.id = b.event_id
            WHERE substr(e.date, 1, 10) = ?
        ''', (day,))
        busy_ids = {row[0] for row in cursor.fetchall()}

        cursor.execute('SELECT id, name, address, capacity, description FROM venues WHERE capacity >= ?', (participants_count,))
        venues = cursor.fetchall()

    return [
        {"id": r[0], "name": r[1], "address": r[2], "capacity": r[3], "description": r[4]}
        for r in venues if r[0] not in busy_ids
    ]


# ==================== БРОНИРОВАНИЕ ====================
def book_venue(event_id, venue_id):
    """Создаёт бронь. Проверяет вместимость и конфликт по дате."""
    event = get_event(event_id)
    if not event:
        return {"ok": False, "error": "Мероприятие не найдено"}

    venue = get_venue(venue_id)
    if not venue:
        return {"ok": False, "error": "Площадка не найдена"}

    if venue["capacity"] < event["participants_count"]:
        return {"ok": False, "error": "Площадка слишком мала для такого количества участников"}

    day = event["date"][:10]
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Уже есть бронь у мероприятия?
        cursor.execute('SELECT id FROM bookings WHERE event_id = ?', (event_id,))
        if cursor.fetchone():
            return {"ok": False, "error": "Мероприятие уже забронировано"}

        # Площадка занята в этот день?
        cursor.execute('''
            SELECT b.id FROM bookings b
            JOIN events e ON e.id = b.event_id
            WHERE b.venue_id = ? AND substr(e.date, 1, 10) = ?
        ''', (venue_id, day))
        if cursor.fetchone():
            return {"ok": False, "error": "Площадка уже забронирована на эту дату"}

        cursor.execute('''
            INSERT INTO bookings (venue_id, event_id, booked_at)
            VALUES (?, ?, ?)
        ''', (venue_id, event_id, datetime.utcnow().isoformat()))

        cursor.execute('UPDATE events SET venue_id = ? WHERE id = ?', (venue_id, event_id))

        return {"ok": True, "booking_id": cursor.lastrowid}


def get_booking(event_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, venue_id, event_id, booked_at
            FROM bookings WHERE event_id = ?
        ''', (event_id,))
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "venue_id": row[1], "event_id": row[2], "booked_at": row[3]}
        return None


init_db()