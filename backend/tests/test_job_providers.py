import pytest
import requests

from app.integrations.jobs import JobProviderError, JobSearchParams, JSearchProvider, MockJobProvider
from app.integrations.jobs.jsearch import normalize_jsearch_job
from app.integrations.jobs.mock import MOCK_NOTICE

SAMPLE_ITEM = {
    "job_id": "abc123==",
    "job_title": "React Developer",
    "employer_name": "Example Pvt Ltd",
    "job_publisher": "LinkedIn",
    "job_employment_type": "FULLTIME",
    "job_apply_link": "https://example.com/jobs/abc123",
    "job_description": "We need React, TypeScript and Node.js experience.",
    "job_is_remote": False,
    "job_posted_at_datetime_utc": "2026-09-20T10:00:00.000Z",
    "job_city": "Chennai", "job_state": "Tamil Nadu", "job_country": "IN",
    "job_highlights": {"Qualifications": ["2+ years with React", "Knowledge of AWS"]},
    "job_required_experience": {"required_experience_in_months": 24},
}


class FakeResponse:
    def __init__(self, status=200, payload=None, json_error=False):
        self.status_code = status
        self._payload = payload
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("not json")
        return self._payload


class FakeSession:
    def __init__(self, response=None, exc=None):
        self.response, self.exc, self.calls = response, exc, []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        if self.exc:
            raise self.exc
        return self.response


def provider(response=None, exc=None):
    session = FakeSession(response, exc)
    return JSearchProvider("test-key", "https://api.openwebninja.com/jsearch", session=session), session


def test_normalize_jsearch_job():
    job = normalize_jsearch_job(SAMPLE_ITEM)
    assert job.external_job_id == "abc123=="
    assert job.title == "React Developer" and job.company == "Example Pvt Ltd"
    assert job.location == "Chennai, Tamil Nadu, IN"
    assert job.employment_type == "Full-time"
    assert job.job_url == "https://example.com/jobs/abc123"
    assert job.source == "jsearch" and job.remote is False
    assert job.posted_at.startswith("2026-09-20T10:00")
    assert job.min_experience_years == 2.0
    assert "Knowledge of AWS" in job.highlights


def test_normalize_rejects_malformed_items():
    assert normalize_jsearch_job(None) is None
    assert normalize_jsearch_job({"job_title": "No id"}) is None
    job = normalize_jsearch_job({"job_id": "x", "job_title": "T", "job_apply_link": "javascript:alert(1)"})
    assert job.job_url is None and job.company == "Company not disclosed"


def test_search_builds_query_and_uses_header():
    prov, session = provider(FakeResponse(200, {"status": "OK", "data": [SAMPLE_ITEM, {"bad": 1}]}))
    jobs = prov.search(JobSearchParams(query="React Developer", location="Chennai", remote=True,
                                       employment_type="FULLTIME"))
    assert len(jobs) == 1
    call = session.calls[0]
    assert call["url"].endswith("/search")
    assert call["params"]["query"] == "React Developer in Chennai"
    assert call["params"]["country"] == "in"
    assert call["params"]["work_from_home"] == "true"
    assert call["params"]["employment_types"] == "FULLTIME"
    assert call["headers"] == {"x-api-key": "test-key"}


def test_empty_results_return_empty_list():
    prov, _ = provider(FakeResponse(200, {"status": "OK", "data": []}))
    assert prov.search(JobSearchParams(query="Rare job")) == []


@pytest.mark.parametrize("response,exc,code", [
    (FakeResponse(401, {}), None, "JOB_API_AUTH_FAILED"),
    (FakeResponse(429, {}), None, "JOB_API_RATE_LIMITED"),
    (FakeResponse(500, {}), None, "JOB_API_ERROR"),
    (FakeResponse(200, json_error=True), None, "JOB_API_MALFORMED"),
    (FakeResponse(200, {"status": "OK", "data": "oops"}), None, "JOB_API_MALFORMED"),
    (None, requests.Timeout(), "JOB_API_TIMEOUT"),
    (None, requests.ConnectionError(), "JOB_API_UNAVAILABLE"),
])
def test_error_handling(response, exc, code):
    prov, _ = provider(response, exc)
    with pytest.raises(JobProviderError) as err:
        prov.search(JobSearchParams(query="python"))
    assert err.value.code == code


def test_missing_api_key_is_reported():
    with pytest.raises(JobProviderError) as err:
        JSearchProvider("", "https://api.openwebninja.com/jsearch")
    assert err.value.code == "JOB_API_NOT_CONFIGURED"


def test_mock_jobs_are_clearly_labelled_and_deterministic():
    params = JobSearchParams(query="Python Developer", location="Hyderabad")
    first = MockJobProvider().search(params)
    second = MockJobProvider().search(params)
    assert [j.external_job_id for j in first] == [j.external_job_id for j in second]
    for job in first:
        assert job.source == "mock"
        assert job.company.endswith("(Sample)")
        assert job.description.startswith(MOCK_NOTICE)
        assert job.job_url is None
        assert "Hyderabad" in job.location
    assert "Python" in first[0].title
    assert MockJobProvider().search(JobSearchParams(query="python", page=99)) == []


def test_job_required_skills_exclude_soft_skills():
    from app.services.job_service import analyse_job_text
    processed, skills = analyse_job_text("Need React and TypeScript. Excellent communication skills and problem solving.")
    assert skills == ["React", "TypeScript"]
    assert processed
