import sqlite3
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "my_database.db")

# Статусы, при которых бронь считается активной (блокирует локацию)
ACTIVE_STATUSES = ("pending", "approved")
CANCELLED_STATUS = "cancelled"


# ==================== ИНИЦИАЛИЗАЦИЯ ====================
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS venues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                description TEXT DEFAULT '',
                contact_phone TEXT DEFAULT ''
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                date TEXT NOT NULL,            -- YYYY-MM-DD
                time_start TEXT NOT NULL,      -- HH:MM
                time_end TEXT NOT NULL,        -- HH:MM
                participants INTEGER NOT NULL,
                total_amount REAL NOT NULL DEFAULT 0,
                comment TEXT DEFAULT '',
                services TEXT DEFAULT '[]',        -- JSON-массив id
                service_configs TEXT DEFAULT '{}', -- JSON-объект
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        ''')

        conn.commit()


# ==================== ХЕЛПЕРЫ ====================
def _row_to_venue(row):
    if not row:
        return None
    return {
        "id": row[0], "name": row[1], "address": row[2],
        "capacity": row[3], "description": row[4] or "",
        "contact_phone": row[5] or "",
    }


def _row_to_event(row):
    if not row:
        return None
    return {
        "id": row[0],
        "client_id": row[1],
        "location_id": row[2],
        "event_type": row[3],
        "date": row[4],
        "time_start": row[5],
        "time_end": row[6],
        "participants": row[7],
        "total_amount": row[8],
        "comment": row[9] or "",
        "services": json.loads(row[10] or "[]"),
        "service_configs": json.loads(row[11] or "{}"),
        "status": row[12],
        "created_at": row[13],
    }


def _time_to_minutes(t: str) -> int:
    """'HH:MM' -> минуты от начала суток."""
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def _times_overlap(s1, e1, s2, e2) -> bool:
    """Пересекаются ли два интервала [start, end)."""
    return _time_to_minutes(s1) < _time_to_minutes(e2) and \
           _time_to_minutes(s2) < _time_to_minutes(e1)


EVENT_SELECT = '''
    SELECT id, client_id, location_id, event_type, date, time_start, time_end,
           participants, total_amount, comment, services, service_configs,
           status, created_at
    FROM events
'''


# ==================== ЛОКАЦИИ ====================
def get_all_venues():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, name, address, capacity, description, contact_phone FROM venues')
        return [_row_to_venue(r) for r in cur.fetchall()]


def get_venue(venue_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, name, address, capacity, description, contact_phone FROM venues WHERE id = ?', (venue_id,))
        return _row_to_venue(cur.fetchone())


def get_free_venues(date_str: str, participants: int):
    """
    Локации, у которых capacity >= participants и которые не заняты
    активной бронью, пересекающейся по времени в указанную дату.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        # Все активные брони на этот день
        cur.execute('''
            SELECT location_id, time_start, time_end
            FROM events
            WHERE date = ? AND status IN (?, ?)
        ''', (date_str, *ACTIVE_STATUSES))
        busy = cur.fetchall()

        cur.execute('''
            SELECT id, name, address, capacity, description, contact_phone
            FROM venues WHERE capacity >= ?
        ''', (participants,))
        venues = [_row_to_venue(r) for r in cur.fetchall()]

    # Для "свободных на дату" считаем локацию занятой, если на неё есть
    # хоть одна активная бронь в этот день (полная блокировка дня).
    busy_ids = {b[0] for b in busy}
    return [v for v in venues if v["id"] not in busy_ids]


def create_venue(name, address, capacity, description="", contact_phone=""):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO venues (name, address, capacity, description, contact_phone)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, address, capacity, description, contact_phone))
        return cur.lastrowid


def update_venue(venue_id, name, address, capacity, description="", contact_phone=""):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('''
            UPDATE venues
            SET name = ?, address = ?, capacity = ?, description = ?, contact_phone = ?
            WHERE id = ?
        ''', (name, address, capacity, description, contact_phone, venue_id))
        return cur.rowcount > 0


def delete_venue(venue_id):
    """Нельзя удалить локацию, если есть активные брони (pending/approved)."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM venues WHERE id = ?', (venue_id,))
        if not cur.fetchone():
            return False

        cur.execute('''
            SELECT 1 FROM events
            WHERE location_id = ? AND status IN (?, ?)
        ''', (venue_id, *ACTIVE_STATUSES))
        if cur.fetchone():
            return False  # есть активные брони

        cur.execute('DELETE FROM venues WHERE id = ?', (venue_id,))
        return True


# ==================== ДОСТУПНОСТЬ ЛОКАЦИИ ====================
def get_busy_slots(location_id, date_str, exclude_event_id=None):
    """Активные брони локации на дату (без данных клиентов)."""
    query = '''
        SELECT id, time_start, time_end, status FROM events
        WHERE location_id = ? AND date = ? AND status IN (?, ?)
    '''
    params = [location_id, date_str, *ACTIVE_STATUSES]
    if exclude_event_id is not None:
        query += " AND id != ?"
        params.append(exclude_event_id)
    query += " ORDER BY time_start"
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return [{"event_id": r[0], "time_start": r[1], "time_end": r[2], "status": r[3]}
                for r in cur.fetchall()]


def is_venue_free(location_id, date_str, time_start, time_end, exclude_event_id=None) -> bool:
    """Свободна ли локация в интервале [time_start, time_end) на дату."""
    for slot in get_busy_slots(location_id, date_str, exclude_event_id):
        if _times_overlap(time_start, time_end, slot["time_start"], slot["time_end"]):
            return False
    return True


def check_event_slot(location_id, date_str, time_start, time_end, participants,
                     exclude_event_id=None):
    """
    Общая проверка брони: локация есть, время корректно, вместимость
    достаточна, интервал не пересекается с активными бронями.
    Возвращает (ok: bool, error: str|None).
    """
    venue = get_venue(location_id)
    if not venue:
        return False, "Локация не найдена"
    try:
        if _time_to_minutes(time_start) >= _time_to_minutes(time_end):
            return False, "Время окончания должно быть позже времени начала"
    except (ValueError, AttributeError):
        return False, "Время должно быть в формате HH:MM"
    if venue["capacity"] < participants:
        return False, "Вместимость локации меньше числа участников"
    if not is_venue_free(location_id, date_str, time_start, time_end, exclude_event_id):
        return False, "Локация занята в это время"
    return True, None


# ==================== МЕРОПРИЯТИЯ ====================
def create_event(client_id, location_id, event_type, date_str, time_start,
                 time_end, participants, total_amount, comment="",
                 services=None, service_configs=None):
    """
    Возвращает (ok: bool, result: int|str).
    ok=True -> result = новый id
    ok=False -> result = текст ошибки
    """
    services = services or []
    service_configs = service_configs or {}

    ok, err = check_event_slot(location_id, date_str, time_start, time_end, participants)
    if not ok:
        return False, err

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO events
            (client_id, location_id, event_type, date, time_start, time_end,
             participants, total_amount, comment, services, service_configs,
             status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        ''', (
            client_id, location_id, event_type, date_str, time_start, time_end,
            participants, total_amount, comment,
            json.dumps(services), json.dumps(service_configs),
            datetime.utcnow().isoformat(),
        ))
        return True, cur.lastrowid


def get_event(event_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(EVENT_SELECT + ' WHERE id = ?', (event_id,))
        return _row_to_event(cur.fetchone())


# Поля, по которым разрешена сортировка (белый список — защита от SQL-инъекций)
EVENT_SORT_FIELDS = ("id", "date", "created_at", "participants", "total_amount", "status")


def get_events(client_id=None, status_filter=None, sort_by="id", order="asc"):
    query = EVENT_SELECT
    clauses, params = [], []
    if client_id is not None:
        clauses.append("client_id = ?")
        params.append(client_id)
    if status_filter is not None:
        clauses.append("status = ?")
        params.append(status_filter)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    if sort_by not in EVENT_SORT_FIELDS:
        sort_by = "id"
    direction = "DESC" if str(order).lower() == "desc" else "ASC"
    query += f" ORDER BY {sort_by} {direction}"
    if sort_by == "date":
        query += f", time_start {direction}"

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return [_row_to_event(r) for r in cur.fetchall()]


def update_event(event_id, data: dict):
    """
    data — словарь уже в терминах БД (date уже строка, ключи — колонки).
    Допустимые поля: event_type, date, time_start, time_end, participants,
    total_amount, comment, services, service_configs.
    """
    if not get_event(event_id):
        return False

    # JSON-поля кодируем
    if "services" in data:
        data["services"] = json.dumps(data["services"])
    if "service_configs" in data:
        data["service_configs"] = json.dumps(data["service_configs"])

    allowed = {"event_type", "date", "time_start", "time_end", "participants",
               "total_amount", "comment", "services", "service_configs"}
    data = {k: v for k, v in data.items() if k in allowed}
    if not data:
        return True  # нечего обновлять — считаем успехом

    set_clause = ", ".join(f"{k} = ?" for k in data)
    values = list(data.values()) + [event_id]

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(f'UPDATE events SET {set_clause} WHERE id = ?', values)
        return True


def update_event_status(event_id, new_status):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('UPDATE events SET status = ? WHERE id = ?', (new_status, event_id))
        return cur.rowcount > 0


def cancel_event(event_id):
    """
    Отмена мероприятия: статус -> cancelled. Бронь площадки снимается
    автоматически, т.к. cancelled не входит в ACTIVE_STATUSES.
    Возвращает (ok: bool, error: str|None).
    """
    event = get_event(event_id)
    if not event:
        return False, "Мероприятие не найдено"
    if event["status"] not in ACTIVE_STATUSES:
        return False, f"Нельзя отменить мероприятие в статусе '{event['status']}'"
    update_event_status(event_id, CANCELLED_STATUS)
    return True, None


def delete_event(event_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM events WHERE id = ?', (event_id,))
        return cur.rowcount > 0


init_db()
