import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.ml.career.career_recommender import CareerRecommender
from app.ml.matching.job_match_scorer import JobMatchScorer, combine_scores
from app.ml.matching.skill_matcher import SkillMatcher
from app.ml.similarity.text_similarity import TextSimilarityCalculator
from app.ml.tfidf.vectorizer import vectorize


def test_tfidf_vectorization_shape_and_norm():
    vectorizer, matrix = vectorize(["python flask api", "react javascript api"])
    assert matrix.shape[0] == 2
    assert set(vectorizer.get_feature_names_out()) == {"python", "flask", "api", "react", "javascript"}
    # rows are L2-normalised
    assert pytest.approx((matrix[0].multiply(matrix[0])).sum(), rel=1e-6) == 1.0


def test_cosine_similarity_bounds_and_identity():
    calc = TextSimilarityCalculator()
    assert calc.cosine("python flask api", "python flask api") == pytest.approx(1.0)
    assert calc.cosine("python flask", "react css") == 0.0
    assert calc.cosine("", "python") == 0.0
    mid = calc.cosine("python flask api", "python django api")
    assert 0 < mid < 1


def test_cosine_matches_sklearn_reference():
    a, b = "python flask mysql api", "python django postgresql api"
    v = TfidfVectorizer(tokenizer=str.split, token_pattern=None, lowercase=False, sublinear_tf=True)
    m = v.fit_transform([a, b])
    expected = cosine_similarity(m[0:1], m[1:2])[0][0]
    assert TextSimilarityCalculator.cosine(a, b) == pytest.approx(expected)


def test_similarity_percent_from_raw_text():
    calc = TextSimilarityCalculator()
    pct = calc.similarity_from_raw("Python developer building Flask REST APIs",
                                   "We need a Python developer with Flask and REST API experience")
    assert 0 < pct <= 100


def test_skill_match_example_from_specification():
    result = SkillMatcher().match(["React", "JavaScript", "Node.js", "MySQL"],
                                  ["React", "JavaScript", "Node.js", "TypeScript", "AWS"])
    assert result.matched == ["React", "JavaScript", "Node.js"]
    assert result.missing == ["TypeScript", "AWS"]
    assert result.skill_match == 60.0


def test_skill_match_uses_implied_skills_and_handles_empty():
    result = SkillMatcher().match(["MySQL"], ["SQL"])
    assert result.matched == ["SQL"] and result.skill_match == 100.0
    empty = SkillMatcher().match(["Python"], [])
    assert empty.skill_match is None and empty.matched == [] and empty.missing == []


def test_final_score_formula_and_bounds():
    assert combine_scores(80, 60, 0.4, 0.6) == pytest.approx(0.4 * 80 + 0.6 * 60)
    assert combine_scores(82, 75, 0.4, 0.6) == pytest.approx(77.8)
    assert combine_scores(50, None, 0.4, 0.6) == 50           # no skill data -> text similarity only
    assert combine_scores(100, 100, 2, 3) == 100               # weights are normalised
    assert 0 <= combine_scores(0, 0, 0.4, 0.6) <= 100


def test_scorer_rejects_invalid_weights():
    with pytest.raises(ValueError):
        JobMatchScorer(0, 0)
    with pytest.raises(ValueError):
        JobMatchScorer(-1, 1)


def test_job_ranking_orders_by_final_score():
    scorer = JobMatchScorer(0.4, 0.6)
    calc = scorer.similarity
    resume = calc.preprocess("React developer skilled in JavaScript, HTML, CSS and Node.js")
    jobs = [
        {"id": "java", "processed_text": calc.preprocess("Java Spring Boot developer with Hibernate"),
         "required_skills": ["Java", "Spring Boot", "Hibernate"]},
        {"id": "react", "processed_text": calc.preprocess("React developer with JavaScript, HTML and CSS"),
         "required_skills": ["React", "JavaScript", "HTML", "CSS", "TypeScript"]},
    ]
    ranked = scorer.rank(resume, ["React", "JavaScript", "HTML", "CSS", "Node.js"], jobs)
    assert ranked[0][0]["id"] == "react"
    top = ranked[0][1]
    assert top.missing_skills == ["TypeScript"]
    assert top.skill_match == 80.0
    assert 0 <= top.final_score <= 100
    assert ranked[1][1].final_score < top.final_score


def test_career_recommender_prefers_skill_evidence_over_interest():
    careers = [
        {"career_id": 1, "career_name": "Frontend Developer", "description": "Builds web interfaces",
         "interest_area": "Web Development",
         "skills": [{"skill_name": "React", "importance": 3}, {"skill_name": "JavaScript", "importance": 3},
                    {"skill_name": "TypeScript", "importance": 2}]},
        {"career_id": 2, "career_name": "Cybersecurity Analyst", "description": "Protects systems",
         "interest_area": "Cybersecurity",
         "skills": [{"skill_name": "Cybersecurity", "importance": 3}, {"skill_name": "SIEM", "importance": 2}]},
    ]
    rec = CareerRecommender()
    results = rec.recommend(careers, ["React", "JavaScript"], "skill_react skill_javascript web",
                            interests=["Cybersecurity"])
    assert results[0].career_id == 1
    frontend, security = results
    assert frontend.skill_alignment == pytest.approx(6 / 8 * 100)
    assert [m["skill"] for m in frontend.missing_skills] == ["TypeScript"]
    # interest alone contributes nothing without any matching skills
    assert security.interest_match is True and security.match_score == 0
    assert frontend.reasons
