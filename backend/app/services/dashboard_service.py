"""Lightweight candidate dashboard summary (a handful of small queries, no bulk loading)."""
from collections import Counter

from ..config.settings import APPLICATION_STATUSES
from ..models import match_model, resume_model, tracking_model, user_model
from ..utils.serialization import load_json_list, row_to_dict
from . import career_service, job_service, matching_service, profile_service


def skill_gap_counts(rows, limit=8):
    counter = Counter()
    for r in rows:
        counter.update(load_json_list(r["missing_skills"]))
    return [{"skill": s, "count": n} for s, n in counter.most_common(limit)]


def dashboard(user):
    user_id = user["user_id"]
    profile = profile_service.get_profile(user)

    top = matching_service.list_matches(user_id, sort="score", limit=5)
    exclude_mock = job_service.hide_mock_jobs()
    recent = match_model.list_matches(user_id, sort="newest", limit=5, exclude_mock=exclude_mock)[0]

    matched_counter = Counter()
    for item in top["items"]:
        matched_counter.update(item["match"]["matched_skills"] if item["match"] else [])

    resume = resume_model.get_active_resume(user_id)
    status_counts = {r["status"]: r["n"] for r in tracking_model.application_status_counts(user_id)}

    careers = []
    if profile["has_resume"] or profile["skills"]:
        careers = career_service.get_recommendations(user_id)["items"][:3]

    top_score = top["items"][0]["match"]["final_score"] if top["items"] and top["items"][0]["match"] else None
    return {
        "user": {"name": user["name"], "email": user["email"]},
        "completeness": profile["completeness"],
        "resume": {
            "has_resume": resume is not None,
            "file_name": resume["file_name"] if resume else None,
            "uploaded_at": row_to_dict({"d": resume["uploaded_at"]})["d"] if resume else None,
            "skill_count": len(profile["skills"]),
        },
        "stats": {
            "top_match_score": top_score,
            "recommended_jobs": top["total"],
            "saved_jobs": tracking_model.count_saved(user_id),
            "applications": sum(status_counts.values()),
            "applications_by_status": {s: status_counts.get(s, 0) for s in APPLICATION_STATUSES},
        },
        "top_jobs": top["items"],
        "recent_matches": [{"job_id": r["job_id"], "title": r["title"], "company": r["company"],
                            "final_score": float(r["final_score"]), "is_mock": r["source"] == "mock"}
                           for r in recent],
        "top_matched_skills": [{"skill": s, "count": n} for s, n in matched_counter.most_common(8)],
        "skill_gaps": skill_gap_counts(match_model.missing_skill_rows(user_id, 30, exclude_mock)),
        "careers": careers,
        "interests": user_model.get_interests(user_id),
    }
