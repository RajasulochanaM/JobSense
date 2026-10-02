"""Job recommendation engine.

    candidate profile -> resume skills -> retrieve jobs -> TF-IDF text similarity
    -> explicit skill match -> final score -> rank -> persist JOB_MATCHES

Matches are cached in JOB_MATCHES and only (re)computed when needed: for
newly seen jobs, or after the candidate's resume/skills change (which clears
the cache).
"""
import logging

from flask import current_app

from ..integrations.jobs import JobSearchParams
from ..ml.matching.job_match_scorer import JobMatchScorer
from ..ml.similarity.text_similarity import TextSimilarityCalculator
from ..models import job_model, match_model, user_model
from ..utils.responses import APIError, NotFound
from ..utils.serialization import dump_json, load_json_list
from .candidate_service import load_candidate
from .job_service import hide_mock_jobs, search_provider
from .serializers import job_payload, match_payload

logger = logging.getLogger(__name__)


def scorer():
    return JobMatchScorer.from_config(current_app.config)


def score_jobs(candidate, job_rows):
    """Compute + persist matches for the given job rows. Returns number scored."""
    if not candidate.is_matchable or not job_rows:
        return 0
    s = scorer()
    rows = []
    for job in job_rows:
        m = s.score(candidate.processed_text, candidate.skills, job.get("processed_text") or "",
                    load_json_list(job.get("required_skills")))
        rows.append((job["job_id"], m.text_similarity, m.skill_match, m.final_score,
                     dump_json(m.matched_skills), dump_json(m.missing_skills)))
    match_model.upsert_matches(candidate.user_id, rows)
    return len(rows)


def ensure_matches(user_id, job_ids, candidate=None):
    """Score only the jobs that do not have a cached match yet."""
    if not job_ids:
        return 0
    already = match_model.matched_job_ids(user_id, job_ids)
    todo = [j for j in job_ids if j not in already]
    if not todo:
        return 0
    candidate = candidate or load_candidate(user_id)
    return score_jobs(candidate, job_model.get_jobs_for_matching(todo))


def refresh_matches(user_id, fetch=False):
    """Re-score the recent job pool; optionally fetch fresh jobs based on the profile first."""
    candidate = load_candidate(user_id)
    if not candidate.is_matchable:
        raise APIError("Upload a resume or add skills to your profile to get job matches.",
                       "PROFILE_INCOMPLETE", 409)
    fetched, fetch_error = 0, None
    if fetch:
        for params in profile_search_params(candidate):
            try:
                ids, _, _ = search_provider(params)
                fetched += len(ids)
            except APIError as exc:
                # Existing jobs can still be re-scored; report the problem instead of failing.
                logger.warning("Profile-based job fetch failed: %s", exc.code)
                fetch_error = exc.message
                break
    pool = job_model.get_jobs_for_matching(limit=current_app.config["MATCH_POOL_LIMIT"],
                                           exclude_mock=hide_mock_jobs())
    scored = score_jobs(candidate, pool)
    return {"scored_jobs": scored, "fetched_jobs": fetched, "fetch_error": fetch_error}


def profile_search_params(candidate):
    """Build 1-2 provider queries from the candidate's top career recommendation / skills."""
    from ..models import career_model
    profile = user_model.get_profile(candidate.user_id) or {}
    locations = [l.strip() for l in (profile.get("preferred_locations") or "").split(",") if l.strip()]
    location = locations[0] if locations else (profile.get("location") or "")
    remote = profile.get("remote_preference") == "remote"

    queries = []
    recs = career_model.list_recommendations(candidate.user_id)
    if recs:
        queries.append(recs[0]["career_name"])
    technical = [s for s in candidate.skills if s not in ("Communication", "Teamwork", "Problem Solving")]
    if technical:
        queries.append(f"{technical[0]} developer")
    if not queries:
        queries.append("software engineer")
    return [JobSearchParams(query=q, location=location, remote=remote or None) for q in queries[:2]]


def list_matches(user_id, sort="score", limit=10, offset=0, min_score=0):
    exclude_mock = hide_mock_jobs()
    total_existing = match_model.count_matches(user_id, exclude_mock)
    candidate = None
    if total_existing == 0:
        candidate = load_candidate(user_id)
        if candidate.is_matchable:
            score_jobs(candidate, job_model.get_jobs_for_matching(limit=current_app.config["MATCH_POOL_LIMIT"],
                                                                  exclude_mock=exclude_mock))
    rows, total = match_model.list_matches(user_id, sort, limit, offset, min_score, exclude_mock)
    items = []
    for r in rows:
        job = job_payload(r)
        job["match"] = match_payload(r)
        items.append(job)
    profile_ready = candidate.is_matchable if candidate else True
    return {"items": items, "total": total, "limit": limit, "offset": offset, "profile_ready": profile_ready}


def match_detail(user_id, job_id):
    job = job_model.get_job(job_id)
    if not job:
        raise NotFound("Job not found")
    candidate = load_candidate(user_id)
    if not candidate.is_matchable:
        return {"job_id": job_id, "match": None, "profile_ready": False, "explanation": None}
    ensure_matches(user_id, [job_id], candidate)
    row = match_model.get_match(user_id, job_id)
    shared = TextSimilarityCalculator.shared_terms(candidate.processed_text, job.get("processed_text") or "")
    cfg = current_app.config
    total_w = cfg["TEXT_SIMILARITY_WEIGHT"] + cfg["SKILL_MATCH_WEIGHT"]
    match = match_payload(row)
    return {
        "job_id": job_id,
        "match": match,
        "profile_ready": True,
        "explanation": {
            "text_similarity_method": "TF-IDF vectors of your resume and the job description, compared with "
                                      "cosine similarity",
            "skill_match_method": "Matched required skills / total required skills x 100",
            "weights": {"text_similarity": round(cfg["TEXT_SIMILARITY_WEIGHT"] / total_w, 3),
                        "skill_match": round(cfg["SKILL_MATCH_WEIGHT"] / total_w, 3)},
            "formula": "Final = w1 x Text Similarity + w2 x Skill Match"
                       if match and match["skill_data_available"]
                       else "Final = Text Similarity (no required skills could be identified in this job)",
            "top_shared_terms": shared,
            "candidate_skill_count": len(candidate.skills),
        },
    }
