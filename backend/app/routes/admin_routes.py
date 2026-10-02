from flask import Blueprint, g, request

from ..auth.decorators import admin_required
from ..services import admin_service, career_service
from ..utils.responses import ValidationError, success
from ..utils.validation import bool_value, clean_str, get_json, int_arg

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.get("/stats")
@admin_required
def stats():
    return success(admin_service.stats())


@bp.get("/analytics")
@admin_required
def analytics():
    return success(admin_service.analytics())


# ------------------------------------------------------------------- users

@bp.get("/users")
@admin_required
def users():
    return success(admin_service.list_users(
        clean_str(request.args.get("q"), 100, "q"), request.args.get("role", ""),
        int_arg("limit", 20, 1, 100), int_arg("offset", 0, 0)))


@bp.patch("/users/<int:user_id>")
@admin_required
def update_user(user_id):
    data = get_json()
    if "is_active" not in data:
        raise ValidationError("is_active is required")
    user = admin_service.set_user_active(g.user, user_id, bool(bool_value(data["is_active"])))
    return success(user, "User updated")


@bp.delete("/users/<int:user_id>")
@admin_required
def delete_user(user_id):
    admin_service.delete_user(g.user, user_id)
    return success(None, "User deleted")


# ----------------------------------------------------------------- careers

@bp.get("/careers")
@admin_required
def careers():
    return success({"items": career_service.list_careers()})


@bp.post("/careers")
@admin_required
def create_career():
    return success(admin_service.create_career(get_json()), "Career path created", 201)


@bp.put("/careers/<int:career_id>")
@admin_required
def update_career(career_id):
    return success(admin_service.update_career(career_id, get_json()), "Career path updated")


@bp.delete("/careers/<int:career_id>")
@admin_required
def delete_career(career_id):
    admin_service.delete_career(career_id)
    return success(None, "Career path deleted")


# ------------------------------------------------------ learning resources

@bp.post("/learning-resources")
@admin_required
def create_resource():
    return success(admin_service.create_resource(get_json()), "Learning resource created", 201)


@bp.put("/learning-resources/<int:resource_id>")
@admin_required
def update_resource(resource_id):
    return success(admin_service.update_resource(resource_id, get_json()), "Learning resource updated")


@bp.delete("/learning-resources/<int:resource_id>")
@admin_required
def delete_resource(resource_id):
    admin_service.delete_resource(resource_id)
    return success(None, "Learning resource deleted")


# -------------------------------------------------------------------- jobs

@bp.get("/jobs")
@admin_required
def jobs():
    return success(admin_service.list_jobs(
        clean_str(request.args.get("q"), 100, "q"), clean_str(request.args.get("source"), 20, "source"),
        int_arg("limit", 20, 1, 100), int_arg("offset", 0, 0)))


@bp.delete("/jobs/<int:job_id>")
@admin_required
def delete_job(job_id):
    admin_service.delete_job(job_id)
    return success(None, "Job deleted")


@bp.delete("/jobs/mock")
@admin_required
def delete_mock_jobs():
    count = admin_service.delete_mock_jobs()
    return success({"deleted": count}, f"Deleted {count} mock jobs")
