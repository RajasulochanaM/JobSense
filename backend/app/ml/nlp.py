"""Lazily loaded, shared spaCy pipeline.

Loading a spaCy model is the most expensive NLP step, so it happens once per
process. Components we do not need (parser, NER) are disabled for speed; the
tagger/attribute_ruler/lemmatizer remain so tokens can be lemmatised.
"""
import logging
import threading

import spacy

logger = logging.getLogger(__name__)

MODEL_NAME = "en_core_web_sm"
_nlp = None
_lock = threading.Lock()


def get_nlp():
    global _nlp
    if _nlp is None:
        with _lock:
            if _nlp is None:
                try:
                    _nlp = spacy.load(MODEL_NAME, disable=["parser", "ner"])
                    logger.info("Loaded spaCy model %s", MODEL_NAME)
                except OSError:
                    # Fallback keeps the app functional (tokenisation + stop words, no lemmas).
                    logger.warning("spaCy model %s not installed - using blank English pipeline. "
                                   "Run: python -m spacy download %s", MODEL_NAME, MODEL_NAME)
                    _nlp = spacy.blank("en")
                _nlp.max_length = 2_000_000
    return _nlp


def has_lemmatizer():
    return "lemmatizer" in get_nlp().pipe_names
