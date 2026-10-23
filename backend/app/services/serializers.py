"""Shape DB rows into API payloads (JSON columns decoded, flags typed)."""
from ..integrations.jobs.mock import MOCK_NOTICE
from ..utils.serialization import load_json_list, row_to_dict


def _clean_snippet(text):
    text = (text or "").replace(MOCK_NOTICE, "").strip()
    return " ".join(text.split())


def match_payload(row):
    if row is None or row.get("final_score") is None:
        return None
    skill_match = row.get("skill_match")
    return {
        "final_score": float(row["final_score"]),
        "text_similarity": float(row["text_similarity"]),
        "skill_match": float(skill_match) if skill_match is not None else None,
        "matched_skills": load_json_list(row.get("matched_skills")),
        "missing_skills": load_json_list(row.get("missing_skills")),
        "skill_data_available": skill_match is not None,
        "calculated_at": row_to_dict({"c": row.get("calculated_at")})["c"],
    }


def job_payload(row, include_description=False):
    data = row_to_dict(row)
    job = {
        "job_id": data["job_id"],
        "external_job_id": data.get("external_job_id"),
        "title": data["title"],
        "company": data["company"],
        "location": data.get("location"),
        "country": data.get("country"),
        "job_url": data.get("job_url"),
        "employment_type": data.get("employment_type"),
        "remote": bool(data.get("remote")),
        "required_skills": load_json_list(data.get("required_skills")),
        "min_experience_years": data.get("min_experience_years"),
        "source": data.get("source"),
        "is_mock": data.get("source") == "mock",
        "publisher": data.get("publisher"),
        "posted_at": data.get("posted_at"),
        "fetched_at": data.get("fetched_at"),
        "is_saved": bool(data.get("is_saved")),
        "match": match_payload(row),
    }
    if include_description:
        job["description"] = data.get("description") or ""
    else:
        job["snippet"] = _clean_snippet(data.get("snippet") or data.get("description") or "")[:280]
    return job
