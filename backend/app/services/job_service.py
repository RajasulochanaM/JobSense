"""Job retrieval: external provider search, normalisation, de-duplication and storage.

Every job is NLP-processed exactly once when first stored (skill extraction +
text preprocessing) so matching never re-runs spaCy on job descriptions.
"""
import logging
import threading
import time

from flask import current_app

from ..integrations.jobs import JobProviderError, JobSearchParams, get_job_provider
from ..integrations.jobs.mock import MOCK_NOTICE
from ..ml.preprocessing.text_preprocessor import get_preprocessor
from ..ml.skill_extraction.skill_extractor import get_skill_extractor
from ..ml.skill_extraction.taxonomy import skill_category
from ..models import job_model
from ..utils.responses import APIError
from ..utils.serialization import dump_json

logger = logging.getLogger(__name__)

_cache = {}
_cache_lock = threading.Lock()


def provider():
    return get_job_provider(current_app.config)


# Soft skills ("communication", "problem solving") appear in almost every job ad but are
# rarely listed verbatim on resumes, so counting them as required skills would lower every
# skill-match score without saying anything about technical fit. They are excluded here.
EXCLUDED_REQUIRED_CATEGORIES = {"Soft Skills"}


def analyse_job_text(description, highlights=()):
    """Return (processed_text, required_skills) for a job description."""
    text = (description or "").replace(MOCK_NOTICE, " ")
    skill_text = "\n".join([text, *highlights])
    skills = [s for s in get_skill_extractor().extract(skill_text)
              if skill_category(s) not in EXCLUDED_REQUIRED_CATEGORIES]
    return get_preprocessor().preprocess(text), skills


def ingest_jobs(normalized_jobs):
    """Store provider results (skipping duplicates) and return job_ids in result order."""
    if not normalized_jobs:
        return []
    by_source = {}
    for job in normalized_jobs:
        by_source.setdefault(job.source, []).append(job)

    job_ids, seen = [], set()
    for source, jobs in by_source.items():
        existing = job_model.find_existing(source, [j.external_job_id for j in jobs],
                                           [job_model.url_hash(j.job_url) for j in jobs])
        for job in jobs:
            h = job_model.url_hash(job.job_url)
            job_id = existing.get(job.external_job_id) or (existing.get(h) if h else None)
            if job_id is None:
                processed, skills = analyse_job_text(job.description, job.highlights)
                job_id = job_model.insert_job({
                    **job.to_dict(),
                    "processed_text": processed,
                    "required_skills": dump_json(skills),
                })
                if h:
                    existing[h] = job_id
                existing[job.external_job_id] = job_id
            if job_id not in seen:
                seen.add(job_id)
                job_ids.append(job_id)
    job_model.touch_jobs(job_ids)
    return job_ids


def _cache_get(key):
    ttl = current_app.config["JOB_SEARCH_CACHE_SECONDS"]
    with _cache_lock:
        entry = _cache.get(key)
        if entry and time.time() - entry[0] < ttl:
            return entry[1]
        if entry:
            _cache.pop(key, None)
    return None


def _cache_set(key, value):
    with _cache_lock:
        if len(_cache) > 500:
            _cache.clear()
        _cache[key] = (time.time(), value)


def clear_cache():
    with _cache_lock:
        _cache.clear()


def search_provider(params: JobSearchParams):
    """Search the configured provider (cached) and return (job_ids, provider_name, is_mock)."""
    try:
        prov = provider()
    except JobProviderError as exc:
        raise APIError(exc.message, exc.code, exc.status)

    key = (prov.name,) + params.cache_key()
    cached = _cache_get(key)
    if cached is not None:
        return cached, prov.name, prov.is_mock

    try:
        results = prov.search(params)
    except JobProviderError as exc:
        raise APIError(exc.message, exc.code, exc.status)
    job_ids = ingest_jobs(results)
    _cache_set(key, job_ids)
    logger.info("Job search via %s returned %d jobs", prov.name, len(job_ids))
    return job_ids, prov.name, prov.is_mock


def hide_mock_jobs():
    """Sample (mock) jobs are for development only - hide them whenever a real provider is active."""
    return not provider_info()["is_mock"]


def provider_info():
    try:
        prov = provider()
        return {"provider": prov.name, "is_mock": prov.is_mock, "configured": True}
    except JobProviderError:
        return {"provider": "jsearch", "is_mock": False, "configured": False}
