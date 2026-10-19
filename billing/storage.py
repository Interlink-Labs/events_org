estimates_db = {}
event_to_estimate = {}
items_db = {}
expenses_db = {}
payments_db = {}
_counters = {"estimate": 0, "item": 0, "expense": 0, "payment": 0}

def next_id(kind: str) -> int:
    _counters[kind] += 1
    return _counters[kind]