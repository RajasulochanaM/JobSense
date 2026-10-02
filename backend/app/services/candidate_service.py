"""Candidate profile aggregation used by the matching and career services."""
from dataclasses import dataclass, field

from ..ml.preprocessing.text_preprocessor import skill_token
from ..models import resume_model, user_model
from ..utils.serialization import load_json_list


@dataclass
class CandidateProfile:
    user_id: int
    skills: list = field(default_factory=list)
    processed_text: str = ""
    has_resume: bool = False
    interests: list = field(default_factory=list)
    experience_years: float | None = None
    education_text: str = ""

    @property
    def is_matchable(self):
        return bool(self.skills or self.processed_text)


def load_candidate(user_id):
    resume = resume_model.get_active_resume(user_id)
    skills = resume_model.skill_names(user_id)
    profile = user_model.get_profile(user_id) or {}

    processed = (resume or {}).get("processed_text") or ""
    # Manually added skills also contribute to the TF-IDF document.
    resume_skill_tokens = set(processed.split())
    extra = [skill_token(s) for s in skills if skill_token(s) not in resume_skill_tokens]
    processed = " ".join(filter(None, [processed, " ".join(extra)]))

    exp = profile.get("experience_years")
    if exp is None and resume:
        exp = resume.get("experience_years")
    education = profile.get("education") or " ".join(load_json_list((resume or {}).get("education")))
    return CandidateProfile(
        user_id=user_id,
        skills=skills,
        processed_text=processed,
        has_resume=resume is not None,
        interests=user_model.get_interests(user_id),
        experience_years=float(exp) if exp is not None else None,
        education_text=education or "",
    )
