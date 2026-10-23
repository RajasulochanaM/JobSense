"""SAVED_JOBS and APPLICATIONS data access."""
from ..database.db import execute, fetch_all, fetch_one, transaction

# ---------------------------------------------------------------- saved jobs


def save_job(user_id, job_id):
    _, count = execute("INSERT IGNORE INTO saved_jobs (user_id, job_id) VALUES (%s, %s)", (user_id, job_id))
    return count > 0


def unsave_job(user_id, job_id):
    _, count = execute("DELETE FROM saved_jobs WHERE user_id = %s AND job_id = %s", (user_id, job_id))
    return count


def list_saved(user_id):
    return fetch_all(
        """SELECT s.saved_id, s.saved_at, j.job_id, j.title, j.company, j.location, j.employment_type, j.remote,
                  j.job_url, j.source, j.posted_at, m.final_score, m.text_similarity, m.skill_match,
                  m.matched_skills, m.missing_skills, m.calculated_at,
                  a.application_id, a.status AS application_status
           FROM saved_jobs s JOIN jobs j ON j.job_id = s.job_id
           LEFT JOIN job_matches m ON m.job_id = s.job_id AND m.user_id = s.user_id
           LEFT JOIN applications a ON a.job_id = s.job_id AND a.user_id = s.user_id
           WHERE s.user_id = %s ORDER BY s.saved_at DESC""", (user_id,))


def count_saved(user_id):
    return fetch_one("SELECT COUNT(*) AS n FROM saved_jobs WHERE user_id = %s", (user_id,))["n"]


def is_saved(user_id, job_id):
    return fetch_one("SELECT 1 AS x FROM saved_jobs WHERE user_id = %s AND job_id = %s", (user_id, job_id)) is not None


# -------------------------------------------------------------- applications

# status_changed_at: when the current status was set (last history event; created_at for older rows).
APPLICATION_SELECT = """SELECT a.application_id, a.job_id, a.status, a.applied_date, a.notes, a.posting_opened_at,
                               a.created_at, a.updated_at, j.title, j.company, j.location, j.job_url, j.source,
                               m.final_score,
                               COALESCE((SELECT MAX(e.created_at) FROM application_events e
                                         WHERE e.application_id = a.application_id
                                           AND e.event_type IN ('created', 'status_change')),
                                        a.created_at) AS status_changed_at
                        FROM applications a JOIN jobs j ON j.job_id = a.job_id
                        LEFT JOIN job_matches m ON m.job_id = a.job_id AND m.user_id = a.user_id"""

EVENT_INSERT = """INSERT INTO application_events (application_id, event_type, from_status, to_status, source)
                  VALUES (%s, %s, %s, %s, %s)"""


def create_application(user_id, job_id, status, applied_date, notes, posting_opened=False, source="user"):
    """Insert the application and its first history event in one transaction."""
    with transaction() as cur:
        cur.execute("""INSERT INTO applications (user_id, job_id, status, applied_date, notes, posting_opened_at)
                       VALUES (%s, %s, %s, %s, %s, IF(%s, NOW(), NULL))""",
                    (user_id, job_id, status, applied_date, notes, posting_opened))
        application_id = cur.lastrowid
        cur.execute(EVENT_INSERT, (application_id, "created", None, status, source))
        return application_id


def mark_posting_opened(user_id, application_id, status):
    """Record the first time the candidate opened the external posting; later clicks are ignored."""
    with transaction() as cur:
        cur.execute("""UPDATE applications SET posting_opened_at = NOW()
                       WHERE application_id = %s AND user_id = %s AND posting_opened_at IS NULL""",
                    (application_id, user_id))
        if cur.rowcount:
            cur.execute(EVENT_INSERT, (application_id, "posting_opened", None, status, "auto"))
        return cur.rowcount


def list_events(user_id, application_ids):
    if not application_ids:
        return []
    placeholders = ", ".join(["%s"] * len(application_ids))
    return fetch_all(
        f"""SELECT e.event_id, e.application_id, e.event_type, e.from_status, e.to_status, e.source, e.created_at
            FROM application_events e JOIN applications a ON a.application_id = e.application_id
            WHERE a.user_id = %s AND e.application_id IN ({placeholders})
            ORDER BY e.created_at, e.event_id""", [user_id, *application_ids])


def get_application(user_id, application_id):
    return fetch_one(APPLICATION_SELECT + " WHERE a.application_id = %s AND a.user_id = %s",
                     (application_id, user_id))


def get_application_for_job(user_id, job_id):
    return fetch_one(APPLICATION_SELECT + " WHERE a.job_id = %s AND a.user_id = %s", (job_id, user_id))


def list_applications(user_id, status=""):
    if status:
        return fetch_all(APPLICATION_SELECT + " WHERE a.user_id = %s AND a.status = %s ORDER BY a.updated_at DESC",
                         (user_id, status))
    return fetch_all(APPLICATION_SELECT + " WHERE a.user_id = %s ORDER BY a.updated_at DESC", (user_id,))


def update_application(user_id, application_id, fields, previous_status=None):
    """Update the given fields; a status change is also written to the history."""
    allowed = {k: v for k, v in fields.items() if k in ("status", "applied_date", "notes")}
    if not allowed:
        return 0
    assignments = ", ".join(f"{k} = %s" for k in allowed)
    with transaction() as cur:
        cur.execute(f"UPDATE applications SET {assignments} WHERE application_id = %s AND user_id = %s",
                    list(allowed.values()) + [application_id, user_id])
        count = cur.rowcount
        if "status" in allowed and allowed["status"] != previous_status:
            cur.execute(EVENT_INSERT, (application_id, "status_change", previous_status, allowed["status"], "user"))
        return count


def delete_application(user_id, application_id):
    _, count = execute("DELETE FROM applications WHERE application_id = %s AND user_id = %s",
                       (application_id, user_id))
    return count


def application_status_counts(user_id=None):
    if user_id is None:
        return fetch_all("SELECT status, COUNT(*) AS n FROM applications GROUP BY status")
    return fetch_all("SELECT status, COUNT(*) AS n FROM applications WHERE user_id = %s GROUP BY status", (user_id,))
