"""Job provider abstraction.

Every provider returns `NormalizedJob` objects so the rest of the system never
depends on a particular external API's response format.
"""
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field


class JobProviderError(Exception):
    """Raised for provider failures. `code` is safe to show to clients."""

    def __init__(self, message, code="JOB_PROVIDER_ERROR", status=502):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


@dataclass
class JobSearchParams:
    query: str
    location: str = ""
    country: str = "in"
    remote: bool | None = None
    employment_type: str = ""          # FULLTIME | PARTTIME | CONTRACTOR | INTERN
    experience: str = ""               # no_experience | under_3_years_experience | more_than_3_years_experience
    max_experience_years: int | None = None  # candidate's years of experience (0-50); jobs needing more are dropped
    date_posted: str = "all"           # all | today | 3days | week | month
    page: int = 1

    def cache_key(self):
        return tuple(sorted(asdict(self).items()))


@dataclass
class NormalizedJob:
    external_job_id: str
    title: str
    company: str
    location: str = ""
    country: str = ""
    description: str = ""
    job_url: str | None = None
    employment_type: str = ""
    remote: bool = False
    source: str = ""
    publisher: str = ""
    posted_at: str | None = None       # ISO-8601
    min_experience_years: float | None = None
    highlights: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


class BaseJobProvider(ABC):
    name = "base"
    is_mock = False

    @abstractmethod
    def search(self, params: JobSearchParams) -> list[NormalizedJob]:
        """Search jobs. Must return [] (not raise) when there are simply no results."""

    def get_details(self, external_job_id: str) -> NormalizedJob | None:  # pragma: no cover - optional
        return None
