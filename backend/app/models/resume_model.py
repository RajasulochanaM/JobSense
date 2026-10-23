"""RESUMES and CANDIDATE_SKILLS data access."""
from ..database.db import execute, fetch_all, fetch_one, transaction
from ..ml.skill_extraction.taxonomy import normalize_skill_key

RESUME_LIST_COLUMNS = ("resume_id, user_id, file_name, file_type, file_size, status, error_message, "
                       "experience_years, is_active, uploaded_at, processed_at")


def create_resume(user_id, file_name, file_type, file_path, file_size):
    with transaction() as cur:
        # Only one active resume per user: previous uploads are kept as history.
        cur.execute("UPDATE resumes SET is_active = 0 WHERE user_id = %s", (user_id,))
        cur.execute("""INSERT INTO resumes (user_id, file_name, file_type, file_path, file_size, status)
                       VALUES (%s, %s, %s, %s, %s, 'processing')""",
                    (user_id, file_name, file_type, file_path, file_size))
        return cur.lastrowid


def mark_processed(resume_id, extracted_text, processed_text, education_json, experience_json, experience_years):
    execute("""UPDATE resumes SET extracted_text = %s, processed_text = %s, education = %s, experience = %s,
                      experience_years = %s, status = 'processed', error_message = NULL, processed_at = UTC_TIMESTAMP()
               WHERE resume_id = %s""",
            (extracted_text, processed_text, education_json, experience_json, experience_years, resume_id))


def mark_failed(resume_id, message):
    execute("UPDATE resumes SET status = 'failed', error_message = %s, is_active = 0 WHERE resume_id = %s",
            (message[:255], resume_id))


def list_resumes(user_id):
    return fetch_all(f"SELECT {RESUME_LIST_COLUMNS} FROM resumes WHERE user_id = %s ORDER BY uploaded_at DESC, "
                     "resume_id DESC", (user_id,))


def get_resume(user_id, resume_id):
    return fetch_one("""SELECT resume_id, user_id, file_name, file_type, file_path, file_size, status, error_message,
                               extracted_text, education, experience, experience_years, is_active,
                               uploaded_at, processed_at
                        FROM resumes WHERE resume_id = %s AND user_id = %s""", (resume_id, user_id))


def get_active_resume(user_id):
    return fetch_one("""SELECT resume_id, file_name, file_type, status, extracted_text, processed_text, education,
                               experience, experience_years, uploaded_at, processed_at
                        FROM resumes WHERE user_id = %s AND is_active = 1 AND status = 'processed'
                        ORDER BY uploaded_at DESC, resume_id DESC LIMIT 1""", (user_id,))


def delete_resume(user_id, resume_id):
    _, count = execute("DELETE FROM resumes WHERE resume_id = %s AND user_id = %s", (resume_id, user_id))
    return count


def activate_latest(user_id):
    """After deleting the active resume, fall back to the newest remaining processed one."""
    row = fetch_one("""SELECT resume_id FROM resumes WHERE user_id = %s AND status = 'processed'
                       ORDER BY uploaded_at DESC, resume_id DESC LIMIT 1""", (user_id,))
    if row:
        execute("UPDATE resumes SET is_active = (resume_id = %s) WHERE user_id = %s", (row["resume_id"], user_id))
    return row["resume_id"] if row else None


# ------------------------------------------------------------ candidate skills

def list_skills(user_id):
    return fetch_all("""SELECT skill_id, skill_name, normalized_skill_name, source, created_at
                        FROM candidate_skills WHERE user_id = %s ORDER BY source, skill_name""", (user_id,))


def skill_names(user_id):
    return [r["skill_name"] for r in list_skills(user_id)]


def replace_resume_skills(user_id, skills):
    """Replace resume-derived skills; manually added skills are preserved."""
    with transaction() as cur:
        cur.execute("DELETE FROM candidate_skills WHERE user_id = %s AND source = 'resume'", (user_id,))
        rows = [(user_id, s, normalize_skill_key(s)) for s in skills]
        if rows:
            cur.executemany("""INSERT IGNORE INTO candidate_skills (user_id, skill_name, normalized_skill_name, source)
                               VALUES (%s, %s, %s, 'resume')""", rows)


def add_manual_skill(user_id, skill_name):
    lastrowid, count = execute(
        """INSERT IGNORE INTO candidate_skills (user_id, skill_name, normalized_skill_name, source)
           VALUES (%s, %s, %s, 'manual')""", (user_id, skill_name, normalize_skill_key(skill_name)))
    return count > 0


def delete_skill(user_id, skill_id):
    _, count = execute("DELETE FROM candidate_skills WHERE skill_id = %s AND user_id = %s", (skill_id, user_id))
    return count
