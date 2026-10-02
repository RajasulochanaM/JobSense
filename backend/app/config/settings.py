"""Central configuration. Every tunable value is read from environment variables here
so the rest of the codebase never hardcodes secrets, credentials or scoring weights."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent

# Load backend/.env first, then the repository-level .env (neither overrides real env vars).
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_DIR / ".env")


def _bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _float(name, default):
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return float(default)


def _int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return int(default)


class Config:
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV == "development"
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY") or "dev-only-insecure-secret-change-me"

    # Database (MySQL)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = _int("DB_PORT", 3306)
    DB_NAME = os.getenv("DB_NAME", "jobsense")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_POOL_SIZE = _int("DB_POOL_SIZE", 5)
    DB_SSL_DISABLED = _bool("DB_SSL_DISABLED", True)

    # Authentication
    TOKEN_TTL_HOURS = _int("TOKEN_TTL_HOURS", 24 * 7)

    # CORS: comma separated list of allowed origins
    CORS_ORIGINS = [o.strip() for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]

    # Resume uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BACKEND_DIR / "uploads"))
    MAX_RESUME_SIZE_MB = _int("MAX_RESUME_SIZE_MB", 5)
    MAX_CONTENT_LENGTH = (MAX_RESUME_SIZE_MB + 1) * 1024 * 1024

    # Job provider: "jsearch", "mock" or "auto" (JSearch when a key is present, otherwise mock)
    JOB_PROVIDER = os.getenv("JOB_PROVIDER", "auto").lower()
    JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY", "")
    JSEARCH_BASE_URL = os.getenv("JSEARCH_BASE_URL", "https://api.openwebninja.com/jsearch")
    JSEARCH_TIMEOUT_SECONDS = _int("JSEARCH_TIMEOUT_SECONDS", 45)
    JOB_SEARCH_CACHE_SECONDS = _int("JOB_SEARCH_CACHE_SECONDS", 900)

    # Matching weights (initial implementation values - adjustable during evaluation)
    TEXT_SIMILARITY_WEIGHT = _float("TEXT_SIMILARITY_WEIGHT", 0.40)
    SKILL_MATCH_WEIGHT = _float("SKILL_MATCH_WEIGHT", 0.60)

    # Career recommendation weights (initial values - adjustable during evaluation)
    CAREER_SKILL_WEIGHT = _float("CAREER_SKILL_WEIGHT", 0.75)
    CAREER_TEXT_WEIGHT = _float("CAREER_TEXT_WEIGHT", 0.15)
    CAREER_INTEREST_WEIGHT = _float("CAREER_INTEREST_WEIGHT", 0.10)

    # How many stored jobs are (re)scored when refreshing recommendations
    MATCH_POOL_LIMIT = _int("MATCH_POOL_LIMIT", 300)

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    DB_NAME = os.getenv("TEST_DB_NAME", "jobsense_test")
    JOB_PROVIDER = "mock"
    SECRET_KEY = "test-secret"


# Interests a candidate can pick from, grouped by field (a secondary career-recommendation signal).
# Candidates may also add their own custom interests; see profile_service.MAX_INTERESTS.
INTEREST_GROUPS = {
    "Information Technology": [
        "IT", "Software Development", "Web Development", "Backend Development", "Mobile Development",
        "AI/ML", "Data", "Cloud", "DevOps", "Cybersecurity", "Testing", "Networking", "IT Support",
        "Game Development", "Blockchain", "Embedded Systems", "UI/UX Design",
    ],
    "Engineering": [
        "Electrical Engineering", "Electronics", "Mechanical Engineering", "Civil Engineering",
        "Chemical Engineering", "Automobile", "Aerospace", "Robotics & Automation", "Manufacturing",
        "Construction", "Energy & Renewables", "Telecommunications",
    ],
    "Healthcare & Science": [
        "Medical", "Nursing", "Pharmacy", "Dentistry", "Healthcare Administration", "Biotechnology",
        "Life Sciences", "Research", "Psychology", "Physiotherapy",
    ],
    "Business & Finance": [
        "Finance", "Accounting", "Banking", "Insurance", "Consulting", "Sales", "Marketing",
        "Digital Marketing", "Business Analysis", "Product Management", "Project Management",
        "Human Resources", "Operations", "Supply Chain & Logistics", "Entrepreneurship",
    ],
    "Creative & Media": [
        "Graphic Design", "Content Writing", "Journalism", "Media & Entertainment", "Photography",
        "Video Production", "Animation", "Fashion Design", "Architecture",
    ],
    "Public Service & Others": [
        "Education & Teaching", "Law & Legal", "Government", "Hospitality", "Tourism", "Retail",
        "Customer Service", "Agriculture", "Environment", "Non-profit & Social Work", "Sports & Fitness",
        "Aviation", "Real Estate",
    ],
}
INTEREST_OPTIONS = [i for group in INTEREST_GROUPS.values() for i in group]

APPLICATION_STATUSES = ["Saved", "Applied", "Interview", "Offer", "Rejected", "Withdrawn"]
