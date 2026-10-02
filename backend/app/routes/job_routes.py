from flask import Blueprint, g, request

from ..auth.decorators import login_required
from ..integrations.jobs import JobSearchParams
from ..models import job_model, tracking_model
from ..services import career_service, job_service, matching_service
from ..services.serializers import job_payload
from ..utils.responses import NotFound, ValidationError, success
from ..utils.validation import bool_value, clean_str, get_json, int_arg

bp = Blueprint("jobs", __name__, url_prefix="/api")

EXPERIENCE_OPTIONS = {"", "no_experience", "under_3_years_experience", "more_than_3_years_experience"}
MAX_EXPERIENCE_YEARS = 50
EMPLOYMENT_OPTIONS = {"", "FULLTIME", "PARTTIME", "CONTRACTOR", "INTERN"}
MAX_SEARCH_PAGE = 20


def _experience_years(value):
    if value in (None, ""):
        return None
    try:
        years = int(value)
    except (TypeError, ValueError):
        raise ValidationError("experience_years must be a whole number", {"experience_years": "invalid"})
    if not 0 <= years <= MAX_EXPERIENCE_YEARS:
        raise ValidationError(f"experience_years must be between 0 and {MAX_EXPERIENCE_YEARS}",
                              {"experience_years": "range"})
    return years


def _experience_bucket(years):
    """Map exact years onto the provider's coarse requirement buckets."""
    if years == 0:
        return "no_experience"
    return "under_3_years_experience" if years < 3 else "more_than_3_years_experience"


def _page(value):
    try:
        return max(1, min(int(value or 1), MAX_SEARCH_PAGE))
    except (TypeError, ValueError):
        return 1


@bp.get("/jobs")
@login_required
def list_jobs():
    """Browse jobs already stored in JobSense (no external API call)."""
    user_id = g.user["user_id"]
    limit = int_arg("limit", 10, 1, 50)
    offset = int_arg("offset", 0, 0)
    rows, total = job_model.list_jobs(
        user_id,
        q=clean_str(request.args.get("q"), 100, "q"),
        location=clean_str(request.args.get("location"), 100, "location"),
        remote=True if bool_value(request.args.get("remote")) else None,
        employment_type=clean_str(request.args.get("employment_type"), 60, "employment_type"),
        limit=limit, offset=offset,
        sort="score" if request.args.get("sort") == "score" else "newest",
        exclude_mock=job_service.hide_mock_jobs(),
    )
    matching_service.ensure_matches(user_id, [r["job_id"] for r in rows])
    rows = job_model.list_jobs_by_ids(user_id, [r["job_id"] for r in rows])
    return success({"items": [job_payload(r) for r in rows], "total": total, "limit": limit, "offset": offset,
                    "source_info": job_service.provider_info()})


@bp.post("/jobs/search")
@login_required
def search_jobs():
    """Search the external job provider, store + score the results and return them ranked."""
    data = get_json()
    query = clean_str(data.get("query"), 100, "query", required=True)
    years = _experience_years(data.get("experience_years"))
    experience = _experience_bucket(years) if years is not None else clean_str(data.get("experience"), 40, "experience")
    employment = clean_str(data.get("employment_type"), 20, "employment_type").upper()
    params = JobSearchParams(
        query=query,
        location=clean_str(data.get("location"), 100, "location"),
        country=(clean_str(data.get("country"), 2, "country") or "in").lower(),
        remote=bool_value(data.get("remote")) or None,
        employment_type=employment if employment in EMPLOYMENT_OPTIONS else "",
        experience=experience if experience in EXPERIENCE_OPTIONS else "",
        max_experience_years=years,
        date_posted=clean_str(data.get("date_posted"), 10, "date_posted") or "all",
        page=_page(data.get("page")),
    )
    job_ids, provider_name, is_mock = job_service.search_provider(params)
    user_id = g.user["user_id"]
    matching_service.ensure_matches(user_id, job_ids)
    items = [job_payload(r) for r in job_model.list_jobs_by_ids(user_id, job_ids)]
    if years is not None:
        # Keep jobs with no stated requirement; drop those asking for more experience than the candidate has.
        items = [j for j in items if j["min_experience_years"] is None or float(j["min_experience_years"]) <= years]
    if data.get("sort") == "score":
        items.sort(key=lambda j: (j["match"] or {}).get("final_score", -1), reverse=True)
    return success({
        "items": items,
        "page": params.page,
        "has_more": bool(job_ids) and params.page < MAX_SEARCH_PAGE,
        "provider": provider_name,
        "is_mock": is_mock,
    }, f"Found {len(items)} jobs")


@bp.get("/jobs/<int:job_id>")
@login_required
def job_detail(job_id):
    user_id = g.user["user_id"]
    row = job_model.get_job(job_id)
    if not row:
        raise NotFound("Job not found")
    detail = matching_service.match_detail(user_id, job_id)
    job = job_payload(row, include_description=True)
    job["match"] = detail["match"]
    job["is_saved"] = tracking_model.is_saved(user_id, job_id)
    application = tracking_model.get_application_for_job(user_id, job_id)
    return success({
        "job": job,
        "explanation": detail["explanation"],
        "profile_ready": detail["profile_ready"],
        "learning_resources": career_service.resources_grouped((detail["match"] or {}).get("missing_skills", [])),
        "application": {"application_id": application["application_id"], "status": application["status"]}
        if application else None,
    })


@bp.get("/jobs/provider")
@login_required
def provider_status():
    return success(job_service.provider_info())
