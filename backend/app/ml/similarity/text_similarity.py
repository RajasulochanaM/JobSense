"""TextSimilarityCalculator - TF-IDF + cosine similarity between two texts.

For every candidate/job comparison a TF-IDF model is fitted on the pair
(resume, job description) and cosine similarity is computed between the two
vectors. Fitting per pair makes each score deterministic: the same resume and
job always produce the same percentage, independent of which other jobs were
in the search results. The result is returned as a 0-100 percentage.
"""
from sklearn.metrics.pairwise import cosine_similarity

from ..preprocessing.text_preprocessor import get_preprocessor
from ..tfidf.vectorizer import top_terms, vectorize


class TextSimilarityCalculator:
    def __init__(self, preprocessor=None):
        self.preprocessor = preprocessor or get_preprocessor()

    def preprocess(self, text):
        return self.preprocessor.preprocess(text)

    @staticmethod
    def cosine(processed_a, processed_b):
        """Cosine similarity (0..1) of two *preprocessed* documents."""
        if not processed_a or not processed_b:
            return 0.0
        try:
            _, matrix = vectorize([processed_a, processed_b])
        except ValueError:  # empty vocabulary
            return 0.0
        value = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
        return max(0.0, min(1.0, value))

    def similarity_percent(self, processed_a, processed_b):
        return round(self.cosine(processed_a, processed_b) * 100, 2)

    def similarity_from_raw(self, text_a, text_b):
        return self.similarity_percent(self.preprocess(text_a), self.preprocess(text_b))

    @staticmethod
    def shared_terms(processed_a, processed_b, limit=8):
        """Terms contributing most to the similarity (present in both documents)."""
        if not processed_a or not processed_b:
            return []
        try:
            vectorizer, matrix = vectorize([processed_a, processed_b])
        except ValueError:
            return []
        product = matrix[0].multiply(matrix[1])
        terms = top_terms(vectorizer, product, limit)
        return [t.replace("skill_", "") for t, _ in terms]
