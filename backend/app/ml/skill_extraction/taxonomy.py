"""Skill taxonomy - the single source of truth for skill extraction and normalisation.

Each entry:
    name       canonical display name (what users see and what is stored)
    category   grouping used in the UI / analytics
    aliases    case-insensitive surface forms that always map to this skill
    ambiguous  surface forms that are ordinary English words (e.g. "go", "react",
               "spring"). They are only accepted when another unambiguous skill
               appears nearby, which avoids false positives such as
               "we react quickly" or "spring internship".
    implies    skills that are logically covered by this one (MySQL -> SQL);
               used during skill matching, never stored as extracted skills.

`database/seed.sql` is generated from this file by `backend/scripts/generate_seed.py`.
"""

SKILLS = [
    # ---------------- Programming languages ----------------
    {"name": "Python", "category": "Programming Languages", "aliases": ["python", "python3", "python 3", "python2", "py3"]},
    {"name": "Java", "category": "Programming Languages", "aliases": ["java", "java8", "java 8", "java 11", "java 17", "core java", "j2ee", "java ee"]},
    {"name": "JavaScript", "category": "Programming Languages", "aliases": ["javascript", "java script", "es6", "es2015", "ecmascript", "vanilla js"], "ambiguous": ["js"]},
    {"name": "TypeScript", "category": "Programming Languages", "aliases": ["typescript", "type script"], "ambiguous": ["ts"], "implies": ["JavaScript"]},
    {"name": "C++", "category": "Programming Languages", "aliases": ["c++", "cpp", "c plus plus"]},
    {"name": "C#", "category": "Programming Languages", "aliases": ["c#", "csharp", "c sharp"]},
    {"name": "C", "category": "Programming Languages", "aliases": ["c programming", "ansi c", "embedded c"], "ambiguous": ["C"]},
    {"name": "Go", "category": "Programming Languages", "aliases": ["golang"], "ambiguous": ["Go"]},
    {"name": "Rust", "category": "Programming Languages", "aliases": ["rustlang"], "ambiguous": ["rust"]},
    {"name": "Kotlin", "category": "Programming Languages", "aliases": ["kotlin"]},
    {"name": "Swift", "category": "Programming Languages", "aliases": ["swiftui"], "ambiguous": ["swift"]},
    {"name": "PHP", "category": "Programming Languages", "aliases": ["php", "php7", "php8"]},
    {"name": "Ruby", "category": "Programming Languages", "aliases": [], "ambiguous": ["ruby"]},
    {"name": "R", "category": "Programming Languages", "aliases": ["r programming", "rstudio"], "ambiguous": ["R"]},
    {"name": "Scala", "category": "Programming Languages", "aliases": ["scala"]},
    {"name": "Dart", "category": "Programming Languages", "aliases": [], "ambiguous": ["dart"]},
    {"name": "Bash", "category": "Programming Languages", "aliases": ["bash", "shell scripting", "shell script", "bash scripting"]},
    {"name": "PowerShell", "category": "Programming Languages", "aliases": ["powershell"]},
    {"name": "MATLAB", "category": "Programming Languages", "aliases": ["matlab"]},

    # ---------------- Frontend ----------------
    {"name": "HTML", "category": "Frontend", "aliases": ["html", "html5", "html 5"]},
    {"name": "CSS", "category": "Frontend", "aliases": ["css", "css3", "css 3"]},
    {"name": "React", "category": "Frontend", "aliases": ["reactjs", "react.js", "react js", "react hooks", "react 18"], "ambiguous": ["react"], "implies": ["JavaScript"]},
    {"name": "Redux", "category": "Frontend", "aliases": ["redux", "redux toolkit"]},
    {"name": "Next.js", "category": "Frontend", "aliases": ["next.js", "nextjs", "next js"], "implies": ["React"]},
    {"name": "Angular", "category": "Frontend", "aliases": ["angular", "angularjs", "angular.js"], "implies": ["TypeScript"]},
    {"name": "Vue.js", "category": "Frontend", "aliases": ["vue", "vue.js", "vuejs", "vue js", "nuxt"]},
    {"name": "jQuery", "category": "Frontend", "aliases": ["jquery"]},
    {"name": "Bootstrap", "category": "Frontend", "aliases": ["bootstrap"]},
    {"name": "Tailwind CSS", "category": "Frontend", "aliases": ["tailwind", "tailwindcss", "tailwind css"]},
    {"name": "Sass", "category": "Frontend", "aliases": ["sass", "scss"]},
    {"name": "Webpack", "category": "Frontend", "aliases": ["webpack"]},
    {"name": "Vite", "category": "Frontend", "aliases": ["vitejs"], "ambiguous": ["vite"]},
    {"name": "Responsive Design", "category": "Frontend", "aliases": ["responsive design", "responsive web design", "mobile-first design"]},
    {"name": "Accessibility", "category": "Frontend", "aliases": ["web accessibility", "wcag", "a11y"]},

    # ---------------- Backend ----------------
    {"name": "Node.js", "category": "Backend", "aliases": ["node.js", "nodejs", "node js"], "ambiguous": ["node"], "implies": ["JavaScript"]},
    {"name": "Express.js", "category": "Backend", "aliases": ["express.js", "expressjs", "express js"], "ambiguous": ["express"], "implies": ["Node.js"]},
    {"name": "Flask", "category": "Backend", "aliases": ["flask"], "implies": ["Python"]},
    {"name": "Django", "category": "Backend", "aliases": ["django", "django rest framework", "drf"], "implies": ["Python"]},
    {"name": "FastAPI", "category": "Backend", "aliases": ["fastapi", "fast api"], "implies": ["Python"]},
    {"name": "Spring Boot", "category": "Backend", "aliases": ["spring boot", "springboot", "spring framework", "spring mvc"], "ambiguous": ["spring"], "implies": ["Java"]},
    {"name": "Hibernate", "category": "Backend", "aliases": ["hibernate", "jpa"]},
    {"name": ".NET", "category": "Backend", "aliases": [".net", "dotnet", "asp.net", ".net core", "asp.net core"]},
    {"name": "Laravel", "category": "Backend", "aliases": ["laravel"], "implies": ["PHP"]},
    {"name": "Ruby on Rails", "category": "Backend", "ambiguous": ["rails"], "aliases": ["ruby on rails", "ror"]},
    {"name": "REST APIs", "category": "Backend", "ambiguous": ["rest"], "aliases": ["rest api", "rest apis", "restful", "restful api", "restful apis", "restful services", "rest services", "api development"]},
    {"name": "GraphQL", "category": "Backend", "aliases": ["graphql"]},
    {"name": "Microservices", "category": "Backend", "aliases": ["microservices", "microservice", "micro services", "microservice architecture"]},
    {"name": "gRPC", "category": "Backend", "aliases": ["grpc"]},

    # ---------------- Databases ----------------
    {"name": "SQL", "category": "Databases", "aliases": ["sql", "t-sql", "tsql", "pl/sql", "plsql", "structured query language"]},
    {"name": "MySQL", "category": "Databases", "aliases": ["mysql", "my sql"], "implies": ["SQL"]},
    {"name": "PostgreSQL", "category": "Databases", "aliases": ["postgresql", "postgres", "psql"], "implies": ["SQL"]},
    {"name": "SQL Server", "category": "Databases", "aliases": ["sql server", "mssql", "ms sql", "microsoft sql server"], "implies": ["SQL"]},
    {"name": "Oracle Database", "category": "Databases", "aliases": ["oracle database", "oracle db", "oracle sql"], "implies": ["SQL"]},
    {"name": "SQLite", "category": "Databases", "aliases": ["sqlite"], "implies": ["SQL"]},
    {"name": "MongoDB", "category": "Databases", "aliases": ["mongodb", "mongo db", "mongoose"]},
    {"name": "Redis", "category": "Databases", "aliases": ["redis"]},
    {"name": "Elasticsearch", "category": "Databases", "aliases": ["elasticsearch", "elastic search", "elk stack"]},
    {"name": "Cassandra", "category": "Databases", "aliases": ["cassandra"]},
    {"name": "Firebase", "category": "Databases", "aliases": ["firebase", "firestore"]},
    {"name": "DynamoDB", "category": "Databases", "aliases": ["dynamodb"]},
    {"name": "Database Design", "category": "Databases", "aliases": ["database design", "data modeling", "data modelling", "database normalization", "er diagrams"]},

    # ---------------- Cloud & DevOps ----------------
    {"name": "AWS", "category": "Cloud", "aliases": ["aws", "amazon web services", "ec2", "s3", "aws lambda", "cloudformation"]},
    {"name": "Azure", "category": "Cloud", "aliases": ["azure", "microsoft azure", "azure devops"]},
    {"name": "Google Cloud", "category": "Cloud", "aliases": ["gcp", "google cloud", "google cloud platform", "bigquery"]},
    {"name": "Docker", "category": "DevOps", "aliases": ["docker", "dockerfile", "docker compose", "docker-compose", "containerization"]},
    {"name": "Kubernetes", "category": "DevOps", "ambiguous": ["helm"], "aliases": ["kubernetes", "k8s", "eks", "aks", "gke"]},
    {"name": "Terraform", "category": "DevOps", "aliases": ["terraform", "infrastructure as code", "iac"]},
    {"name": "Ansible", "category": "DevOps", "aliases": ["ansible"]},
    {"name": "Jenkins", "category": "DevOps", "aliases": ["jenkins"]},
    {"name": "CI/CD", "category": "DevOps", "aliases": ["ci/cd", "ci cd", "cicd", "continuous integration", "continuous delivery", "continuous deployment", "github actions", "gitlab ci"]},
    {"name": "Linux", "category": "DevOps", "aliases": ["linux", "unix", "ubuntu", "centos", "red hat", "rhel"]},
    {"name": "Nginx", "category": "DevOps", "aliases": ["nginx"]},
    {"name": "Monitoring", "category": "DevOps", "aliases": ["prometheus", "grafana", "datadog", "new relic", "observability"]},
    {"name": "Networking", "category": "DevOps", "aliases": ["networking", "tcp/ip", "dns", "computer networks", "network administration"]},

    # ---------------- Version control & tools ----------------
    {"name": "Git", "category": "Tools", "aliases": ["git", "version control", "gitlab", "bitbucket"]},
    {"name": "GitHub", "category": "Tools", "aliases": ["github"], "implies": ["Git"]},
    {"name": "Jira", "category": "Tools", "aliases": ["jira", "confluence"]},
    {"name": "Postman", "category": "Tools", "aliases": ["postman"]},
    {"name": "Agile", "category": "Practices", "aliases": ["agile", "scrum", "kanban", "agile methodology", "sprint planning"]},

    # ---------------- Data ----------------
    {"name": "Data Analysis", "category": "Data", "aliases": ["data analysis", "data analytics", "exploratory data analysis", "eda", "data analyst"]},
    {"name": "Excel", "category": "Data", "ambiguous": ["excel"], "aliases": ["ms excel", "microsoft excel", "advanced excel", "vlookup", "pivot tables"]},
    {"name": "Power BI", "category": "Data", "aliases": ["power bi", "powerbi", "dax"]},
    {"name": "Tableau", "category": "Data", "aliases": ["tableau"]},
    {"name": "Pandas", "category": "Data", "aliases": ["pandas"], "implies": ["Python"]},
    {"name": "NumPy", "category": "Data", "aliases": ["numpy"], "implies": ["Python"]},
    {"name": "Matplotlib", "category": "Data", "aliases": ["matplotlib", "seaborn", "plotly"]},
    {"name": "Statistics", "category": "Data", "aliases": ["statistics", "statistical analysis", "hypothesis testing", "probability", "regression analysis"]},
    {"name": "Data Visualization", "category": "Data", "aliases": ["data visualization", "data visualisation"]},
    {"name": "ETL", "category": "Data", "aliases": ["etl", "elt", "data pipelines", "data pipeline", "data warehousing", "data warehouse"]},
    {"name": "Apache Spark", "category": "Data", "ambiguous": ["spark"], "aliases": ["apache spark", "pyspark"]},
    {"name": "Hadoop", "category": "Data", "ambiguous": ["hive"], "aliases": ["hadoop", "hdfs", "mapreduce"]},
    {"name": "Apache Airflow", "category": "Data", "aliases": ["airflow", "apache airflow"]},

    # ---------------- AI / ML ----------------
    {"name": "Machine Learning", "category": "AI/ML", "ambiguous": ["ML"], "aliases": ["machine learning", "supervised learning", "unsupervised learning", "predictive modeling", "predictive modelling"]},
    {"name": "Deep Learning", "category": "AI/ML", "aliases": ["deep learning", "neural networks", "neural network", "cnn", "rnn", "lstm"], "implies": ["Machine Learning"]},
    {"name": "NLP", "category": "AI/ML", "aliases": ["nlp", "natural language processing", "text mining", "text classification", "named entity recognition"]},
    {"name": "Computer Vision", "category": "AI/ML", "aliases": ["computer vision", "opencv", "image processing", "object detection"]},
    {"name": "TensorFlow", "category": "AI/ML", "aliases": ["tensorflow", "tensor flow", "keras"], "implies": ["Deep Learning"]},
    {"name": "PyTorch", "category": "AI/ML", "ambiguous": ["torch"], "aliases": ["pytorch"], "implies": ["Deep Learning"]},
    {"name": "scikit-learn", "category": "AI/ML", "aliases": ["scikit-learn", "scikit learn", "sklearn"], "implies": ["Machine Learning"]},
    {"name": "spaCy", "category": "AI/ML", "aliases": ["spacy"], "implies": ["NLP"]},
    {"name": "NLTK", "category": "AI/ML", "aliases": ["nltk"], "implies": ["NLP"]},
    {"name": "Hugging Face", "category": "AI/ML", "aliases": ["hugging face", "huggingface", "bert"], "implies": ["NLP"]},
    {"name": "MLOps", "category": "AI/ML", "aliases": ["mlops", "mlflow", "kubeflow", "model deployment"]},
    {"name": "Feature Engineering", "category": "AI/ML", "aliases": ["feature engineering", "feature selection"]},
    {"name": "Jupyter", "category": "AI/ML", "aliases": ["jupyter", "jupyter notebook", "jupyterlab", "google colab"]},

    # ---------------- Testing / QA ----------------
    {"name": "Software Testing", "category": "Testing", "aliases": ["software testing", "manual testing", "test cases", "test planning", "qa testing", "quality assurance", "functional testing", "regression testing"]},
    {"name": "Test Automation", "category": "Testing", "aliases": ["test automation", "automation testing", "automated testing"]},
    {"name": "Selenium", "category": "Testing", "aliases": ["selenium", "selenium webdriver", "webdriver"], "implies": ["Test Automation"]},
    {"name": "Cypress", "category": "Testing", "aliases": ["cypress"], "implies": ["Test Automation"]},
    {"name": "Playwright", "category": "Testing", "aliases": ["playwright"], "implies": ["Test Automation"]},
    {"name": "JUnit", "category": "Testing", "aliases": ["junit", "testng", "mockito"]},
    {"name": "pytest", "category": "Testing", "aliases": ["pytest", "unittest"]},
    {"name": "Jest", "category": "Testing", "ambiguous": ["mocha", "chai"], "aliases": ["jest", "react testing library", "vitest"]},
    {"name": "Unit Testing", "category": "Testing", "aliases": ["unit testing", "unit tests", "tdd", "test driven development", "test-driven development"]},
    {"name": "API Testing", "category": "Testing", "aliases": ["api testing", "rest assured", "soapui"]},
    {"name": "Performance Testing", "category": "Testing", "aliases": ["performance testing", "load testing", "jmeter", "locust"]},
    {"name": "Cucumber", "category": "Testing", "aliases": ["cucumber", "bdd", "gherkin"]},

    # ---------------- Security ----------------
    {"name": "Cybersecurity", "category": "Security", "aliases": ["cybersecurity", "cyber security", "information security", "infosec", "network security"]},
    {"name": "Penetration Testing", "category": "Security", "aliases": ["penetration testing", "pen testing", "pentesting", "ethical hacking", "vapt", "burp suite", "metasploit"]},
    {"name": "SIEM", "category": "Security", "aliases": ["siem", "splunk", "qradar", "security monitoring"]},
    {"name": "Vulnerability Assessment", "category": "Security", "aliases": ["vulnerability assessment", "vulnerability management", "nessus", "owasp"]},
    {"name": "Incident Response", "category": "Security", "aliases": ["incident response", "threat hunting", "threat analysis", "soc"]},
    {"name": "Firewalls", "category": "Security", "aliases": ["firewall", "firewalls", "ids/ips", "intrusion detection"]},
    {"name": "Wireshark", "category": "Security", "aliases": ["wireshark", "packet analysis", "nmap"]},
    {"name": "Cryptography", "category": "Security", "aliases": ["cryptography", "encryption", "pki", "ssl/tls"]},
    {"name": "IAM", "category": "Security", "aliases": ["iam", "identity and access management", "oauth", "oauth2", "jwt", "sso", "active directory"]},

    # ---------------- Mobile ----------------
    {"name": "Android", "category": "Mobile", "aliases": ["android", "android sdk", "android studio"]},
    {"name": "iOS", "category": "Mobile", "aliases": ["ios", "xcode"]},
    {"name": "React Native", "category": "Mobile", "aliases": ["react native", "react-native"], "implies": ["React"]},
    {"name": "Flutter", "category": "Mobile", "aliases": ["flutter"], "implies": ["Dart"]},

    # ---------------- CS fundamentals & soft skills ----------------
    {"name": "Data Structures", "category": "Fundamentals", "aliases": ["data structures", "data structures and algorithms", "dsa"]},
    {"name": "Algorithms", "category": "Fundamentals", "aliases": ["algorithms", "algorithm design"]},
    {"name": "OOP", "category": "Fundamentals", "aliases": ["oop", "oops", "object oriented programming", "object-oriented programming", "object oriented design"]},
    {"name": "System Design", "category": "Fundamentals", "aliases": ["system design", "software architecture", "distributed systems", "scalable systems", "design patterns"]},
    {"name": "Communication", "category": "Soft Skills", "aliases": ["communication skills", "verbal communication", "written communication", "stakeholder communication"]},
    {"name": "Problem Solving", "category": "Soft Skills", "aliases": ["problem solving", "problem-solving", "analytical skills", "critical thinking"]},
    {"name": "Teamwork", "category": "Soft Skills", "aliases": ["teamwork", "team player", "collaboration", "cross-functional"]},
]


def _build_indexes():
    by_key = {}
    for entry in SKILLS:
        entry.setdefault("aliases", [])
        entry.setdefault("ambiguous", [])
        entry.setdefault("implies", [])
        by_key[entry["name"].lower()] = entry
    return by_key


SKILL_INDEX = _build_indexes()


def normalize_skill_key(name):
    return (name or "").strip().lower()


def canonical_skill(name):
    """Map any known alias/name to its canonical name; unknown skills are title-cased as typed."""
    key = normalize_skill_key(name)
    if key in SKILL_INDEX:
        return SKILL_INDEX[key]["name"]
    for entry in SKILLS:
        if key in (a.lower() for a in entry["aliases"]) or key in (a.lower() for a in entry["ambiguous"]):
            return entry["name"]
    return (name or "").strip()


def skill_category(name):
    entry = SKILL_INDEX.get(normalize_skill_key(name))
    return entry["category"] if entry else "Other"


def implied_skills(name):
    entry = SKILL_INDEX.get(normalize_skill_key(name))
    return list(entry["implies"]) if entry else []
