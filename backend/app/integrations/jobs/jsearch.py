"""OpenWeb Ninja JSearch provider.

Docs: https://www.openwebninja.com/api/jsearch
    GET {JSEARCH_BASE_URL}/search       ?query=&page=&num_pages=&country=&date_posted=
                                         &work_from_home=&employment_types=&job_requirements=
    GET {JSEARCH_BASE_URL}/job-details  ?job_id=&country=
Authentication header: x-api-key (the key is only ever read server-side).
The RapidAPI-hosted variant (https://jsearch.p.rapidapi.com) is also supported
by setting JSEARCH_BASE_URL accordingly.
"""
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

from .base import BaseJobProvider, JobProviderError, JobSearchParams, NormalizedJob

logger = logging.getLogger(__name__)

VALID_EMPLOYMENT_TYPES = {"FULLTIME", "PARTTIME", "CONTRACTOR", "INTERN"}
VALID_REQUIREMENTS = {"no_experience", "under_3_years_experience", "more_than_3_years_experience", "no_degree"}
VALID_DATE_POSTED = {"all", "today", "3days", "week", "month"}
EMPLOYMENT_LABELS = {"FULLTIME": "Full-time", "PARTTIME": "Part-time", "CONTRACTOR": "Contract",
                     "INTERN": "Internship"}


def _str(value, max_len=None):
    if value is None:
        return ""
    value = str(value).strip()
    return value[:max_len] if max_len else value


def _safe_url(value):
    url = _str(value)
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return url[:1000]
    return None


def _posted_at(item):
    raw = item.get("job_posted_at_datetime_utc")
    if raw:
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).astimezone(timezone.utc) \
                .replace(tzinfo=None).isoformat()
        except ValueError:
            pass
    ts = item.get("job_posted_at_timestamp")
    if isinstance(ts, (int, float)) and ts > 0:
        return datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None).isoformat()
    return None


def normalize_jsearch_job(item):
    """Convert one JSearch result into a NormalizedJob. Returns None if unusable."""
    if not isinstance(item, dict):
        return None
    job_id = _str(item.get("job_id"), 255)
    title = _str(item.get("job_title"), 255)
    if not job_id or not title:
        return None

    location = _str(item.get("job_location"))
    if not location:
        location = ", ".join(p for p in (_str(item.get("job_city")), _str(item.get("job_state")),
                                         _str(item.get("job_country"))) if p)

    highlights = []
    raw_highlights = item.get("job_highlights")
    if isinstance(raw_highlights, dict):
        for key in ("Qualifications", "Responsibilities"):
            values = raw_highlights.get(key)
            if isinstance(values, list):
                highlights.extend(_str(v, 500) for v in values if v)

    emp = _str(item.get("job_employment_type")).upper().replace("-", "").replace(" ", "")
    exp_months = None
    req = item.get("job_required_experience")
    if isinstance(req, dict) and isinstance(req.get("required_experience_in_months"), (int, float)):
        exp_months = req["required_experience_in_months"]

    return NormalizedJob(
        external_job_id=job_id,
        title=title,
        company=_str(item.get("employer_name"), 255) or "Company not disclosed",
        location=location[:255],
        country=_str(item.get("job_country"), 8),
        description=_str(item.get("job_description"), 60000),
        job_url=_safe_url(item.get("job_apply_link")) or _safe_url(item.get("job_google_link")),
        employment_type=EMPLOYMENT_LABELS.get(emp, _str(item.get("job_employment_type"), 60)),
        remote=bool(item.get("job_is_remote")),
        source="jsearch",
        publisher=_str(item.get("job_publisher"), 120),
        posted_at=_posted_at(item),
        min_experience_years=round(exp_months / 12, 1) if exp_months else None,
        highlights=highlights[:40],
    )


class JSearchProvider(BaseJobProvider):
    name = "jsearch"

    def __init__(self, api_key, base_url, timeout=45, session=None):
        if not api_key:
            raise JobProviderError("JSearch API key is not configured", "JOB_API_NOT_CONFIGURED", 503)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def _headers(self):
        host = urlparse(self.base_url).netloc
        if "rapidapi" in host:
            return {"X-RapidAPI-Key": self.api_key, "X-RapidAPI-Host": host}
        return {"x-api-key": self.api_key}

    def _get(self, path, params):
        url = f"{self.base_url}/{path}"
        try:
            resp = self.session.get(url, params=params, headers=self._headers(), timeout=self.timeout)
        except requests.Timeout as exc:
            logger.warning("JSearch timeout (%s)", path)
            raise JobProviderError("The job search service timed out. Please try again.", "JOB_API_TIMEOUT", 504) from exc
        except requests.RequestException as exc:
            logger.error("JSearch connection error (%s): %s", path, type(exc).__name__)
            raise JobProviderError("Could not reach the job search service.", "JOB_API_UNAVAILABLE", 502) from exc

        if resp.status_code in (401, 403):
            logger.error("JSearch rejected the API key (HTTP %s)", resp.status_code)
            raise JobProviderError("The job search service rejected the API key.", "JOB_API_AUTH_FAILED", 502)
        if resp.status_code == 429:
            logger.warning("JSearch rate limit reached")
            raise JobProviderError("Job search rate limit reached. Please wait a moment and try again.",
                                   "JOB_API_RATE_LIMITED", 429)
        if resp.status_code >= 400:
            logger.error("JSearch HTTP %s on %s", resp.status_code, path)
            raise JobProviderError("The job search service returned an error.", "JOB_API_ERROR", 502)
        try:
            payload = resp.json()
        except ValueError as exc:
            logger.error("JSearch returned non-JSON response")
            raise JobProviderError("The job search service returned an invalid response.",
                                   "JOB_API_MALFORMED", 502) from exc
        if not isinstance(payload, dict):
            raise JobProviderError("The job search service returned an invalid response.", "JOB_API_MALFORMED", 502)
        if str(payload.get("status", "OK")).upper() == "ERROR":
            logger.error("JSearch error status: %s", _str(payload.get("error", {}).get("message")
                                                             if isinstance(payload.get("error"), dict) else "", 200))
            raise JobProviderError("The job search service returned an error.", "JOB_API_ERROR", 502)
        return payload

    @staticmethod
    def build_query(params: JobSearchParams):
        query = params.query.strip()
        if params.location.strip():
            query = f"{query} in {params.location.strip()}"
        elif params.remote:
            query = f"remote {query}"
        return query

    def search(self, params: JobSearchParams):
        api_params = {
            "query": self.build_query(params),
            "page": max(1, int(params.page)),
            "num_pages": 1,
            "country": (params.country or "in").lower(),
            "date_posted": params.date_posted if params.date_posted in VALID_DATE_POSTED else "all",
        }
        if params.remote:
            api_params["work_from_home"] = "true"
        emp = (params.employment_type or "").upper()
        if emp in VALID_EMPLOYMENT_TYPES:
            api_params["employment_types"] = emp
        if params.experience in VALID_REQUIREMENTS:
            api_params["job_requirements"] = params.experience

        payload = self._get("search", api_params)
        data = payload.get("data")
        if data is None:
            return []
        if not isinstance(data, list):
            raise JobProviderError("The job search service returned an invalid response.", "JOB_API_MALFORMED", 502)
        jobs = []
        for item in data:
            job = normalize_jsearch_job(item)
            if job:
                jobs.append(job)
            else:
                logger.debug("Skipped malformed JSearch item")
        return jobs

    def get_details(self, external_job_id):
        payload = self._get("job-details", {"job_id": external_job_id})
        data = payload.get("data")
        if isinstance(data, list) and data:
            return normalize_jsearch_job(data[0])
        return None
