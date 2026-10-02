"""Dictionary-based skill extraction with spaCy's PhraseMatcher.

Why a taxonomy + PhraseMatcher rather than a statistical model?
  * explainable - every extracted skill traces back to a known alias
  * deterministic and fast
  * normalises variants (ReactJS / React.js -> React, NodeJS -> Node.js, JS -> JavaScript)

False-positive control:
  * multi-word and punctuation-heavy aliases match case-insensitively
  * ambiguous aliases (plain English words such as "react", "go", "spring",
    single letters "C" / "R") are only accepted when another *unambiguous*
    skill occurs within CONTEXT_WINDOW tokens - i.e. when they appear in a
    technical context such as a skills list
  * overlapping matches keep the longest span ("React Native" beats "React")
"""
import re
import threading

from spacy.matcher import PhraseMatcher
from spacy.util import filter_spans

from ..nlp import get_nlp
from .taxonomy import SKILLS

CONTEXT_WINDOW = 8

# Characters that commonly glue skills together in resumes ("React/Redux", "Python|SQL").
SEPARATORS_RE = re.compile(r"[/|\\,;:()\[\]{}<>•·●▪]")


def prepare_text(text):
    text = SEPARATORS_RE.sub(" , ", text or "")
    # "React.js." at the end of a sentence -> keep the alias intact but detach the full stop.
    text = re.sub(r"(\w)\.(\s|$)", r"\1 .\2", text)
    return re.sub(r"[ \t]+", " ", text)


class SkillExtractor:
    def __init__(self, skills=None):
        self.skills = skills or SKILLS
        self.nlp = get_nlp()
        self._build_matchers()

    def _build_matchers(self):
        def make_doc(alias):
            return self.nlp.make_doc(prepare_text(alias).strip())

        self.lower_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self.ambiguous_lower = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self.ambiguous_exact = PhraseMatcher(self.nlp.vocab, attr="ORTH")
        self.label_to_skill = {}
        for idx, entry in enumerate(self.skills):
            label = f"SKILL_{idx}"
            self.label_to_skill[self.nlp.vocab.strings.add(label)] = entry["name"]
            aliases = {entry["name"].lower(), *[a.lower() for a in entry.get("aliases", [])]}
            ambiguous_lower = {a.lower() for a in entry.get("ambiguous", [])}
            aliases -= ambiguous_lower
            if aliases:
                self.lower_matcher.add(label, [make_doc(a) for a in sorted(aliases)])
            exact = [a for a in entry.get("ambiguous", []) if any(ch.isupper() for ch in a)]
            lower = [a for a in entry.get("ambiguous", []) if not any(ch.isupper() for ch in a)]
            if exact:
                self.ambiguous_exact.add(label, [make_doc(a) for a in exact])
            if lower:
                self.ambiguous_lower.add(label, [make_doc(a) for a in lower])

    def find_skill_spans(self, doc):
        """Return [(start_token, end_token, canonical_skill)] for a spaCy Doc."""
        strong = [(doc[s:e], mid) for mid, s, e in self.lower_matcher(doc)]
        weak = [(doc[s:e], mid) for mid, s, e in self.ambiguous_lower(doc)]
        weak += [(doc[s:e], mid) for mid, s, e in self.ambiguous_exact(doc)]

        strong_positions = [span.start for span, _ in strong]
        accepted = list(strong)
        for span, mid in weak:
            if any(abs(span.start - pos) <= CONTEXT_WINDOW for pos in strong_positions):
                accepted.append((span, mid))

        span_label = {}
        spans = []
        for span, mid in accepted:
            span_label[(span.start, span.end)] = mid
            spans.append(span)
        result = []
        for span in filter_spans(spans):
            result.append((span.start, span.end, self.label_to_skill[span_label[(span.start, span.end)]]))
        return sorted(result)

    def extract(self, text):
        """Extract a de-duplicated, ordered list of canonical skills from free text."""
        if not text or not text.strip():
            return []
        doc = self.nlp.make_doc(prepare_text(text))
        seen = []
        for _, _, skill in self.find_skill_spans(doc):
            if skill not in seen:
                seen.append(skill)
        return seen

    def extract_with_counts(self, text):
        counts = {}
        if not text:
            return counts
        doc = self.nlp.make_doc(prepare_text(text))
        for _, _, skill in self.find_skill_spans(doc):
            counts[skill] = counts.get(skill, 0) + 1
        return counts


_instance = None
_lock = threading.Lock()


def get_skill_extractor():
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = SkillExtractor()
    return _instance
