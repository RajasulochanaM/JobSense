"""Job provider factory."""
import logging

from .base import BaseJobProvider, JobProviderError, JobSearchParams, NormalizedJob
from .jsearch import JSearchProvider
from .mock import MockJobProvider

logger = logging.getLogger(__name__)

__all__ = ["BaseJobProvider", "JobProviderError", "JobSearchParams", "NormalizedJob",
           "JSearchProvider", "MockJobProvider", "get_job_provider"]


def get_job_provider(config):
    """JOB_PROVIDER=jsearch|mock|auto. 'auto' uses JSearch when a key is configured."""
    choice = (config["JOB_PROVIDER"] or "auto").lower()
    if choice == "mock":
        return MockJobProvider()
    if choice == "jsearch" or (choice == "auto" and config["JSEARCH_API_KEY"]):
        return JSearchProvider(config["JSEARCH_API_KEY"], config["JSEARCH_BASE_URL"], config["JSEARCH_TIMEOUT_SECONDS"])
    return MockJobProvider()
