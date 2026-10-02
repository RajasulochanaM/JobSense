# REST API

Base URL: `http://localhost:5000/api` locally, or `https://<your-render-service>.onrender.com/api` in production.

Authenticated endpoints need `Authorization: Bearer <token>`. The token comes from
register or login. All responses use the envelope described in
[architecture.md](architecture.md#error-handling). A Postman collection with tests is in
`postman/`.

| Status | Meaning |
|---|---|
| 200 / 201 | success / created |
| 401 `UNAUTHORIZED` | missing, invalid or expired token |
| 403 `FORBIDDEN` | authenticated but not allowed (e.g. candidate calling `/admin/*`) |
| 404 `NOT_FOUND` | resource missing, or it belongs to another user |
| 409 | duplicate (email, skill, application) |
| 413 / 415 | file too large / unsupported file type |
| 422 `VALIDATION_ERROR` | invalid input (`error.details` names the field) |
| 429 / 502 / 504 | job provider rate-limited / failed / timed out |
| 503 `DATABASE_ERROR` | database unavailable |

## Authentication

| Method | Path | Body | Notes |
|---|---|---|---|
| POST | `/auth/register` | `name, email, password, password_confirmation` | returns `{token, user}`; role is always `candidate` |
| POST | `/auth/login` | `email, password` | returns `{token, user}` |
| POST | `/auth/logout` | none | revokes the token |
| GET | `/auth/me` | none | current user |

Passwords must be at least 8 characters and contain letters and numbers.

## Profile and skills

| Method | Path | Notes |
|---|---|---|
| GET | `/profile` | user, profile, interests, skills, completeness, options |
| PUT | `/profile` | any of `name, headline, experience_years, experience_summary, education, location, preferred_locations, remote_preference (any/remote/hybrid/onsite), interests[] (suggested or custom, max 25), social_links {linkedin, github, portfolio, twitter, stackoverflow, behance}, avatar_color`; `role`/`email` are ignored |
| PUT | `/profile/avatar` | `{image}`: `data:image/(png\|jpeg\|webp);base64,...` (max 300 KB decoded) |
| DELETE | `/profile/avatar` | remove the photo and fall back to the initials avatar |
| GET | `/interests` | suggested interests grouped by field |
| GET | `/profile/skills` | candidate skills (`source`: resume or manual) |
| POST | `/profile/skills` | `{skill_name}`; aliases are normalised (`reactjs` -> `React`) |
| DELETE | `/profile/skills/<skill_id>` | |
| GET | `/skills` | skill taxonomy grouped by category |
| GET | `/dashboard` | dashboard summary |

## Resumes

| Method | Path | Notes |
|---|---|---|
| POST | `/resumes` | `multipart/form-data` field `file` (.pdf/.docx, 5 MB max). Returns `{resume, skills, stages}` |
| GET | `/resumes` | history (newest first) |
| GET | `/resumes/<id>` | includes `text_preview`, `education`, `experience` |
| DELETE | `/resumes/<id>` | the newest remaining resume becomes active |

## Jobs and matching

| Method | Path | Notes |
|---|---|---|
| POST | `/jobs/search` | `{query*, location, country="in", remote, employment_type (FULLTIME/PARTTIME/CONTRACTOR/INTERN), experience_years (0-50; jobs requiring more are dropped), date_posted, page, sort ("score")}`. Returns `{items, page, has_more, provider, is_mock}` |
| GET | `/jobs` | stored jobs: `q, location, remote, employment_type, limit, offset, sort=newest/score` |
| GET | `/jobs/<id>` | full description, `match`, `explanation` (weights, formula, shared terms), `application`, `learning_resources` |
| GET | `/jobs/provider` | active provider (`jsearch` / `mock`) |
| GET | `/matches` | `sort=score/newest, limit, offset, min_score`; scores the job pool on first use |
| GET | `/matches/<job_id>` | match detail + learning resources for missing skills |
| POST | `/matches/refresh` | `{fetch: bool}`: optionally fetch jobs for the profile, then re-score the pool |

A job's `match` object looks like this:

```json
{ "final_score": 77.8, "text_similarity": 82.0, "skill_match": 75.0,
  "matched_skills": ["React", "JavaScript", "Node.js"], "missing_skills": ["TypeScript"],
  "skill_data_available": true }
```

## Saved jobs and applications

| Method | Path | Notes |
|---|---|---|
| GET | `/saved-jobs` | includes match and application status |
| POST | `/saved-jobs/<job_id>` | 201 when newly saved, 200 if already saved |
| DELETE | `/saved-jobs/<job_id>` | |
| GET | `/applications` | `?status=Interview` filter |
| POST | `/applications` | `{job_id*, status="Applied", applied_date (YYYY-MM-DD, not in the future), notes}` |
| PUT | `/applications/<id>` | any of `status, applied_date, notes` |
| DELETE | `/applications/<id>` | |

Statuses: `Saved, Applied, Interview, Offer, Rejected, Withdrawn`.

## Careers and learning

| Method | Path | Notes |
|---|---|---|
| GET | `/careers` | career paths with skills |
| GET | `/careers/<id>` | career, the user's recommendation (reasons, matched/missing) and learning resources |
| GET | `/career-recommendations` | ranked; `?refresh=1` recomputes |
| GET | `/learning-resources` | `skill, q, limit, offset` |
| GET | `/learning-resources/<skill>` | skill aliases accepted |

## Admin (role `admin`)

| Method | Path | Notes |
|---|---|---|
| GET | `/admin/stats` | totals |
| GET | `/admin/analytics` | top skills, top missing skills, application status, match statistics, jobs by source, sign-ups |
| GET | `/admin/users` | `q, role, limit, offset` |
| PATCH | `/admin/users/<id>` | `{is_active}` (not for yourself) |
| DELETE | `/admin/users/<id>` | candidates only |
| GET / POST | `/admin/careers` | POST `{career_name, description, interest_area, skills: [{skill_name, importance 1-3}]}` |
| PUT / DELETE | `/admin/careers/<id>` | |
| POST | `/admin/learning-resources` | `{skill_name, resource_name, resource_url (http/https), resource_type, description}` |
| PUT / DELETE | `/admin/learning-resources/<id>` | |
| GET | `/admin/jobs` | `q, source, limit, offset` |
| DELETE | `/admin/jobs/<id>` | |
| DELETE | `/admin/jobs/mock` | remove all mock sample jobs |

## Health

`GET /health` returns `{status, database: bool, job_provider}` and needs no authentication. It is used by Render's health check.
