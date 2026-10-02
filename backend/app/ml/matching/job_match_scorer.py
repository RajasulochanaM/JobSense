"""JobMatchScorer - combines TF-IDF text similarity and explicit skill matching.

    Final Score = w1 x Text Similarity + w2 x Skill Match

w1 = TEXT_SIMILARITY_WEIGHT and w2 = SKILL_MATCH_WEIGHT come from configuration
(initial values 0.40 / 0.60 - adjustable during evaluation). Weights are
normalised so they always sum to 1, which keeps 0 <= final score <= 100.
If a job has no identifiable required skills, the final score equals the text
similarity and `skill_data_available` is False so the UI can say so.
"""
from dataclasses import dataclass

from ..similarity.text_similarity import TextSimilarityCalculator
from .skill_matcher import SkillMatcher


@dataclass
class JobMatch:
    text_similarity: float
    skill_match: float | None
    final_score: float
    matched_skills: list
    missing_skills: list
    skill_data_available: bool
    weights: dict

    def to_dict(self):
        return {
            "text_similarity": self.text_similarity,
            "skill_match": self.skill_match,
            "final_score": self.final_score,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "matched_count": len(self.matched_skills),
            "missing_count": len(self.missing_skills),
            "skill_data_available": self.skill_data_available,
            "weights": self.weights,
        }


def combine_scores(text_similarity, skill_match, text_weight, skill_weight):
    """Weighted combination clamped to [0, 100]."""
    if skill_match is None:
        score = text_similarity
    else:
        total = (text_weight + skill_weight) or 1.0
        score = (text_weight / total) * text_similarity + (skill_weight / total) * skill_match
    return round(max(0.0, min(100.0, score)), 2)


class JobMatchScorer:
    def __init__(self, text_weight=0.40, skill_weight=0.60, similarity=None, skill_matcher=None):
        if text_weight < 0 or skill_weight < 0 or (text_weight + skill_weight) == 0:
            raise ValueError("Match weights must be non-negative and not both zero")
        self.text_weight = float(text_weight)
        self.skill_weight = float(skill_weight)
        self.similarity = similarity or TextSimilarityCalculator()
        self.skill_matcher = skill_matcher or SkillMatcher()

    @classmethod
    def from_config(cls, config):
        return cls(config["TEXT_SIMILARITY_WEIGHT"], config["SKILL_MATCH_WEIGHT"])

    def score(self, processed_resume, candidate_skills, processed_job, job_skills):
        """Score one job. Texts must already be preprocessed (see TextPreprocessor)."""
        text_sim = self.similarity.similarity_percent(processed_resume, processed_job)
        skills = self.skill_matcher.match(candidate_skills, job_skills)
        final = combine_scores(text_sim, skills.skill_match, self.text_weight, self.skill_weight)
        total = self.text_weight + self.skill_weight
        return JobMatch(
            text_similarity=text_sim,
            skill_match=skills.skill_match,
            final_score=final,
            matched_skills=skills.matched,
            missing_skills=skills.missing,
            skill_data_available=skills.skill_match is not None,
            weights={"text_similarity": round(self.text_weight / total, 3),
                     "skill_match": round(self.skill_weight / total, 3)},
        )

    def rank(self, processed_resume, candidate_skills, jobs):
        """jobs: iterable of dicts with 'processed_text' and 'required_skills'.
        Returns [(job, JobMatch)] sorted by final score (desc)."""
        scored = [(job, self.score(processed_resume, candidate_skills,
                                   job.get("processed_text", ""), job.get("required_skills", [])))
                  for job in jobs]
        scored.sort(key=lambda pair: (pair[1].final_score, pair[1].text_similarity), reverse=True)
        return scored
