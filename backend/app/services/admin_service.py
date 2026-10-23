"""Administrative management and analytics."""
from collections import Counter
from urllib.parse import urlparse

from ..database.db import DatabaseError
from ..config.settings import APPLICATION_STATUSES, INTEREST_OPTIONS
from ..ml.skill_extraction.taxonomy import canonical_skill
from ..models import analytics_model, career_model, job_model, tracking_model, user_model
from ..utils.responses import APIError, NotFound, ValidationError
from ..utils.serialization import load_json_list, row_to_dict, rows_to_list
from ..utils.validation import clean_str
from .serializers import job_payload

RESOURCE_TYPES = ("documentation", "tutorial", "course", "reference", "guide")


def stats():
    return row_to_dict(analytics_model.overview_counts())


def analytics():
    missing = Counter()
    for r in analytics_model.all_missing_skill_rows():
        missing.update(load_json_list(r["missing_skills"]))
    status = {r["status"]: r["n"] for r in tracking_model.application_status_counts()}
    return {
        "top_candidate_skills": [{"skill": r["skill_name"], "count": r["n"]}
                                 for r in analytics_model.top_candidate_skills(12)],
        "top_missing_skills": [{"skill": s, "count": n} for s, n in missing.most_common(12)],
        "application_status": [{"status": s, "count": status.get(s, 0)} for s in APPLICATION_STATUSES],
        "match_statistics": row_to_dict(analytics_model.match_statistics()),
        "jobs_by_source": rows_to_list(analytics_model.jobs_by_source()),
        "signups_by_month": list(reversed(rows_to_list(analytics_model.signups_by_month()))),
    }


# ------------------------------------------------------------------- users

def list_users(search, role, limit, offset):
    rows, total = user_model.list_users(search, role, limit, offset)
    items = rows_to_list(rows)
    for item in items:
        item["is_active"] = bool(item["is_active"])
    return {"items": items, "total": total, "limit": limit, "offset": offset}


def set_user_active(admin, user_id, active):
    if user_id == admin["user_id"]:
        raise APIError("You cannot deactivate your own account", "INVALID_OPERATION", 400)
    if not user_model.get_by_id(user_id):
        raise NotFound("User not found")
    user_model.set_active(user_id, active)
    return row_to_dict(user_model.get_by_id(user_id))


def delete_user(admin, user_id):
    if user_id == admin["user_id"]:
        raise APIError("You cannot delete your own account", "INVALID_OPERATION", 400)
    target = user_model.get_by_id(user_id)
    if not target:
        raise NotFound("User not found")
    if target["role"] == "admin":
        raise APIError("Administrator accounts cannot be deleted here", "INVALID_OPERATION", 400)
    user_model.delete_user(user_id)


# ----------------------------------------------------------------- careers

def _validate_career(data, career_id=None):
    name = clean_str(data.get("career_name"), 120, "career_name", required=True)
    description = clean_str(data.get("description"), 2000, "description", required=True)
    interest = clean_str(data.get("interest_area"), 60, "interest_area") or None
    if interest and interest not in INTEREST_OPTIONS:
        raise ValidationError(f"interest_area must be one of: {', '.join(INTEREST_OPTIONS)}")
    if career_model.career_name_exists(name, career_id):
        raise APIError("A career path with this name already exists", "DUPLICATE", 409)

    skills = None
    if "skills" in data or career_id is None:
        raw = data.get("skills") or []
        if not isinstance(raw, list):
            raise ValidationError("skills must be a list")
        skills, seen = [], set()
        for item in raw:
            if isinstance(item, str):
                item = {"skill_name": item, "importance": 2}
            if not isinstance(item, dict):
                raise ValidationError("Each skill must be an object with skill_name and importance")
            skill = canonical_skill(clean_str(item.get("skill_name"), 80, "skill_name", required=True))
            try:
                importance = int(item.get("importance", 2))
            except (TypeError, ValueError):
                raise ValidationError("importance must be 1, 2 or 3")
            if importance not in (1, 2, 3):
                raise ValidationError("importance must be 1, 2 or 3")
            if skill.lower() not in seen:
                seen.add(skill.lower())
                skills.append({"skill_name": skill, "importance": importance})
    return name, description, interest, skills


def create_career(data):
    name, description, interest, skills = _validate_career(data)
    career = career_model.get_career(career_model.create_career(name, description, interest, skills))
    return row_to_dict(career) | {"skills": rows_to_list(career["skills"])}


def update_career(career_id, data):
    if not career_model.get_career(career_id):
        raise NotFound("Career path not found")
    name, description, interest, skills = _validate_career(data, career_id)
    career_model.update_career(career_id, name, description, interest, skills)
    career = career_model.get_career(career_id)
    return row_to_dict(career) | {"skills": rows_to_list(career["skills"])}


def delete_career(career_id):
    if not career_model.delete_career(career_id):
        raise NotFound("Career path not found")


# ------------------------------------------------------ learning resources

def _validate_resource(data):
    url = clean_str(data.get("resource_url"), 500, "resource_url", required=True)
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValidationError("resource_url must be a valid http(s) URL", {"resource_url": "invalid"})
    rtype = clean_str(data.get("resource_type") or "documentation", 20, "resource_type")
    if rtype not in RESOURCE_TYPES:
        raise ValidationError(f"resource_type must be one of: {', '.join(RESOURCE_TYPES)}")
    return {
        "skill_name": canonical_skill(clean_str(data.get("skill_name"), 80, "skill_name", required=True)),
        "resource_name": clean_str(data.get("resource_name"), 200, "resource_name", required=True),
        "resource_url": url,
        "description": clean_str(data.get("description"), 500, "description") or None,
        "resource_type": rtype,
    }


def create_resource(data):
    fields = _validate_resource(data)
    try:
        resource_id = career_model.create_resource(fields)
    except DatabaseError as exc:  # unique (skill_name, resource_url) violation
        raise APIError("This resource already exists for the skill", "DUPLICATE", 409) from exc
    return row_to_dict(career_model.get_resource(resource_id))


def update_resource(resource_id, data):
    if not career_model.get_resource(resource_id):
        raise NotFound("Learning resource not found")
    career_model.update_resource(resource_id, _validate_resource(data))
    return row_to_dict(career_model.get_resource(resource_id))


def delete_resource(resource_id):
    if not career_model.delete_resource(resource_id):
        raise NotFound("Learning resource not found")


# -------------------------------------------------------------------- jobs

def list_jobs(q, source, limit, offset):
    rows, total = job_model.list_jobs(None, q=q, source=source, limit=limit, offset=offset)
    return {"items": [job_payload(r) for r in rows], "total": total, "limit": limit, "offset": offset}


def delete_job(job_id):
    if not job_model.delete_job(job_id):
        raise NotFound("Job not found")


def delete_mock_jobs():
    return job_model.delete_jobs_by_source("mock")
