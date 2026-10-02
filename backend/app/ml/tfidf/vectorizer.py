"""TF-IDF vectorisation (scikit-learn TfidfVectorizer).

Input documents are already normalised by TextPreprocessor (lower-cased,
lemmatised, stop words removed, skill phrases protected as single tokens),
so the vectorizer only needs to split on whitespace.
"""
from sklearn.feature_extraction.text import TfidfVectorizer


def build_vectorizer():
    return TfidfVectorizer(
        tokenizer=str.split,       # documents are pre-tokenised
        token_pattern=None,
        lowercase=False,
        # Unigrams: multi-word skills ("machine learning", "rest api") are already
        # protected as single skill_* tokens by the preprocessor; in evaluation,
        # adding bigrams diluted the overlap between resumes and job ads.
        ngram_range=(1, 1),
        sublinear_tf=True,         # 1 + log(tf) dampens repeated words
        smooth_idf=True,
        norm="l2",
    )


def vectorize(documents):
    """Fit a vectorizer on `documents` and return (vectorizer, sparse matrix)."""
    vectorizer = build_vectorizer()
    matrix = vectorizer.fit_transform(documents)
    return vectorizer, matrix


def top_terms(vectorizer, vector, limit=10):
    """Highest-weighted terms of one TF-IDF row - used to explain a similarity score."""
    features = vectorizer.get_feature_names_out()
    row = vector.tocoo()
    pairs = sorted(zip(row.col, row.data), key=lambda p: p[1], reverse=True)[:limit]
    return [(features[i], round(float(w), 4)) for i, w in pairs]
