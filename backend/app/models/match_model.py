"""JOB_MATCHES data access."""
from ..database.db import execute, fetch_all, fetch_one, transaction


def upsert_matches(user_id, rows):
    """rows: [(job_id, text_similarity, skill_match, final_score, matched_json, missing_json)]"""
    if not rows:
        return
    with transaction() as cur:
        cur.executemany(
            """INSERT INTO job_matches (user_id, job_id, text_similarity, skill_match, final_score,
                                        matched_skills, missing_skills)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE text_similarity = VALUES(text_similarity), skill_match = VALUES(skill_match),
                   final_score = VALUES(final_score), matched_skills = VALUES(matched_skills),
                   missing_skills = VALUES(missing_skills), calculated_at = CURRENT_TIMESTAMP""",
            [(user_id,) + tuple(r) for r in rows])


def matched_job_ids(user_id, job_ids):
    if not job_ids:
        return set()
    placeholders = ", ".join(["%s"] * len(job_ids))
    rows = fetch_all(f"SELECT job_id FROM job_matches WHERE user_id = %s AND job_id IN ({placeholders})",
                     [user_id] + list(job_ids))
    return {r["job_id"] for r in rows}


# Appended to WHERE clauses that join `jobs j` when mock (sample) jobs must be hidden.
NOT_MOCK = " AND j.source <> 'mock'"


def count_matches(user_id, exclude_mock=False):
    return fetch_one(f"""SELECT COUNT(*) AS n FROM job_matches m JOIN jobs j ON j.job_id = m.job_id
                         WHERE m.user_id = %s{NOT_MOCK if exclude_mock else ''}""", (user_id,))["n"]


def list_matches(user_id, sort="score", limit=10, offset=0, min_score=0, exclude_mock=False):
    order = "m.final_score DESC, m.text_similarity DESC" if sort == "score" \
        else "COALESCE(j.posted_at, j.fetched_at) DESC, m.final_score DESC"
    extra = NOT_MOCK if exclude_mock else ""
    total = fetch_one(f"""SELECT COUNT(*) AS n FROM job_matches m JOIN jobs j ON j.job_id = m.job_id
                          WHERE m.user_id = %s AND m.final_score >= %s{extra}""", (user_id, min_score))["n"]
    rows = fetch_all(
        f"""SELECT m.match_id, m.job_id, m.text_similarity, m.skill_match, m.final_score, m.matched_skills,
                   m.missing_skills, m.calculated_at,
                   j.title, j.company, j.location, j.employment_type, j.remote, j.source, j.job_url, j.posted_at,
                   j.required_skills, (s.saved_id IS NOT NULL) AS is_saved
            FROM job_matches m JOIN jobs j ON j.job_id = m.job_id
            LEFT JOIN saved_jobs s ON s.job_id = m.job_id AND s.user_id = m.user_id
            WHERE m.user_id = %s AND m.final_score >= %s{extra}
            ORDER BY {order} LIMIT %s OFFSET %s""", (user_id, min_score, limit, offset))
    return rows, total


def get_match(user_id, job_id):
    return fetch_one("""SELECT match_id, job_id, text_similarity, skill_match, final_score, matched_skills,
                               missing_skills, calculated_at
                        FROM job_matches WHERE user_id = %s AND job_id = %s""", (user_id, job_id))


def missing_skill_rows(user_id, limit=50, exclude_mock=False):
    return fetch_all(f"""SELECT m.missing_skills FROM job_matches m JOIN jobs j ON j.job_id = m.job_id
                         WHERE m.user_id = %s{NOT_MOCK if exclude_mock else ''}
                         ORDER BY m.final_score DESC LIMIT %s""", (user_id, limit))


def clear_user_matches(user_id):
    """Invalidate cached matches after the resume or skills change."""
    with transaction() as cur:
        cur.execute("DELETE FROM job_matches WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM career_recommendations WHERE user_id = %s", (user_id,))


def clear_job_matches(job_id):
    execute("DELETE FROM job_matches WHERE job_id = %s", (job_id,))
