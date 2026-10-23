"""Career paths, career recommendations and learning resources."""
from flask import Blueprint, g, request

from ..auth.decorators import login_required
from ..ml.skill_extraction.taxonomy import canonical_skill
from ..models import career_model
from ..services import career_service
from ..utils.responses import success
from ..utils.serialization import rows_to_list
from ..utils.validation import bool_value, clean_str, int_arg

bp = Blueprint("careers", __name__, url_prefix="/api")


@bp.get("/careers")
@login_required
def list_careers():
    return success({"items": career_service.list_careers()})


@bp.get("/careers/<int:career_id>")
@login_required
def career_detail(career_id):
    return success(career_service.career_detail(g.user["user_id"], career_id))


@bp.get("/career-recommendations")
@login_required
def career_recommendations():
    refresh = bool(bool_value(request.args.get("refresh")))
    return success(career_service.get_recommendations(g.user["user_id"], refresh=refresh))


@bp.get("/learning-resources")
@login_required
def learning_resources():
    rows, total = career_model.list_resources(
        skill=canonical_skill(clean_str(request.args.get("skill"), 80, "skill")) if request.args.get("skill") else "",
        search=clean_str(request.args.get("q"), 80, "q"),
        limit=int_arg("limit", 200, 1, 500), offset=int_arg("offset", 0, 0))
    return success({"items": rows_to_list(rows), "total": total, "skills": career_model.resource_skills()})


@bp.get("/learning-resources/<path:skill>")
@login_required
def learning_resources_for_skill(skill):
    name = canonical_skill(clean_str(skill, 80, "skill", required=True))
    rows, total = career_model.list_resources(skill=name)
    return success({"skill": name, "items": rows_to_list(rows), "total": total})
