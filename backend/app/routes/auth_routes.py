from flask import Blueprint, g

from ..auth.decorators import login_required
from ..services import auth_service
from ..utils.responses import success
from ..utils.validation import get_json

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    result = auth_service.register(get_json())
    return success(result, "Account created successfully", 201)


@bp.post("/login")
def login():
    result = auth_service.login(get_json())
    return success(result, "Logged in successfully")


@bp.post("/logout")
@login_required
def logout():
    auth_service.logout(g.get("token"))
    return success(None, "Logged out")


@bp.get("/me")
@login_required
def me():
    return success({"user": auth_service.public_user(g.user)})
