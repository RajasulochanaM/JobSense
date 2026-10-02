"""SkillMatcher - explicit comparison of candidate skills with required skills.

    skill_match = matched_required_skills / total_required_skills * 100

Candidate skills are expanded with logically implied skills from the taxonomy
(e.g. MySQL implies SQL, TypeScript implies JavaScript) before comparison.
When a job has no reliably identifiable required skills, `skill_match` is
None and the scorer falls back to text similarity only.
"""
from dataclasses import dataclass, field

from ..skill_extraction.taxonomy import canonical_skill, implied_skills, normalize_skill_key


@dataclass
class SkillMatchResult:
    matched: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    skill_match: float | None = None   # percentage 0-100, None when no required skills

    @property
    def total_required(self):
        return len(self.matched) + len(self.missing)

    def to_dict(self):
        return {
            "matched_skills": self.matched,
            "missing_skills": self.missing,
            "skill_match": self.skill_match,
            "matched_count": len(self.matched),
            "missing_count": len(self.missing),
            "total_required": self.total_required,
        }


class SkillMatcher:
    @staticmethod
    def expand(candidate_skills):
        """Canonical candidate skill keys, including implied skills (transitively)."""
        keys = set()
        stack = [canonical_skill(s) for s in candidate_skills if s]
        while stack:
            skill = stack.pop()
            key = normalize_skill_key(skill)
            if key in keys:
                continue
            keys.add(key)
            stack.extend(implied_skills(skill))
        return keys

    def match(self, candidate_skills, required_skills):
        required = []
        for skill in required_skills or []:
            name = canonical_skill(skill)
            if name and name not in required:
                required.append(name)
        if not required:
            return SkillMatchResult(matched=[], missing=[], skill_match=None)

        have = self.expand(candidate_skills)
        matched = [s for s in required if normalize_skill_key(s) in have]
        missing = [s for s in required if normalize_skill_key(s) not in have]
        pct = round(len(matched) / len(required) * 100, 2)
        return SkillMatchResult(matched=matched, missing=missing, skill_match=pct)
