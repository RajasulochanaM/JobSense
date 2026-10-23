"""Text normalisation pipeline used before TF-IDF vectorisation.

    raw text
      -> normalisation (unicode, lower-case, URLs/emails/phone numbers removed)
      -> skill-phrase protection (e.g. "node.js" -> "skill_nodejs") so that
         punctuation-heavy technical terms survive tokenisation as one token
      -> spaCy tokenisation
      -> noise removal (stop words, punctuation, numbers, 1-char tokens)
      -> lemmatisation ("developed" -> "develop", "APIs" -> "api")
      -> space-joined string of clean tokens
"""
import re
import unicodedata

from ..nlp import get_nlp, has_lemmatizer

URL_RE = re.compile(r"(https?://\S+|www\.\S+)")
EMAIL_RE = re.compile(r"\S+@\S+\.\S+")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
BULLETS_RE = re.compile(r"[•●▪◦■►✓✔➤•●▪]")
MULTISPACE_RE = re.compile(r"\s+")

# Generic resume / job-ad words that carry little discriminative meaning.
DOMAIN_STOPWORDS = {
    "experience", "year", "years", "work", "working", "job", "role", "responsibility",
    "responsibilities", "requirement", "requirements", "skill", "skills", "candidate",
    "company", "team", "strong", "good", "excellent", "ability", "knowledge", "etc",
    "including", "include", "new", "use", "using", "well", "must", "preferred", "plus",
    "looking", "opportunity", "resume", "curriculum", "vitae", "email", "phone", "mobile",
    "address", "linkedin", "github.com", "responsible", "day", "month", "per",
}


def normalize_text(text):
    """Unicode-normalise, strip URLs/emails/phones/bullets and collapse whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", str(text))
    text = URL_RE.sub(" ", text)
    text = EMAIL_RE.sub(" ", text)
    text = PHONE_RE.sub(" ", text)
    text = BULLETS_RE.sub(" ", text)
    text = text.replace(" ", " ")
    return MULTISPACE_RE.sub(" ", text).strip()


def skill_token(skill_name):
    """Turn a canonical skill into a single TF-IDF-safe token, e.g. 'C++' -> 'skill_cplusplus'."""
    s = skill_name.lower().replace("++", "plusplus").replace("#", "sharp").replace(".", "dot")
    s = re.sub(r"[^a-z0-9]+", "", s)
    return f"skill_{s}"


class TextPreprocessor:
    """Converts free text into a normalised token string for TF-IDF."""

    def __init__(self, skill_extractor=None):
        # Imported lazily to avoid a circular import between preprocessing and extraction.
        if skill_extractor is None:
            from ..skill_extraction.skill_extractor import get_skill_extractor
            skill_extractor = get_skill_extractor()
        self.skill_extractor = skill_extractor

    def tokens(self, text):
        text = normalize_text(text)
        if not text:
            return []
        from ..skill_extraction.skill_extractor import prepare_text
        doc = get_nlp()(prepare_text(text))

        # Skill phrases found by the extractor become single protected tokens.
        spans = self.skill_extractor.find_skill_spans(doc)
        protected = {}
        for start, end, skill in spans:
            protected[start] = (end, skill_token(skill))

        use_lemma = has_lemmatizer()
        out = []
        i = 0
        while i < len(doc):
            if i in protected:
                end, tok = protected[i]
                out.append(tok)
                i = end
                continue
            token = doc[i]
            i += 1
            if token.is_stop or token.is_punct or token.is_space or token.like_num \
                    or token.like_url or token.like_email:
                continue
            word = (token.lemma_ if use_lemma and token.lemma_ else token.text).lower().strip()
            word = re.sub(r"[^a-z0-9+#]", "", word)
            if len(word) < 2 or word in DOMAIN_STOPWORDS or word.isdigit():
                continue
            out.append(word)
        return out

    def preprocess(self, text):
        return " ".join(self.tokens(text))


_instance = None


def get_preprocessor():
    global _instance
    if _instance is None:
        _instance = TextPreprocessor()
    return _instance
