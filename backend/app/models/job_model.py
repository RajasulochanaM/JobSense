"""JOBS data access, including de-duplicating upserts."""
import hashlib

from ..database.db import execute, fetch_all, fetch_one, transaction

JOB_LIST_COLUMNS = ("j.job_id, j.external_job_id, j.title, j.company, j.location, j.country, "
                    "LEFT(j.description, 400) AS snippet, j.job_url, j.employment_type, j.remote, j.required_skills, "
                    "j.min_experience_years, j.source, j.publisher, j.posted_at, j.fetched_at")


def url_hash(url):
    return hashlib.sha256(url.encode("utf-8")).hexdigest() if url else None


def find_existing(source, external_ids, url_hashes):
    """Return {external_job_id or url_hash: job_id} for jobs already stored."""
    found = {}
    if external_ids:
        placeholders = ", ".join(["%s"] * len(external_ids))
        for row in fetch_all(f"SELECT job_id, external_job_id FROM jobs WHERE source = %s "
                             f"AND external_job_id IN ({placeholders})", [source] + list(external_ids)):
            found[row["external_job_id"]] = row["job_id"]
    hashes = [h for h in url_hashes if h]
    if hashes:
        placeholders = ", ".join(["%s"] * len(hashes))
        for row in fetch_all(f"SELECT job_id, job_url_hash FROM jobs WHERE job_url_hash IN ({placeholders})", hashes):
            found[row["job_url_hash"]] = row["job_id"]
    return found


def insert_job(job):
    """job: dict with the JOBS columns (required_skills already JSON-encoded)."""
    lastrowid, _ = execute(
        """INSERT INTO jobs (external_job_id, title, company, location, country, description, processed_text,
                             job_url, job_url_hash, employment_type, remote, required_skills, min_experience_years,
                             source, publisher, posted_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE job_id = LAST_INSERT_ID(job_id), fetched_at = CURRENT_TIMESTAMP""",
        (job["external_job_id"], job["title"], job["company"], job.get("location"), job.get("country"),
         job.get("description"), job.get("processed_text"), job.get("job_url"), url_hash(job.get("job_url")),
         job.get("employment_type"), 1 if job.get("remote") else 0, job.get("required_skills"),
         job.get("min_experience_years"), job["source"], job.get("publisher"), job.get("posted_at")))
    return lastrowid


def touch_jobs(job_ids):
    if job_ids:
        placeholders = ", ".join(["%s"] * len(job_ids))
        execute(f"UPDATE jobs SET fetched_at = CURRENT_TIMESTAMP WHERE job_id IN ({placeholders})", list(job_ids))


def get_job(job_id):
    return fetch_one("SELECT * FROM jobs WHERE job_id = %s", (job_id,))


def get_jobs_for_matching(job_ids=None, limit=300, exclude_mock=False):
    """Rows needed by the scorer (processed text + skills), newest first."""
    if job_ids is not None:
        if not job_ids:
            return []
        placeholders = ", ".join(["%s"] * len(job_ids))
        return fetch_all(f"SELECT job_id, processed_text, required_skills FROM jobs WHERE job_id IN ({placeholders})",
                         list(job_ids))
    where = "WHERE source <> 'mock'" if exclude_mock else ""
    return fetch_all(f"""SELECT job_id, processed_text, required_skills FROM jobs {where}
                         ORDER BY fetched_at DESC, job_id DESC LIMIT %s""", (limit,))


def _filters(q="", location="", remote=None, employment_type="", source="", exclude_mock=False):
    where, params = ["1=1"], []
    if exclude_mock:
        where.append("j.source <> 'mock'")
    if q:
        where.append("(j.title LIKE %s OR j.company LIKE %s OR j.required_skills LIKE %s)")
        params += [f"%{q}%"] * 3
    if location:
        where.append("j.location LIKE %s")
        params.append(f"%{location}%")
    if remote is True:
        where.append("j.remote = 1")
    if employment_type:
        where.append("j.employment_type = %s")
        params.append(employment_type)
    if source:
        where.append("j.source = %s")
        params.append(source)
    return " AND ".join(where), params


def list_jobs(user_id=None, q="", location="", remote=None, employment_type="", source="",
              limit=10, offset=0, sort="newest", exclude_mock=False):
    clause, params = _filters(q, location, remote, employment_type, source, exclude_mock)
    total = fetch_one(f"SELECT COUNT(*) AS n FROM jobs j WHERE {clause}", params)["n"]
    order = "COALESCE(j.posted_at, j.fetched_at) DESC, j.job_id DESC"
    if sort == "score" and user_id:
        order = "m.final_score IS NULL, m.final_score DESC, " + order
    rows = fetch_all(
        f"""SELECT {JOB_LIST_COLUMNS},
                   m.final_score, m.text_similarity, m.skill_match, m.matched_skills, m.missing_skills,
                   (s.saved_id IS NOT NULL) AS is_saved
            FROM jobs j
            LEFT JOIN job_matches m ON m.job_id = j.job_id AND m.user_id = %s
            LEFT JOIN saved_jobs s ON s.job_id = j.job_id AND s.user_id = %s
            WHERE {clause} ORDER BY {order} LIMIT %s OFFSET %s""",
        [user_id or 0, user_id or 0] + params + [limit, offset])
    return rows, total


def list_jobs_by_ids(user_id, job_ids):
    if not job_ids:
        return []
    placeholders = ", ".join(["%s"] * len(job_ids))
    rows = fetch_all(
        f"""SELECT {JOB_LIST_COLUMNS},
                   m.final_score, m.text_similarity, m.skill_match, m.matched_skills, m.missing_skills,
                   (s.saved_id IS NOT NULL) AS is_saved
            FROM jobs j
            LEFT JOIN job_matches m ON m.job_id = j.job_id AND m.user_id = %s
            LEFT JOIN saved_jobs s ON s.job_id = j.job_id AND s.user_id = %s
            WHERE j.job_id IN ({placeholders})""", [user_id, user_id] + list(job_ids))
    order = {jid: i for i, jid in enumerate(job_ids)}
    return sorted(rows, key=lambda r: order.get(r["job_id"], 0))


def delete_job(job_id):
    _, count = execute("DELETE FROM jobs WHERE job_id = %s", (job_id,))
    return count


def delete_jobs_by_source(source):
    _, count = execute("DELETE FROM jobs WHERE source = %s", (source,))
    return count


def update_job_analysis(job_id, processed_text, required_skills_json):
    with transaction() as cur:
        cur.execute("UPDATE jobs SET processed_text = %s, required_skills = %s WHERE job_id = %s",
                    (processed_text, required_skills_json, job_id))
