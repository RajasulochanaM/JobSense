"""MockJobProvider - DEVELOPMENT / TESTING FALLBACK ONLY.

Generates clearly labelled sample listings so the full matching workflow can
be demonstrated without a JSearch API key. Every mock job:
  * has source = "mock" (the UI shows a "Sample listing" badge)
  * uses a company name ending in "(Sample)"
  * starts its description with a MOCK DATA notice
  * has no job_url (there is no real posting to visit)
Mock jobs must never be presented as real opportunities.
"""
import hashlib
from datetime import datetime, timedelta

from .base import BaseJobProvider, JobSearchParams, NormalizedJob

MOCK_NOTICE = ("[MOCK DATA - sample listing generated for development and testing. "
               "This is not a real job posting.]")

TEMPLATES = [
    {"title": "React Developer", "keys": ["react", "frontend", "front end", "javascript", "ui", "web"],
     "skills": "React, JavaScript, TypeScript, HTML, CSS, Redux, REST APIs, Git and Jest",
     "summary": "build responsive single-page applications and reusable UI components"},
    {"title": "Frontend Engineer", "keys": ["frontend", "front end", "ui", "web", "angular", "vue"],
     "skills": "JavaScript, TypeScript, Angular or Vue.js, HTML, CSS, Sass, Webpack, accessibility (WCAG) and Git",
     "summary": "craft accessible, high-performance web interfaces"},
    {"title": "Python Developer", "keys": ["python", "backend", "django", "flask", "software"],
     "skills": "Python, Flask or Django, REST APIs, MySQL or PostgreSQL, Git, Docker and pytest",
     "summary": "develop backend services and data-driven APIs"},
    {"title": "Backend Engineer (Node.js)", "keys": ["node", "backend", "javascript", "api", "software"],
     "skills": "Node.js, Express.js, JavaScript, TypeScript, MongoDB, MySQL, REST APIs, Docker and AWS",
     "summary": "design scalable APIs and microservices"},
    {"title": "Full Stack Developer", "keys": ["full stack", "fullstack", "web", "software", "react", "node"],
     "skills": "React, Node.js, JavaScript, TypeScript, MySQL, MongoDB, REST APIs, Git, Docker and AWS",
     "summary": "own features end to end, from database to user interface"},
    {"title": "Java Developer", "keys": ["java", "spring", "backend", "software"],
     "skills": "Java, Spring Boot, Hibernate, Microservices, SQL, REST APIs, JUnit, Git and Jenkins",
     "summary": "build enterprise backend applications"},
    {"title": "Software Engineer", "keys": ["software", "engineer", "developer", "sde", "programmer"],
     "skills": "Data Structures, Algorithms, OOP, Java or Python, SQL, Git, Linux and System Design",
     "summary": "design, develop and test software components"},
    {"title": "Data Analyst", "keys": ["data", "analyst", "analytics", "sql", "excel", "power bi"],
     "skills": "SQL, Microsoft Excel, Power BI, Tableau, Python, Pandas, statistics and data visualization",
     "summary": "turn business data into dashboards and insights"},
    {"title": "Data Scientist", "keys": ["data", "scientist", "machine learning", "ml", "ai"],
     "skills": "Python, Machine Learning, scikit-learn, Pandas, NumPy, statistics, SQL, TensorFlow and Jupyter",
     "summary": "build predictive models and run experiments"},
    {"title": "Machine Learning Engineer", "keys": ["machine learning", "ml", "ai", "deep learning", "mlops"],
     "skills": "Python, Machine Learning, Deep Learning, PyTorch, TensorFlow, MLOps, Docker, AWS and SQL",
     "summary": "train, deploy and monitor ML models in production"},
    {"title": "NLP Engineer", "keys": ["nlp", "language", "ai", "ml", "text"],
     "skills": "Python, NLP, spaCy, NLTK, Hugging Face transformers, Machine Learning, PyTorch and REST APIs",
     "summary": "build text classification and information extraction pipelines"},
    {"title": "DevOps Engineer", "keys": ["devops", "cloud", "sre", "infrastructure", "docker", "kubernetes"],
     "skills": "Linux, Docker, Kubernetes, Terraform, Jenkins, CI/CD, AWS, Bash, Git and monitoring with Prometheus",
     "summary": "automate build, release and infrastructure"},
    {"title": "Cloud Engineer", "keys": ["cloud", "aws", "azure", "gcp", "infrastructure"],
     "skills": "AWS, Azure, Terraform, Linux, networking, Docker, Kubernetes, Python and IAM",
     "summary": "design and operate secure cloud infrastructure"},
    {"title": "QA Engineer", "keys": ["qa", "test", "testing", "quality"],
     "skills": "Software testing, test cases, regression testing, API testing with Postman, SQL, Jira and Agile",
     "summary": "ensure product quality through structured testing"},
    {"title": "Automation Test Engineer", "keys": ["automation", "test", "testing", "qa", "selenium"],
     "skills": "Selenium, Java or Python, Test Automation, Cypress, TestNG, API testing, CI/CD, Git and Cucumber (BDD)",
     "summary": "build and maintain automated test suites"},
    {"title": "Cybersecurity Analyst", "keys": ["security", "cyber", "soc", "analyst", "infosec"],
     "skills": "Cybersecurity, SIEM (Splunk), incident response, vulnerability assessment, networking, firewalls, "
               "Linux and Wireshark",
     "summary": "monitor, detect and respond to security threats"},
    {"title": "Android Developer", "keys": ["android", "mobile", "kotlin", "app"],
     "skills": "Kotlin, Java, Android SDK, REST APIs, Firebase, Git and unit testing",
     "summary": "build native Android applications"},
]

COMPANIES = ["Northwind Labs", "Bluepeak Systems", "Kaveri Tech", "Lotus Digital", "Monsoon Analytics",
             "Indigo Softworks", "Saffron Cloud", "Coromandel Data", "Deccan Apps", "Teal River Tech"]
CITIES = ["Chennai", "Bengaluru", "Hyderabad", "Mumbai", "Pune", "Noida", "Kochi", "Coimbatore"]
TYPES = ["Full-time", "Full-time", "Full-time", "Contract", "Internship"]
PAGE_SIZE = 10
MAX_PAGES = 3


def _seed(*parts):
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:8], 16)


class MockJobProvider(BaseJobProvider):
    name = "mock"
    is_mock = True

    def _select_templates(self, query):
        q = query.lower()
        ranked = sorted(TEMPLATES, key=lambda t: (-sum(1 for k in t["keys"] if k in q) - (2 if t["title"].lower() in q else 0),
                                                  TEMPLATES.index(t)))
        hits = [t for t in ranked if any(k in q for k in t["keys"]) or t["title"].lower() in q]
        return hits or ranked

    def search(self, params: JobSearchParams):
        page = max(1, int(params.page))
        if page > MAX_PAGES or not params.query.strip():
            return []
        templates = self._select_templates(params.query)
        location_input = params.location.strip()
        jobs = []
        for i in range(PAGE_SIZE):
            n = (page - 1) * PAGE_SIZE + i
            tpl = templates[n % len(templates)]
            seed = _seed(params.query.lower(), location_input.lower(), str(n))
            company = COMPANIES[seed % len(COMPANIES)]
            city = location_input.title() if location_input else CITIES[(seed // 7) % len(CITIES)]
            remote = bool(params.remote) or (seed % 5 == 0)
            employment = TYPES[(seed // 11) % len(TYPES)]
            if params.employment_type:
                employment = {"FULLTIME": "Full-time", "PARTTIME": "Part-time", "CONTRACTOR": "Contract",
                              "INTERN": "Internship"}.get(params.employment_type.upper(), employment)
            years = [0, 1, 2, 3, 5][(seed // 13) % 5]
            if params.max_experience_years is not None:
                cap = params.max_experience_years
                years = 0 if cap == 0 else (min(years, cap) if cap < 3 else min(max(years, 3), cap))
            elif params.experience == "no_experience":
                years = 0
            elif params.experience == "under_3_years_experience":
                years = min(years, 2)
            elif params.experience == "more_than_3_years_experience":
                years = max(years, 3)
            seniority = "Junior " if years <= 1 else ("Senior " if years >= 5 else "")
            title = f"{seniority}{tpl['title']}"
            description = (
                f"{MOCK_NOTICE}\n\n"
                f"{company} (Sample) is hiring a {title} in {city}{' (remote friendly)' if remote else ''}. "
                f"You will {tpl['summary']} and collaborate with product and design teams.\n\n"
                f"Requirements: {years}+ years of experience. Hands-on skills in {tpl['skills']}. "
                f"Good communication and problem solving skills.\n\n"
                f"Nice to have: experience working in an Agile team."
            )
            posted = datetime.utcnow() - timedelta(days=seed % 21, hours=seed % 24)
            jobs.append(NormalizedJob(
                external_job_id=f"mock-{seed:08x}-{n}",
                title=title,
                company=f"{company} (Sample)",
                location=f"{city}, India" if city.lower() != "india" else "India",
                country="IN",
                description=description,
                job_url=None,
                employment_type=employment,
                remote=remote,
                source="mock",
                publisher="JobSense mock provider",
                posted_at=posted.replace(microsecond=0).isoformat(),
                min_experience_years=float(years),
            ))
        if params.remote:
            jobs = [j for j in jobs if j.remote]
        return jobs
