"""CAREER_PATHS, CAREER_SKILLS, CAREER_RECOMMENDATIONS and LEARNING_RESOURCES data access."""
from ..database.db import execute, fetch_all, fetch_one, transaction

# ------------------------------------------------------------- career paths


def list_careers_with_skills():
    careers = fetch_all("SELECT career_id, career_name, description, interest_area FROM career_paths "
                        "ORDER BY career_name")
    skills = fetch_all("SELECT career_skill_id, career_id, skill_name, importance FROM career_skills "
                       "ORDER BY importance DESC, skill_name")
    by_career = {}
    for s in skills:
        by_career.setdefault(s["career_id"], []).append(s)
    for c in careers:
        c["skills"] = by_career.get(c["career_id"], [])
    return careers


def get_career(career_id):
    career = fetch_one("SELECT career_id, career_name, description, interest_area, created_at, updated_at "
                       "FROM career_paths WHERE career_id = %s", (career_id,))
    if career:
        career["skills"] = fetch_all("SELECT career_skill_id, skill_name, importance FROM career_skills "
                                     "WHERE career_id = %s ORDER BY importance DESC, skill_name", (career_id,))
    return career


def career_name_exists(name, exclude_id=None):
    row = fetch_one("SELECT career_id FROM career_paths WHERE career_name = %s", (name,))
    return row is not None and row["career_id"] != exclude_id


def create_career(name, description, interest_area, skills):
    with transaction() as cur:
        cur.execute("INSERT INTO career_paths (career_name, description, interest_area) VALUES (%s, %s, %s)",
                    (name, description, interest_area))
        career_id = cur.lastrowid
        _replace_skills(cur, career_id, skills)
    return career_id


def update_career(career_id, name, description, interest_area, skills=None):
    with transaction() as cur:
        cur.execute("UPDATE career_paths SET career_name = %s, description = %s, interest_area = %s "
                    "WHERE career_id = %s", (name, description, interest_area, career_id))
        if skills is not None:
            _replace_skills(cur, career_id, skills)
        # Career definition changed -> cached recommendations are stale.
        cur.execute("DELETE FROM career_recommendations WHERE career_id = %s", (career_id,))


def _replace_skills(cur, career_id, skills):
    cur.execute("DELETE FROM career_skills WHERE career_id = %s", (career_id,))
    if skills:
        cur.executemany("INSERT INTO career_skills (career_id, skill_name, importance) VALUES (%s, %s, %s)",
                        [(career_id, s["skill_name"], s["importance"]) for s in skills])


def delete_career(career_id):
    _, count = execute("DELETE FROM career_paths WHERE career_id = %s", (career_id,))
    return count


# ---------------------------------------------------- career recommendations

def save_recommendations(user_id, rows):
    """rows: [(career_id, match_score, skill_alignment, text_similarity, interest_match,
               matched_json, missing_json, reasons_json)]"""
    with transaction() as cur:
        cur.execute("DELETE FROM career_recommendations WHERE user_id = %s", (user_id,))
        if rows:
            cur.executemany(
                """INSERT INTO career_recommendations (user_id, career_id, match_score, skill_alignment,
                        text_similarity, interest_match, matched_skills, missing_skills, reasons)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""", [(user_id,) + tuple(r) for r in rows])


def clear_recommendations(user_id):
    execute("DELETE FROM career_recommendations WHERE user_id = %s", (user_id,))


def list_recommendations(user_id):
    return fetch_all(
        """SELECT r.recommendation_id, r.career_id, r.match_score, r.skill_alignment, r.text_similarity,
                  r.interest_match, r.matched_skills, r.missing_skills, r.reasons, r.calculated_at,
                  c.career_name, c.description, c.interest_area
           FROM career_recommendations r JOIN career_paths c ON c.career_id = r.career_id
           WHERE r.user_id = %s ORDER BY r.match_score DESC, r.skill_alignment DESC""", (user_id,))


def get_recommendation(user_id, career_id):
    return fetch_one(
        """SELECT recommendation_id, career_id, match_score, skill_alignment, text_similarity, interest_match,
                  matched_skills, missing_skills, reasons, calculated_at
           FROM career_recommendations WHERE user_id = %s AND career_id = %s""", (user_id, career_id))


# ------------------------------------------------------- learning resources

RESOURCE_COLUMNS = "resource_id, skill_name, resource_name, resource_url, description, resource_type, created_at"


def list_resources(skill="", search="", limit=200, offset=0):
    where, params = ["1=1"], []
    if skill:
        where.append("skill_name = %s")
        params.append(skill)
    if search:
        where.append("(skill_name LIKE %s OR resource_name LIKE %s)")
        params += [f"%{search}%", f"%{search}%"]
    clause = " AND ".join(where)
    total = fetch_one(f"SELECT COUNT(*) AS n FROM learning_resources WHERE {clause}", params)["n"]
    rows = fetch_all(f"SELECT {RESOURCE_COLUMNS} FROM learning_resources WHERE {clause} "
                     "ORDER BY skill_name, FIELD(resource_type, 'documentation', 'guide', 'tutorial', 'reference', "
                     "'course'), resource_name LIMIT %s OFFSET %s", params + [limit, offset])
    return rows, total


def resources_for_skills(skills):
    if not skills:
        return []
    placeholders = ", ".join(["%s"] * len(skills))
    return fetch_all(f"SELECT {RESOURCE_COLUMNS} FROM learning_resources WHERE skill_name IN ({placeholders}) "
                     "ORDER BY skill_name, FIELD(resource_type, 'documentation', 'guide', 'tutorial', 'reference', "
                     "'course')", list(skills))


def resource_skills():
    return [r["skill_name"] for r in fetch_all("SELECT DISTINCT skill_name FROM learning_resources ORDER BY skill_name")]


def get_resource(resource_id):
    return fetch_one(f"SELECT {RESOURCE_COLUMNS} FROM learning_resources WHERE resource_id = %s", (resource_id,))


def create_resource(fields):
    lastrowid, _ = execute(
        """INSERT INTO learning_resources (skill_name, resource_name, resource_url, description, resource_type)
           VALUES (%s, %s, %s, %s, %s)""",
        (fields["skill_name"], fields["resource_name"], fields["resource_url"], fields.get("description"),
         fields["resource_type"]))
    return lastrowid


def update_resource(resource_id, fields):
    _, count = execute(
        """UPDATE learning_resources SET skill_name = %s, resource_name = %s, resource_url = %s, description = %s,
                  resource_type = %s WHERE resource_id = %s""",
        (fields["skill_name"], fields["resource_name"], fields["resource_url"], fields.get("description"),
         fields["resource_type"], resource_id))
    return count


def delete_resource(resource_id):
    _, count = execute("DELETE FROM learning_resources WHERE resource_id = %s", (resource_id,))
    return count
