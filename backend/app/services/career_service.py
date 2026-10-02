"""Career path recommendations and learning-resource lookup."""
from flask import current_app

from ..ml.career.career_recommender import CareerRecommender
from ..ml.skill_extraction.taxonomy import canonical_skill
from ..models import career_model
from ..utils.responses import NotFound
from ..utils.serialization import dump_json, load_json_list, row_to_dict
from .candidate_service import load_candidate


def _career_summary(row):
    data = row_to_dict(row)
    data["skills"] = [row_to_dict(s) for s in row.get("skills", [])]
    return data


def list_careers():
    return [_career_summary(c) for c in career_model.list_careers_with_skills()]


def compute_recommendations(user_id):
    candidate = load_candidate(user_id)
    careers = career_model.list_careers_with_skills()
    recommender = CareerRecommender.from_config(current_app.config)
    results = recommender.recommend(careers, candidate.skills, candidate.processed_text, candidate.interests,
                                    candidate.experience_years, candidate.education_text)
    career_model.save_recommendations(user_id, [
        (r.career_id, r.match_score, r.skill_alignment, r.text_similarity, 1 if r.interest_match else 0,
         dump_json(r.matched_skills), dump_json(r.missing_skills), dump_json(r.reasons)) for r in results])
    return candidate


def _rec_payload(row):
    data = row_to_dict(row)
    for key in ("matched_skills", "missing_skills", "reasons"):
        data[key] = load_json_list(data.get(key))
    data["interest_match"] = bool(data.get("interest_match"))
    return data


def get_recommendations(user_id, refresh=False):
    rows = [] if refresh else career_model.list_recommendations(user_id)
    candidate = None
    if not rows:
        candidate = compute_recommendations(user_id)
        rows = career_model.list_recommendations(user_id)
    if candidate is None:
        candidate = load_candidate(user_id)
    return {
        "items": [_rec_payload(r) for r in rows],
        "profile_ready": candidate.is_matchable,
        "interests": candidate.interests,
        "weights": {
            "skill_alignment": current_app.config["CAREER_SKILL_WEIGHT"],
            "text_similarity": current_app.config["CAREER_TEXT_WEIGHT"],
            "interest": current_app.config["CAREER_INTEREST_WEIGHT"],
        },
    }


def career_detail(user_id, career_id):
    career = career_model.get_career(career_id)
    if not career:
        raise NotFound("Career path not found")
    rec = career_model.get_recommendation(user_id, career_id)
    if rec is None:
        compute_recommendations(user_id)
        rec = career_model.get_recommendation(user_id, career_id)
    rec_data = _rec_payload(rec) if rec else None
    missing = [m["skill"] for m in (rec_data or {}).get("missing_skills", [])]
    return {
        "career": _career_summary(career),
        "recommendation": rec_data,
        "learning_resources": resources_grouped(missing),
    }


def resources_grouped(skills):
    """{skill: [resources]} preserving the order of `skills`."""
    skills = [canonical_skill(s) for s in skills if s]
    rows = career_model.resources_for_skills(skills)
    grouped = {s: [] for s in skills}
    for r in rows:
        grouped.setdefault(r["skill_name"], []).append(row_to_dict(r))
    return [{"skill": s, "resources": grouped.get(s, [])} for s in skills]
