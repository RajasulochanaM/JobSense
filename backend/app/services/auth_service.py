"""Registration, login and logout."""
import logging

from flask import current_app

from ..auth.security import expiry, hash_password, hash_token, new_token, verify_password
from ..models import user_model
from ..utils.responses import APIError, ValidationError
from ..utils.serialization import row_to_dict
from ..utils.validation import clean_str, validate_email, validate_password

logger = logging.getLogger(__name__)

# Used to equalise timing when the email does not exist (prevents user enumeration by timing).
_DUMMY_HASH = hash_password("dummy-password-for-timing-1")


def public_user(user):
    data = row_to_dict(user, exclude=("password_hash",))
    avatar = user_model.get_avatar(user["user_id"])
    data["avatar_image"] = avatar.get("avatar_image")
    data["avatar_color"] = avatar.get("avatar_color")
    return data


def _issue_token(user_id):
    token = new_token()
    user_model.create_session(user_id, hash_token(token), expiry(current_app.config["TOKEN_TTL_HOURS"]))
    return token


def register(data):
    name = clean_str(data.get("name"), 120, "name", required=True)
    if len(name) < 2:
        raise ValidationError("Name must be at least 2 characters", {"name": "too_short"})
    email = validate_email(data.get("email"))
    password = validate_password(data.get("password"))
    confirm = data.get("password_confirmation", data.get("confirm_password"))
    if confirm is None or confirm != password:
        raise ValidationError("Passwords do not match", {"password_confirmation": "mismatch"})
    if user_model.email_exists(email):
        raise APIError("An account with this email already exists", "EMAIL_TAKEN", 409)

    # Role is never taken from the request: every self-registered user is a candidate.
    user_id = user_model.create_user(name, email, hash_password(password), "candidate")
    logger.info("New candidate registered (user_id=%s)", user_id)
    token = _issue_token(user_id)
    return {"token": token, "user": public_user(user_model.get_by_id(user_id))}


def login(data):
    email = clean_str(data.get("email"), 255, "email", required=True).lower()
    password = data.get("password") or ""
    if not isinstance(password, str) or not password:
        raise ValidationError("Password is required", {"password": "required"})

    user = user_model.get_by_email_with_hash(email)
    if user is None:
        verify_password(_DUMMY_HASH, password)
        raise APIError("Invalid email or password", "INVALID_CREDENTIALS", 401)
    if not verify_password(user["password_hash"], password):
        raise APIError("Invalid email or password", "INVALID_CREDENTIALS", 401)
    if not user["is_active"]:
        raise APIError("This account has been deactivated. Please contact the administrator.",
                       "ACCOUNT_DISABLED", 403)
    token = _issue_token(user["user_id"])
    return {"token": token, "user": public_user(user_model.get_by_id(user["user_id"]))}


def logout(token):
    if token:
        user_model.delete_session(hash_token(token))
