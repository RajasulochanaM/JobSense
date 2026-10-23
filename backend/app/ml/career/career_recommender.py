"""CareerRecommender - compares a candidate profile with predefined career paths.

For each career:
    skill_alignment = sum(importance of matched career skills)
                      / sum(importance of all career skills) * 100
        (importance: 3 = core, 2 = important, 1 = nice to have)
    text_similarity = TF-IDF cosine similarity between the candidate's resume
                      and the career profile (description + skills), 0-100
    interest_match  = 100 if the career's interest area is one of the
                      candidate's interests, else 0

    match_score = ws x skill_alignment + wt x text_similarity + wi x interest_match

Weights default to 0.75 / 0.15 / 0.10. Interests are a secondary signal only:
they contribute nothing unless the candidate already shows skill evidence for
the career (skill_alignment > 0), so they can never outweigh actual skills.
"""
from dataclasses import dataclass, field

from ..matching.skill_matcher import SkillMatcher
from ..similarity.text_similarity import TextSimilarityCalculator
from ..skill_extraction.taxonomy import canonical_skill, normalize_skill_key

IMPORTANCE_LABELS = {3: "core", 2: "important", 1: "nice to have"}


@dataclass
class CareerMatch:
    career_id: int
    match_score: float
    skill_alignment: float
    text_similarity: float
    interest_match: bool
    matched_skills: list = field(default_factory=list)
    missing_skills: list = field(default_factory=list)
    reasons: list = field(default_factory=list)


class CareerRecommender:
    def __init__(self, skill_weight=0.75, text_weight=0.15, interest_weight=0.10, similarity=None):
        total = skill_weight + text_weight + interest_weight
        if total <= 0:
            raise ValueError("Career weights must sum to a positive value")
        self.ws, self.wt, self.wi = skill_weight / total, text_weight / total, interest_weight / total
        self.similarity = similarity or TextSimilarityCalculator()
        self.skill_matcher = SkillMatcher()

    @classmethod
    def from_config(cls, config):
        return cls(config["CAREER_SKILL_WEIGHT"], config["CAREER_TEXT_WEIGHT"], config["CAREER_INTEREST_WEIGHT"])

    def score_career(self, career, candidate_skills, processed_resume, interests,
                     experience_years=None, education_text=""):
        """career: {'career_id', 'career_name', 'description', 'interest_area',
                    'skills': [{'skill_name', 'importance'}]}"""
        have = self.skill_matcher.expand(candidate_skills)
        total_weight = matched_weight = 0
        matched, missing = [], []
        for cs in sorted(career.get("skills", []), key=lambda s: -int(s.get("importance", 2))):
            name = canonical_skill(cs["skill_name"])
            weight = int(cs.get("importance", 2))
            total_weight += weight
            if normalize_skill_key(name) in have:
                matched_weight += weight
                matched.append({"skill": name, "importance": weight,
                                "importance_label": IMPORTANCE_LABELS.get(weight, "important")})
            else:
                missing.append({"skill": name, "importance": weight,
                                "importance_label": IMPORTANCE_LABELS.get(weight, "important")})
        skill_alignment = round(matched_weight / total_weight * 100, 2) if total_weight else 0.0

        career_doc = " ".join([career.get("career_name", ""), career.get("description", "")] +
                              [s["skill_name"] for s in career.get("skills", [])])
        text_sim = self.similarity.similarity_percent(processed_resume or "",
                                                      self.similarity.preprocess(career_doc)) \
            if processed_resume else 0.0

        interest_area = (career.get("interest_area") or "").lower()
        interest_hit = bool(interest_area) and interest_area in {i.lower() for i in interests or []}
        interest_component = 100.0 if (interest_hit and skill_alignment > 0) else 0.0

        score = self.ws * skill_alignment + self.wt * text_sim + self.wi * interest_component
        score = round(max(0.0, min(100.0, score)), 2)

        reasons = []
        core_matched = [m["skill"] for m in matched if m["importance"] == 3]
        if core_matched:
            reasons.append(f"You already have {len(core_matched)} core skill(s) for this role: "
                           f"{', '.join(core_matched[:5])}.")
        if matched:
            reasons.append(f"{len(matched)} of {len(matched) + len(missing)} listed skills match your profile "
                           f"({skill_alignment:.0f}% weighted skill alignment).")
        else:
            reasons.append("None of this role's listed skills were found in your profile yet.")
        if text_sim >= 10:
            reasons.append(f"Your resume content is textually similar to this role's profile "
                           f"({text_sim:.0f}% TF-IDF similarity).")
        if interest_hit:
            if skill_alignment > 0:
                reasons.append(f"It matches your stated interest in {career.get('interest_area')}.")
            else:
                reasons.append(f"It matches your interest in {career.get('interest_area')}, but interests only "
                               "count once you have some matching skills.")
        if experience_years is not None and experience_years > 0:
            reasons.append(f"Your profile shows about {experience_years:g} year(s) of experience.")
        if education_text:
            edu = education_text.lower()
            if any(k in edu for k in ("computer", "information technology", "software", "data", "statistics",
                                      "mathematics", "electronics", "engineering")):
                reasons.append("Your education background is relevant to technical roles.")
        missing_core = [m["skill"] for m in missing if m["importance"] == 3]
        if missing_core:
            reasons.append(f"Core skills to develop next: {', '.join(missing_core[:5])}.")

        return CareerMatch(
            career_id=career["career_id"], match_score=score, skill_alignment=skill_alignment,
            text_similarity=text_sim, interest_match=interest_hit,
            matched_skills=matched, missing_skills=missing, reasons=reasons,
        )

    def recommend(self, careers, candidate_skills, processed_resume, interests,
                  experience_years=None, education_text=""):
        results = [self.score_career(c, candidate_skills, processed_resume, interests,
                                     experience_years, education_text) for c in careers]
        results.sort(key=lambda r: (r.match_score, r.skill_alignment), reverse=True)
        return results
