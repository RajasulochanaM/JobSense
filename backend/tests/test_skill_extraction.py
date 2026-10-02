from app.ml.preprocessing.text_preprocessor import normalize_text, get_preprocessor, skill_token
from app.ml.skill_extraction.skill_extractor import get_skill_extractor
from app.ml.skill_extraction.taxonomy import canonical_skill


def extract(text):
    return get_skill_extractor().extract(text)


def test_basic_skill_detection():
    skills = extract("Experienced with Python, Flask, MySQL, Docker and AWS.")
    assert {"Python", "Flask", "MySQL", "Docker", "AWS"} <= set(skills)


def test_variant_normalization():
    skills = extract("Skills: ReactJS, React.js, NodeJS, JS, Python3, C++, C#, CI/CD")
    assert skills.count("React") == 1          # de-duplicated
    assert "Node.js" in skills
    assert "JavaScript" in skills               # JS -> JavaScript (in a skills context)
    assert "Python" in skills                   # Python3 -> Python
    assert "C++" in skills and "C#" in skills
    assert "CI/CD" in skills


def test_ambiguous_words_need_technical_context():
    assert extract("We react quickly and the rest of the team will excel.") == []
    assert extract("Go to the office. Grade C in chemistry.") == []
    assert "Go" in extract("Languages: Go, Python, Java")
    assert "Node.js" in extract("Built services in Node and TypeScript")


def test_longest_match_wins():
    skills = extract("Mobile apps with React Native and Firebase")
    assert "React Native" in skills
    assert "React" not in skills


def test_canonical_skill_lookup():
    assert canonical_skill("reactjs") == "React"
    assert canonical_skill("NODEJS") == "Node.js"
    assert canonical_skill("k8s") == "Kubernetes"
    assert canonical_skill("Some Unknown Skill") == "Some Unknown Skill"


def test_preprocessing_removes_noise_and_lemmatizes():
    text = "Contact: jane@example.com, https://jane.dev. Developed REST APIs using Node.js for 3 years!"
    processed = get_preprocessor().preprocess(text)
    tokens = processed.split()
    assert "jane@example.com" not in processed and "https" not in processed
    assert skill_token("REST APIs") in tokens and skill_token("Node.js") in tokens
    assert "develop" in tokens                  # lemmatised "Developed"
    assert "3" not in tokens and "year" not in tokens
    assert normalize_text("  a\n\n b ") == "a b"
