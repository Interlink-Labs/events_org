import sqlite3
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "my_database.db")

# ==================== ИНИЦИАЛИЗАЦИЯ БД ====================
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Площадки (локации)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS venues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                description TEXT
            )
        ''')

        # Мероприятия (поля подстроены под твой фронтенд)
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
                total_amount REAL NOT NULL,
                comment TEXT,
                services TEXT,          -- JSON строка
                service_configs TEXT,   -- JSON строка
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
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
        
        # Добавим пару тестовых локаций, если таблица пустая
        cursor.execute('SELECT COUNT(*) FROM venues')
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO venues (name, address, capacity) VALUES (?, ?, ?)", ("Зал Гранд", "ул. Центральная, 10", 200))
            cursor.execute("INSERT INTO venues (name, address, capacity) VALUES (?, ?, ?)", ("Лофт Кирпич", "пр-т Индустриальный, 25", 80))

# ==================== МЕРОПРИЯТИЯ И БРОНИРОВАНИЕ ====================
def create_event_db(data: dict):
    """Создает мероприятие и сразу бронирует локацию (если свободна)"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Проверка: существует ли локация и хватает ли мест
        cursor.execute('SELECT capacity, name FROM venues WHERE id = ?', (data["location_id"],))
        venue = cursor.fetchone()
        if not venue:
            return {"ok": False, "error": "Локация не найдена"}
        
        capacity, venue_name = venue
        if data["participants"] > capacity:
            return {"ok": False, "error": f"Локация '{venue_name}' вмещает только {capacity} человек"}

        # 2. Проверка: свободна ли локация на эту дату
        cursor.execute('''
            SELECT b.id FROM bookings b
            JOIN events e ON e.id = b.event_id
            WHERE b.venue_id = ? AND substr(e.date, 1, 10) = ?
        ''', (data["location_id"], data["date"]))
        if cursor.fetchone():
            return {"ok": False, "error": "Локация уже забронирована на эту дату"}

        # 3. Создаем мероприятие
        cursor.execute('''
            INSERT INTO events (
                client_id, location_id, event_type, date, time_start, time_end, 
                participants, total_amount, comment, services, service_configs, 
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data["client_id"], data["location_id"], data["event_type"], data["date"],
            data["time_start"], data["time_end"], data["participants"], data["total_amount"],
            data.get("comment", ""), 
            json.dumps(data.get("services", [])), 
            json.dumps(data.get("service_configs", {})),
            "pending", # По умолчанию
            datetime.now().isoformat()
        ))
        event_id = cursor.lastrowid

        # 4. Создаем бронь
        cursor.execute('''
            INSERT INTO bookings (venue_id, event_id, booked_at)
            VALUES (?, ?, ?)
        ''', (data["location_id"], event_id, datetime.now().isoformat()))

        return {"ok": True, "event_id": event_id}


def get_events_db(client_id: int = None, status_filter: str = None):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM events WHERE 1=1'
        params = []
        
        if client_id:
            query += ' AND client_id = ?'
            params.append(client_id)
        if status_filter:
            query += ' AND status = ?'
            params.append(status_filter)
            
        query += ' ORDER BY created_at DESC'
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Преобразуем в список словарей и расшифровываем JSON
        result = []
        for row in rows:
            event = dict(row)
            event["services"] = json.loads(event["services"]) if event["services"] else []
            event["service_configs"] = json.loads(event["service_configs"]) if event["service_configs"] else {}
            result.append(event)
        return result


def update_status_db(event_id: int, new_status: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE events SET status = ? WHERE id = ?', (new_status, event_id))
        return cursor.rowcount > 0


def delete_event_db(event_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bookings WHERE event_id = ?', (event_id,))
        cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
        return cursor.rowcount > 0

# Инициализируем базу при импорте файла
init_db()