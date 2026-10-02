from flask import Blueprint, g, request

from ..auth.decorators import login_required
from ..services import career_service, matching_service
from ..utils.responses import success
from ..utils.validation import bool_value, get_json, int_arg

bp = Blueprint("matches", __name__, url_prefix="/api/matches")


@bp.get("")
@login_required
def list_matches():
    sort = "newest" if request.args.get("sort") == "newest" else "score"
    result = matching_service.list_matches(
        g.user["user_id"], sort=sort, limit=int_arg("limit", 10, 1, 50), offset=int_arg("offset", 0, 0),
        min_score=int_arg("min_score", 0, 0, 100))
    return success(result)


@bp.post("/refresh")
@login_required
def refresh():
    fetch = bool_value(get_json().get("fetch"))
    result = matching_service.refresh_matches(g.user["user_id"], fetch=bool(fetch))
    message = f"Scored {result['scored_jobs']} jobs"
    if result.get("fetch_error"):
        message += f" (new jobs could not be fetched: {result['fetch_error']})"
    return success(result, message)


@bp.get("/<int:job_id>")
@login_required
def match_detail(job_id):
    detail = matching_service.match_detail(g.user["user_id"], job_id)
    missing = (detail["match"] or {}).get("missing_skills", [])
    detail["learning_resources"] = career_service.resources_grouped(missing)
    return success(detail)
