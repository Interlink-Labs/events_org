"""In-memory хранилище. При переходе на БД — заменить на репозитории SQLAlchemy."""
from __future__ import annotations

# estimate_id -> estimate
estimates_db: dict[int, dict] = {}

# вспомогательные индексы: event_id -> estimate_id
event_to_estimate: dict[int, int] = {}

# item_id -> item
items_db: dict[int, dict] = {}

# expense_id -> expense
expenses_db: dict[int, dict] = {}

# payment_id -> payment
payments_db: dict[int, dict] = {}

# payment_id -> list[status_log]
payment_logs_db: dict[int, list[dict]] = {}

_counters = {"estimate": 0, "item": 0, "expense": 0, "payment": 0}


def next_id(kind: str) -> int:
    _counters[kind] += 1
    return _counters[kind]