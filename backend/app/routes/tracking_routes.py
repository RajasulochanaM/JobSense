"""Saved jobs and application tracking."""
from datetime import date

from flask import Blueprint, g, request

from ..config.settings import APPLICATION_STATUSES
from ..auth.decorators import login_required
from ..models import job_model, tracking_model
from ..services.serializers import match_payload
from ..utils.responses import APIError, NotFound, ValidationError, success
from ..utils.serialization import row_to_dict
from ..utils.validation import clean_str, get_json

bp = Blueprint("tracking", __name__, url_prefix="/api")


def _require_job(job_id):
    if not job_model.get_job(job_id):
        raise NotFound("Job not found")


# ------------------------------------------------------------- saved jobs

@bp.get("/saved-jobs")
@login_required
def list_saved():
    items = []
    for r in tracking_model.list_saved(g.user["user_id"]):
        item = row_to_dict(r, exclude=("matched_skills", "missing_skills", "final_score", "text_similarity",
                                       "skill_match", "calculated_at"))
        item["remote"] = bool(item["remote"])
        item["is_mock"] = item["source"] == "mock"
        item["match"] = match_payload(r)
        items.append(item)
    return success({"items": items, "total": len(items)})


@bp.post("/saved-jobs/<int:job_id>")
@login_required
def save_job(job_id):
    _require_job(job_id)
    created = tracking_model.save_job(g.user["user_id"], job_id)
    return success({"job_id": job_id, "saved": True}, "Job saved" if created else "Job already saved",
                   201 if created else 200)


@bp.delete("/saved-jobs/<int:job_id>")
@login_required
def unsave_job(job_id):
    if not tracking_model.unsave_job(g.user["user_id"], job_id):
        raise NotFound("Saved job not found")
    return success({"job_id": job_id, "saved": False}, "Job removed from saved jobs")


# ----------------------------------------------------------- applications

def _parse_status(value, default=None):
    status = clean_str(value, 20, "status") or default
    if status not in APPLICATION_STATUSES:
        raise ValidationError(f"status must be one of: {', '.join(APPLICATION_STATUSES)}", {"status": "invalid"})
    return status


def _parse_date(value):
    if value in (None, ""):
        return None
    try:
        parsed = date.fromisoformat(str(value)[:10])
    except ValueError:
        raise ValidationError("applied_date must be a date in YYYY-MM-DD format", {"applied_date": "invalid"})
    if parsed > date.today():
        raise ValidationError("applied_date cannot be in the future", {"applied_date": "future"})
    return parsed


def _application(user_id, application_id):
    row = tracking_model.get_application(user_id, application_id)
    if not row:
        raise NotFound("Application not found")
    return row_to_dict(row)


@bp.get("/applications")
@login_required
def list_applications():
    status = request.args.get("status", "")
    if status and status not in APPLICATION_STATUSES:
        raise ValidationError("Invalid status filter")
    items = [row_to_dict(r) for r in tracking_model.list_applications(g.user["user_id"], status)]
    return success({"items": items, "total": len(items), "statuses": APPLICATION_STATUSES})


@bp.post("/applications")
@login_required
def create_application():
    data = get_json()
    try:
        job_id = int(data.get("job_id"))
    except (TypeError, ValueError):
        raise ValidationError("job_id is required", {"job_id": "required"})
    _require_job(job_id)
    user_id = g.user["user_id"]
    if tracking_model.get_application_for_job(user_id, job_id):
        raise APIError("You are already tracking an application for this job", "DUPLICATE_APPLICATION", 409)
    status = _parse_status(data.get("status"), "Applied")
    applied = _parse_date(data.get("applied_date"))
    if applied is None and status not in ("Saved",):
        applied = date.today()
    notes = clean_str(data.get("notes"), 2000, "notes") or None
    application_id = tracking_model.create_application(user_id, job_id, status, applied, notes)
    return success(_application(user_id, application_id), "Application tracking started", 201)


@bp.put("/applications/<int:application_id>")
@login_required
def update_application(application_id):
    user_id = g.user["user_id"]
    current = _application(user_id, application_id)
    data = get_json()
    fields = {}
    if "status" in data:
        fields["status"] = _parse_status(data.get("status"))
        if fields["status"] != "Saved" and not current.get("applied_date") and "applied_date" not in data:
            fields["applied_date"] = date.today()
    if "applied_date" in data:
        fields["applied_date"] = _parse_date(data.get("applied_date"))
    if "notes" in data:
        fields["notes"] = clean_str(data.get("notes"), 2000, "notes") or None
    if not fields:
        raise ValidationError("Nothing to update")
    tracking_model.update_application(user_id, application_id, fields)
    return success(_application(user_id, application_id), "Application updated")


@bp.delete("/applications/<int:application_id>")
@login_required
def delete_application(application_id):
    if not tracking_model.delete_application(g.user["user_id"], application_id):
        raise NotFound("Application not found")
    return success(None, "Application removed")
