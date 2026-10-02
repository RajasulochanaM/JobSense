"""Authentication primitives: Werkzeug password hashing and opaque bearer tokens.

Sessions are server-side: the client holds a random 256-bit token; the DB only
stores its SHA-256 hash, so a leaked database cannot be used to hijack sessions
and logout genuinely revokes the token. Bearer tokens (rather than cookies)
are used because the frontend (Vercel) and API (Render) live on different
domains, where third-party cookies are increasingly blocked by browsers.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    return generate_password_hash(password, method="scrypt")


def verify_password(password_hash, password):
    try:
        return check_password_hash(password_hash, password)
    except (ValueError, TypeError):
        return False


def new_token():
    return secrets.token_urlsafe(32)


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def expiry(hours):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).replace(tzinfo=None)
