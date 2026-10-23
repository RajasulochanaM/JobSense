"""Aggregate queries for the admin dashboard and analytics."""
from ..database.db import fetch_all, fetch_one


def overview_counts():
    return fetch_one("""SELECT
        (SELECT COUNT(*) FROM users) AS total_users,
        (SELECT COUNT(*) FROM users WHERE role = 'candidate') AS total_candidates,
        (SELECT COUNT(*) FROM resumes) AS total_resumes,
        (SELECT COUNT(*) FROM jobs) AS total_jobs,
        (SELECT COUNT(*) FROM jobs WHERE source = 'mock') AS mock_jobs,
        (SELECT COUNT(*) FROM applications) AS total_applications,
        (SELECT COUNT(*) FROM saved_jobs) AS total_saved_jobs,
        (SELECT COUNT(*) FROM job_matches) AS total_matches,
        (SELECT COUNT(*) FROM career_paths) AS total_careers,
        (SELECT COUNT(*) FROM learning_resources) AS total_resources""")


def top_candidate_skills(limit=10):
    return fetch_all("""SELECT skill_name, COUNT(DISTINCT user_id) AS n FROM candidate_skills
                        GROUP BY skill_name ORDER BY n DESC, skill_name LIMIT %s""", (limit,))


def all_missing_skill_rows(limit=5000):
    return fetch_all("SELECT missing_skills FROM job_matches ORDER BY calculated_at DESC LIMIT %s", (limit,))


def match_statistics():
    return fetch_one("""SELECT COUNT(*) AS total, ROUND(AVG(final_score), 2) AS avg_final,
                               ROUND(AVG(text_similarity), 2) AS avg_text, ROUND(AVG(skill_match), 2) AS avg_skill,
                               ROUND(MAX(final_score), 2) AS max_final,
                               SUM(final_score >= 70) AS band_high, SUM(final_score >= 40 AND final_score < 70) AS band_mid,
                               SUM(final_score < 40) AS band_low
                        FROM job_matches""")


def signups_by_month(limit=6):
    return fetch_all("""SELECT DATE_FORMAT(created_at, '%Y-%m') AS month, COUNT(*) AS n FROM users
                        GROUP BY month ORDER BY month DESC LIMIT %s""", (limit,))


def jobs_by_source():
    return fetch_all("SELECT source, COUNT(*) AS n FROM jobs GROUP BY source ORDER BY n DESC")
