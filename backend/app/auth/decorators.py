"""Route protection decorators: @login_required and @admin_required."""
from functools import wraps

from flask import g, request

from ..models import user_model
from ..utils.responses import error
from .security import hash_token


def _token_from_request():
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


def load_current_user():
    token = _token_from_request()
    if not token or len(token) > 200:
        return None
    user = user_model.get_session_user(hash_token(token))
    if not user or not user["is_active"]:
        return None
    g.token = token
    return user


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = load_current_user()
        if user is None:
            return error("Authentication required. Please log in.", "UNAUTHORIZED", 401)
        g.user = user
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = load_current_user()
        if user is None:
            return error("Authentication required. Please log in.", "UNAUTHORIZED", 401)
        if user["role"] != "admin":
            return error("You do not have permission to access this resource.", "FORBIDDEN", 403)
        g.user = user
        return view(*args, **kwargs)
    return wrapper

