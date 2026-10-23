# Architecture

## Overview

```
Browser
  |  HTTPS
Vercel - React (Vite) SPA  --------------------------+
  |  HTTPS, JSON, Authorization: Bearer <token>       |  (static assets only;
Render - Flask API (gunicorn)                         |   no secrets in the bundle)
  |-- MySQL (Railway)       mysql-connector-python pool
  |-- OpenWeb Ninja JSearch  requests (server-side only, x-api-key)
```

## Backend layers (`backend/app`)

```
routes/        HTTP only: parse/validate input, call a service, return the JSON envelope
  |
services/      business logic and orchestration (auth, resume, jobs, matching, careers, admin)
  |        \
models/     ml/                       integrations/jobs/
SQL only    NLP + scoring (no Flask)  BaseJobProvider -> JSearchProvider | MockJobProvider
  |
database/db.py   connection pool, transactions, parameterised queries
```

* **Routes never contain NLP or SQL.** A route calls one service function.
* **ML modules are framework-free.** `app/ml` does not import Flask or the DB, so it is
  unit-tested in isolation and reusable.
* **Repositories (`models/`)** hold all SQL and always use `%s` placeholders.
* **Providers** normalise every external job into `NormalizedJob`, so nothing else depends
  on the JSearch response format.

| Concern | Where |
|---|---|
| Config / env vars / weights | `config/settings.py` |
| Auth primitives (Werkzeug scrypt hashing, tokens) | `auth/security.py` |
| `@login_required`, `@admin_required` | `auth/decorators.py` |
| Response envelope + `APIError` | `utils/responses.py` |
| Global error handlers, CORS, security headers, logging | `app/__init__.py` |
| CLI: `init-db`, `create-admin` | `app/cli.py` |

### Authentication

Opaque bearer tokens: `secrets.token_urlsafe(32)` is returned to the client, and only its
SHA-256 hash is stored in `user_sessions` with an expiry (default 7 days). Logout deletes
the session, so the token is genuinely revoked. Bearer tokens are used instead of cookies
because the frontend (Vercel) and API (Render) are on different sites, where third-party
cookies are unreliable. Passwords are hashed with Werkzeug `generate_password_hash`
(scrypt). Login uses a dummy hash check for unknown emails to reduce timing-based user
enumeration. Deactivated users are rejected and their sessions deleted.

Authorisation: every user-owned query is scoped with `WHERE user_id = %s`, so accessing
another user's resume returns 404. Admin routes use `@admin_required` (403 for
candidates). The role cannot be set through registration or profile updates.

### Error handling

All responses use one envelope:

```json
{ "success": true,  "data": { }, "message": "..." }
{ "success": false, "data": null, "message": "...", "error": { "code": "...", "details": null } }
```

`APIError` subclasses map to 4xx codes. `DatabaseError` maps to 503. Unhandled exceptions
map to a generic 500, and the stack trace is logged server-side only.

### Performance

* the spaCy model and `SkillExtractor` load once per process (lazy singletons)
* resumes and job descriptions are NLP-processed once and persisted
* matches are cached in `job_matches` and computed only for unseen jobs
* provider searches are cached in memory for 15 minutes (`JOB_SEARCH_CACHE_SECONDS`)
* list endpoints are paginated, and job lists return a 400-character snippet, not the full description

## Frontend (`frontend/src`)

```
main.jsx       providers: Router, Toasts, Auth
App.jsx        routes; authenticated pages are React.lazy code-split
layouts/       PublicLayout (header + footer), AppLayout (sidebar / mobile drawer + footer)
pages/         19 pages (public, candidate, admin/)
components/    ui.jsx primitives, JobCard, SkillGap, BarList (charts), ApplicationModal,
               RouteGuards, Footer
services/api.js   Axios instance, bearer interceptor, envelope unwrapping, ApiError
context/       AuthContext, ToastContext
hooks/         useAsync (loading/error/reload), useDebounce, useSaveJob, useDocumentTitle
utils/format.js   dates, percentages, score bands, constants
assets/        global.css (design tokens), layout.css
```

Design system: burgundy `#6B2638` / `#481824` for brand, navigation, primary actions and
headings; butter yellow `#F4DFA6` / `#FBF4DD` for highlights, active navigation and score
emphasis; warm neutral surfaces. Plain CSS with custom properties, no CSS framework.

Accessibility: semantic landmarks, skip link, labelled inputs with `aria-invalid` and
`aria-describedby`, visible focus rings, keyboard-operable dialogs (Esc to close, focus
restored), a mobile drawer with `aria-expanded`, and matched/missing skills conveyed by
✓ / ○ symbols as well as colour. Charts have a table view.

## Data flow (end to end)

```
Register/Login -> Profile (interests, locations) -> Upload resume
  -> extract text -> NLP -> skills -> CANDIDATE_SKILLS
  -> Search jobs (JSearch) -> normalise -> de-duplicate -> NLP once -> JOBS
  -> TF-IDF cosine + skill match -> final score -> JOB_MATCHES -> ranked list
  -> job details: score breakdown, matched/missing skills, learning resources
  -> save job / track application
Parallel: profile -> CareerRecommender -> CAREER_RECOMMENDATIONS -> career gaps -> resources
```
