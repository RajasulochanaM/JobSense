# JobSense - ML-based Resume & Job Matching System

JobSense helps candidates understand their resume, find relevant jobs and see exactly
which skills to build next. It extracts skills from a PDF/DOCX resume with **spaCy**,
ranks real job postings with **TF-IDF + cosine similarity** combined with **explicit skill
matching**, identifies skill gaps, compares the profile with career paths, and links
missing skills to official learning resources.

> The methodology is classical and explainable NLP. No LLMs, embeddings or vector
> databases are used for scoring. See [docs/ml-methodology.md](docs/ml-methodology.md).

## Features

**Candidates**
- Register / login / logout (Werkzeug-hashed passwords, revocable bearer sessions)
- Resume upload (PDF, DOCX): text extraction, skill extraction, education and experience detection, text preview, replace/delete
- Job search through the OpenWeb Ninja **JSearch** API (India-focused: keyword, location, remote, job type, experience, pagination)
- Explainable match score for every job: **text similarity, skill match, final score, matched skills, missing skills**
- Personalised ranked matches (sort by score or newest) and profile-based "refresh recommendations"
- Skill-gap analysis per job with official learning resources
- Saved jobs, and application tracking (Saved, Applied, Interview, Offer, Rejected, Withdrawn)
- Potential career paths (15 roles) with skill alignment, reasons, gaps and resources
- Profile with experience, education, locations, remote preference, interests and manual skills
- Dashboard: completeness, resume status, top jobs, recent matches, top skills, skill gaps, careers

**Admins**
- Overview statistics, user management (activate/deactivate/delete), stored jobs (incl. bulk-delete of mock jobs)
- Career path and career-skill CRUD, learning resource CRUD
- Analytics: common candidate skills, common missing skills, application status, match statistics

## Architecture

```
Browser -> React (Vite) on Vercel --HTTPS/JSON--> Flask API on Render --> MySQL on Railway
                                                        \--> OpenWeb Ninja JSearch
```

```
jobsense/
├── frontend/            React 19 + Vite, React Router, Axios, Lucide icons, plain CSS
│   └── src/{components,layouts,pages,pages/admin,services,hooks,context,utils,assets}
├── backend/             Flask API
│   ├── app/
│   │   ├── routes/          thin HTTP layer (blueprints)
│   │   ├── services/        business logic / orchestration
│   │   ├── models/          SQL repositories (parameterised queries)
│   │   ├── database/        mysql-connector connection pool
│   │   ├── ml/              preprocessing, skill_extraction, tfidf, similarity, matching, career
│   │   ├── integrations/jobs/  BaseJobProvider, JSearchProvider, MockJobProvider
│   │   ├── auth/            hashing, tokens, @login_required / @admin_required
│   │   ├── config/ utils/   settings, response envelope, validation
│   │   └── cli.py           flask init-db / create-admin
│   ├── scripts/         seed generator + seed data
│   ├── tests/           pytest (unit + MySQL integration)
│   ├── requirements.txt
│   └── run.py
├── database/            schema.sql, seed.sql
├── postman/             JobSense.postman_collection.json (+ local environment)
├── docs/                architecture, database, ml-methodology, api, deployment
├── render.yaml          Render blueprint
└── .env.example
```

More detail: [docs/architecture.md](docs/architecture.md) · [docs/database.md](docs/database.md) ·
[docs/api.md](docs/api.md) · [docs/deployment.md](docs/deployment.md)

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React.js, JavaScript, HTML, CSS, Vite, React Router, Axios, Lucide React |
| Backend | Python 3.12+, Flask, Flask-CORS, Werkzeug |
| Database | MySQL 8 (mysql-connector-python) |
| NLP / ML | spaCy (`en_core_web_sm`), scikit-learn (TfidfVectorizer, cosine_similarity) |
| Resume parsing | pypdf, python-docx |
| HTTP | requests (backend), Axios (frontend) |
| Testing | pytest, Vitest + Testing Library, Postman/Newman |
| Hosting | Vercel (frontend), Render (API), Railway (MySQL) |

## Prerequisites

- Python **3.12+** (tested with 3.12 wheels and 3.14 locally)
- Node.js **20+** and npm
- MySQL **8.0+** server and client
- Optional: an OpenWeb Ninja JSearch API key (without one, the app uses clearly-labelled mock jobs)

## Installation and local setup

```bash
git clone <your-repo-url> jobsense
cd jobsense
```

### 1. MySQL setup

```sql
-- in the mysql client
CREATE DATABASE jobsense CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt          # also installs the spaCy en_core_web_sm model
cp ../.env.example .env                  # Windows: copy ..\.env.example .env
```

Edit `backend/.env`. At minimum set `DB_USER`, `DB_PASSWORD` and `SECRET_KEY`.
The file must be named exactly `.env`; watch out for Notepad saving it as `.env.txt`.

### 3. Database setup (schema + seed)

Either use the CLI (creates the database if needed, then runs both SQL files):

```bash
flask --app run init-db            # asks for confirmation: it recreates all tables
```

or run the files manually:

```bash
mysql -u root -p jobsense < ../database/schema.sql
mysql -u root -p jobsense < ../database/seed.sql
```

The seed creates the admin **admin@jobsense.local / Admin@12345**. Change it, or create
your own admin with `flask --app run create-admin --email you@example.com`.

### 4. Run the backend

```bash
python run.py                      # http://localhost:5000  (health: /api/health)
```

### 5. Frontend

```bash
cd ../frontend
npm install
cp .env.example .env               # VITE_API_URL=http://localhost:5000
npm run dev                        # http://localhost:5173
```

Then open <http://localhost:5173>, create an account, complete your profile, upload a
resume, search for jobs (e.g. "React Developer" in "Chennai"), and explore matches, skill
gaps and career paths.

## Environment variables

Backend (`backend/.env`, full list with comments in [.env.example](.env.example)):

| Variable | Required | Description |
|---|---|---|
| `FLASK_ENV` | | `development` / `production` |
| `SECRET_KEY` | yes (prod) | random secret |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | yes | MySQL connection |
| `DB_SSL_DISABLED` | | `true` (default) / `false` |
| `CORS_ORIGINS` | yes (prod) | comma-separated frontend origins |
| `JOB_PROVIDER` | | `auto` (default) · `jsearch` · `mock` |
| `JSEARCH_API_KEY` | for real jobs | OpenWeb Ninja key (server-side only) |
| `JSEARCH_BASE_URL` | | default `https://api.openwebninja.com/jsearch` |
| `TEXT_SIMILARITY_WEIGHT`, `SKILL_MATCH_WEIGHT` | | match weights (0.40 / 0.60) |
| `CAREER_SKILL_WEIGHT`, `CAREER_TEXT_WEIGHT`, `CAREER_INTEREST_WEIGHT` | | career weights (0.75 / 0.15 / 0.10) |
| `MAX_RESUME_SIZE_MB` | | default 5 |
| `TEST_DB_NAME` | | pytest database (default `jobsense_test`) |

Frontend (`frontend/.env`): only `VITE_API_URL`. Never put secrets in Vite variables.

## Job API setup (JSearch)

1. Get a key from <https://www.openwebninja.com/> (JSearch API).
2. Set `JSEARCH_API_KEY=...` in `backend/.env` and restart the backend.
3. `GET /api/health` shows `"provider": "jsearch"`.

Without a key (`JOB_PROVIDER=auto`), the **MockJobProvider** returns sample jobs, so the whole
workflow can be demonstrated offline. Mock jobs are always labelled: company names end in
"(Sample)", the UI shows a "Sample listing" badge and a development-mode banner, the
description starts with a MOCK DATA notice, and there is no external link. Admins can delete
all mock jobs in one click. Production should use `JOB_PROVIDER=jsearch`.

## Testing

```bash
# Backend: unit tests always run; DB integration tests need MySQL (credentials from backend/.env)
cd backend
pytest                    # creates/rebuilds the separate `jobsense_test` database automatically
```

If MySQL is unreachable, the 14 integration tests are **skipped** with the reason shown, and
the unit tests (NLP, TF-IDF, scoring, parsing, providers) still run.

```bash
# Frontend
cd frontend
npm test                  # Vitest + Testing Library
npm run build             # production build
```

### Postman

Import `postman/JobSense.postman_collection.json` (and optionally
`JobSense.local.postman_environment.json`). Set `baseUrl` (default `http://localhost:5000/api`),
then run **Auth > Register**; the token is stored automatically. For resume upload, select a
file in the request body. Command line:

```bash
npx newman run postman/JobSense.postman_collection.json --env-var baseUrl=http://localhost:5000/api
```

## Deployment

Summary (full guide: [docs/deployment.md](docs/deployment.md)):

1. **Railway MySQL**: create a MySQL service, then run `schema.sql` and `seed.sql` against its public host/port.
2. **Render**: create a web service from `render.yaml` (root `backend`, `gunicorn run:app`), and set the DB, `SECRET_KEY`, `JSEARCH_API_KEY` and `CORS_ORIGINS` variables.
3. **Vercel**: import the project with root `frontend`, set `VITE_API_URL=https://<render-service>.onrender.com`, and deploy.
4. Add the Vercel URL to Render's `CORS_ORIGINS`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Access denied for user ...` | wrong `DB_USER`/`DB_PASSWORD` in `backend/.env` (check it isn't named `.env.txt`) |
| `Unknown database 'jobsense'` | run `CREATE DATABASE jobsense ...` or `flask --app run init-db` |
| `/api/health` shows `database: false` | MySQL not running, or wrong host/port; the API still starts and retries per request |
| Frontend shows "Cannot reach the JobSense server" | backend not running, or `VITE_API_URL` wrong (restart `npm run dev` after changing `.env`) |
| CORS error in the browser console | add the exact frontend origin (scheme + host + port) to `CORS_ORIGINS` |
| "Very little text could be extracted" | the PDF is scanned or image-only; upload a text-based PDF or DOCX |
| Jobs are all "Sample listing" | no `JSEARCH_API_KEY` configured (mock mode) |
| `JOB_API_RATE_LIMITED` / `JOB_API_AUTH_FAILED` | JSearch quota reached / invalid key |
| spaCy `Can't find model 'en_core_web_sm'` | `python -m spacy download en_core_web_sm` (the app falls back to a basic tokenizer and logs a warning) |
| Integration tests skipped | MySQL credentials are missing, or the user cannot `CREATE DATABASE jobsense_test` |

## Limitations

- Skill extraction is dictionary-based (137 skills). Unknown skills can be added manually or to the taxonomy.
- TF-IDF measures lexical, not semantic, overlap, and resume-vs-job similarities are typically 10-40%.
- Scanned PDFs are not OCR'd.
- Match scores describe profile alignment. They do not predict hiring outcomes.
