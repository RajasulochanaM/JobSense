"""Helpers to turn DB rows into JSON-safe dicts."""
import json
from datetime import date, datetime
from decimal import Decimal


def to_json_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    return value


def row_to_dict(row, exclude=()):
    if row is None:
        return None
    return {k: to_json_value(v) for k, v in row.items() if k not in exclude}


def rows_to_list(rows, exclude=()):
    return [row_to_dict(r, exclude) for r in rows]


def load_json_list(value):
    """Parse a JSON array column; tolerates NULL, lists and malformed values."""
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (TypeError, ValueError):
        return []


def dump_json(value):
    return json.dumps(value or [], ensure_ascii=False)
