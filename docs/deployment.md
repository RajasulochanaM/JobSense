# Deployment: Railway MySQL + Render (API) + Vercel (frontend)

```
Browser -> Vercel (React build) --HTTPS--> Render (Flask + gunicorn) -> Railway MySQL
                                             \-> OpenWeb Ninja JSearch
```

No Docker is required. Deploy in this order: **database, then API, then frontend**. After
the frontend is live, update CORS on the API.

## 1. Railway MySQL

1. Create a project at <https://railway.app>, then choose **+ New > Database > MySQL**.
2. Open the MySQL service, then **Variables** / **Connect**. Note these values:
   * `MYSQLHOST` - use the **public** proxy host (e.g. `xxx.proxy.rlwy.net`), because Render is outside Railway's private network
   * `MYSQLPORT` - the public proxy port (not 3306)
   * `MYSQLUSER` (usually `root`), `MYSQLPASSWORD`, `MYSQLDATABASE` (usually `railway`)
3. Initialise the schema and seed data from your machine:

   ```bash
   mysql -h <MYSQLHOST> -P <MYSQLPORT> -u <MYSQLUSER> -p <MYSQLDATABASE> < database/schema.sql
   mysql -h <MYSQLHOST> -P <MYSQLPORT> -u <MYSQLUSER> -p <MYSQLDATABASE> < database/seed.sql
   ```

   Alternatively, put the Railway values in `backend/.env` and run
   `flask --app run init-db --yes` from `backend/`.
4. **Change the seeded admin password.** Either regenerate the seed first
   (`python scripts/generate_seed.py --admin-email ... --admin-password ...`), or create your own admin:
   `flask --app run create-admin --email you@example.com`.

## 2. Render (Flask API)

Option A, Blueprint: in Render choose **New > Blueprint**, select the repository, and
Render reads `render.yaml`. Fill in the variables marked `sync: false`.

Option B, manual: **New > Web Service**, then set:

| Setting | Value |
|---|---|
| Root directory | `backend` |
| Runtime | Python 3 (`PYTHON_VERSION=3.12.8`) |
| Build command | `pip install -r requirements.txt` (this also installs the spaCy `en_core_web_sm` model) |
| Start command | `gunicorn run:app --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT` |
| Health check path | `/api/health` |

Environment variables:

| Variable | Value |
|---|---|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | long random string (`python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Railway public connection values |
| `DB_SSL_DISABLED` | `true` (Railway's proxy works without TLS); set `false` if your DB requires TLS |
| `JOB_PROVIDER` | `jsearch` |
| `JSEARCH_API_KEY` | your OpenWeb Ninja key (server-side only) |
| `JSEARCH_BASE_URL` | `https://api.openwebninja.com/jsearch` |
| `CORS_ORIGINS` | `https://<your-app>.vercel.app` (comma-separate several; add custom domains) |
| `TEXT_SIMILARITY_WEIGHT` / `SKILL_MATCH_WEIGHT` | `0.40` / `0.60` (optional) |

Check the deployment: `https://<service>.onrender.com/api/health` should return
`"database": true` and `"provider": "jsearch"`.

Notes:

* The spaCy model plus scikit-learn use roughly 250-350 MB of RAM. If the free instance is
  short on memory, reduce to `--workers 1`.
* Render's disk is ephemeral. Uploaded resume **files** may disappear on redeploy, but that
  is harmless: extracted text, skills and analysis live in MySQL, and the original file is
  not needed again. Attach a Render Disk and set `UPLOAD_FOLDER` if you want to keep the files.
* Free instances sleep when idle. The first request after a sleep can take 30-60 seconds,
  including spaCy model load.

## 3. Vercel (React frontend)

1. **Add New > Project**, then import the repository.
2. Root directory: `frontend`. Framework preset: **Vite**. Build command: `npm run build`. Output directory: `dist`.
3. Environment variable: `VITE_API_URL=https://<service>.onrender.com` (no trailing slash, no `/api`).
   This is the **only** frontend variable. Never put `JSEARCH_API_KEY` or any secret in Vercel.
4. Deploy. `frontend/vercel.json` rewrites all routes to `index.html` so deep links such as
   `/jobs/12` work, and it caches hashed assets long-term.
5. Copy the Vercel URL into Render's `CORS_ORIGINS` and redeploy the API.

## 4. JSearch API key

1. Sign up at <https://www.openwebninja.com/> and subscribe to the **JSearch** API. The free tier is rate limited.
2. Copy the API key and set `JSEARCH_API_KEY` on Render (or in `backend/.env` locally).
3. The key is sent only from the Flask server, as the `x-api-key` header. If you use the
   RapidAPI-hosted JSearch instead, set `JSEARCH_BASE_URL=https://jsearch.p.rapidapi.com`;
   the provider then sends the RapidAPI headers automatically.
4. Searches default to `country=in` (India). Location is appended to the query (e.g.
   "Python Developer in Hyderabad"), and remote searches set `work_from_home=true`.
5. Failures are handled and reported to the user without exposing details: timeout (504),
   rate limit (429), invalid key (502, logged server-side), malformed response (502), and
   empty results (empty list).

## 5. Production checklist

- [ ] `SECRET_KEY` set, `FLASK_ENV=production`
- [ ] admin password changed
- [ ] `JOB_PROVIDER=jsearch` and a key configured (mock data is for development only)
- [ ] `CORS_ORIGINS` lists only your frontend origin(s)
- [ ] `/api/health` shows `database: true`
- [ ] if mock jobs were created during testing: Admin > Jobs > "Delete all mock jobs"
