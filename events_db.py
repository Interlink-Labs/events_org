import sqlite3
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "my_database.db")



def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Площадки (локации) + контактный телефон ответственного (п.14 ТЗ)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS venues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                description TEXT DEFAULT '',
                contact_phone TEXT DEFAULT ''
            )
        ''')

        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                date TEXT NOT NULL,
                time_start TEXT NOT NULL,
                time_end TEXT NOT NULL,
                participants INTEGER NOT NULL,
                total_amount REAL NOT NULL DEFAULT 0,
                comment TEXT DEFAULT '',
                services TEXT DEFAULT '[]',          -- JSON: список id услуг
                service_configs TEXT DEFAULT '{}',   -- JSON: {service_id: config}
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        ''')

        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venue_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL UNIQUE,
                booked_at TEXT NOT NULL
            )
        ''')

        
        cursor.execute('SELECT COUNT(*) FROM venues')
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO venues (name, address, capacity, contact_phone) VALUES (?, ?, ?, ?)",
                ("Зал Гранд", "ул. Центральная, 10", 200, "+7 (900) 000-00-01"),
            )
            cursor.execute(
                "INSERT INTO venues (name, address, capacity, contact_phone) VALUES (?, ?, ?, ?)",
                ("Лофт Кирпич", "пр-т Индустриальный, 25", 80, "+7 (900) 000-00-02"),
            )



def get_all_venues():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM venues ORDER BY id')
        return [dict(row) for row in cursor.fetchall()]


def get_venue(venue_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM venues WHERE id = ?', (venue_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_free_venues(date_str, participants):
    """
    Свободные локации на дату с достаточной вместимостью.
    Отклонённые заявки не считаются занятыми.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM venues
            WHERE capacity >= ?
              AND id NOT IN (
                  SELECT b.venue_id FROM bookings b
                  JOIN events e ON e.id = b.event_id
                  WHERE substr(e.date, 1, 10) = ? AND e.status != 'rejected'
              )
            ORDER BY capacity
        ''', (participants, date_str))
        return [dict(row) for row in cursor.fetchall()]


def create_venue(name, address, capacity, description="", contact_phone=""):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO venues (name, address, capacity, description, contact_phone)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, address, capacity, description, contact_phone))
        return cursor.lastrowid


def update_venue(venue_id, name, address, capacity, description="", contact_phone=""):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE venues
            SET name = ?, address = ?, capacity = ?, description = ?, contact_phone = ?
            WHERE id = ?
        ''', (name, address, capacity, description, contact_phone, venue_id))
        return cursor.rowcount > 0


def delete_venue(venue_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM bookings WHERE venue_id = ?', (venue_id,))
        if cursor.fetchone()[0] > 0:
            return False
        cursor.execute('DELETE FROM venues WHERE id = ?', (venue_id,))
        return cursor.rowcount > 0



def create_event(client_id, location_id, event_type, date_str, time_start, time_end,
                 participants, total_amount, comment="", services=None, service_configs=None):
    """
    Создаёт мероприятие и сразу бронирует локацию.
    Возвращает (ok: bool, result: int | str).
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        
        cursor.execute('SELECT capacity, name FROM venues WHERE id = ?', (location_id,))
        venue = cursor.fetchone()
        if not venue:
            return False, "Локация не найдена"
        capacity, venue_name = venue
        if participants > capacity:
            return False, f"Локация '{venue_name}' вмещает только {capacity} человек"

        
        cursor.execute('''
            SELECT b.id FROM bookings b
            JOIN events e ON e.id = b.event_id
            WHERE b.venue_id = ? AND substr(e.date, 1, 10) = ? AND e.status != 'rejected'
        ''', (location_id, date_str))
        if cursor.fetchone():
            return False, "Локация уже забронирована на эту дату"

        
        cursor.execute('''
            INSERT INTO events (
                client_id, location_id, event_type, date, time_start, time_end,
                participants, total_amount, comment, services, service_configs,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            client_id, location_id, event_type, date_str, time_start, time_end,
            participants, total_amount, comment,
            json.dumps(services or []),
            json.dumps(service_configs or {}),
            "pending",
            datetime.now().isoformat(),
        ))
        event_id = cursor.lastrowid

        
        cursor.execute('''
            INSERT INTO bookings (venue_id, event_id, booked_at)
            VALUES (?, ?, ?)
        ''', (location_id, event_id, datetime.now().isoformat()))

        return True, event_id


def _row_to_event(row):
    """Преобразует sqlite3.Row в dict и расшифровывает JSON-поля."""
    event = dict(row)
    event["services"] = json.loads(event["services"]) if event["services"] else []
    event["service_configs"] = json.loads(event["service_configs"]) if event["service_configs"] else {}
    return event


def get_events(client_id=None, status_filter=None):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = 'SELECT * FROM events WHERE 1=1'
        params = []
        if client_id is not None:
            query += ' AND client_id = ?'
            params.append(client_id)
        if status_filter is not None:
            query += ' AND status = ?'
            params.append(status_filter)
        query += ' ORDER BY created_at DESC'
        cursor.execute(query, params)
        return [_row_to_event(row) for row in cursor.fetchall()]


def get_event(event_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM events WHERE id = ?', (event_id,))
        row = cursor.fetchone()
        return _row_to_event(row) if row else None


def update_event(event_id, data):
    """Частичное обновление мероприятия (передаются только изменённые поля)."""
    allowed = {
        "event_type", "date", "time_start", "time_end",
        "participants", "total_amount", "comment", "services", "service_configs",
    }
    fields, values = [], []
    for key in allowed:
        if key in data:
            fields.append(f"{key} = ?")
            val = data[key]
            if key in ("services", "service_configs"):
                val = json.dumps(val)
            values.append(val)
    if not fields:
        return False
    values.append(event_id)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE events SET {', '.join(fields)} WHERE id = ?", values)
        return cursor.rowcount > 0


def update_event_status(event_id, new_status):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM events WHERE id = ?', (event_id,))
        if not cursor.fetchone():
            return False
        cursor.execute('UPDATE events SET status = ? WHERE id = ?', (new_status, event_id))
        
        if new_status == 'rejected':
            cursor.execute('DELETE FROM bookings WHERE event_id = ?', (event_id,))
        return True


def delete_event(event_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bookings WHERE event_id = ?', (event_id,))
        cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
        return cursor.rowcount > 0


init_db()