"""Small request-validation helpers (kept dependency free)."""
import re

from flask import request

from .responses import ValidationError

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def get_json():
    data = request.get_json(silent=True)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")
    return data


def clean_str(value, max_len=255, field="value", required=False):
    if value is None:
        value = ""
    if not isinstance(value, (str, int, float)):
        raise ValidationError(f"{field} must be text")
    value = str(value).strip()
    if required and not value:
        raise ValidationError(f"{field} is required", {field: "required"})
    if len(value) > max_len:
        raise ValidationError(f"{field} must be at most {max_len} characters", {field: "too_long"})
    return value


def validate_email(email):
    email = clean_str(email, 255, "email", required=True).lower()
    if not EMAIL_RE.match(email):
        raise ValidationError("Please enter a valid email address", {"email": "invalid"})
    return email


def validate_password(password):
    if not isinstance(password, str) or len(password) < 8:
        raise ValidationError("Password must be at least 8 characters", {"password": "too_short"})
    if len(password) > 128:
        raise ValidationError("Password is too long", {"password": "too_long"})
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ValidationError("Password must contain letters and numbers", {"password": "weak"})
    return password


def int_arg(name, default, minimum=None, maximum=None):
    raw = request.args.get(name)
    try:
        value = int(raw) if raw not in (None, "") else default
    except ValueError:
        raise ValidationError(f"{name} must be an integer")
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def bool_value(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
