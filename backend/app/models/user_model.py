"""USERS, USER_SESSIONS, USER_PROFILES and USER_INTERESTS data access."""
from ..database.db import execute, fetch_all, fetch_one, transaction

PUBLIC_USER_COLUMNS = "user_id, name, email, role, is_active, created_at, updated_at"


def create_user(name, email, password_hash, role="candidate"):
    with transaction() as cur:
        cur.execute("INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                    (name, email, password_hash, role))
        user_id = cur.lastrowid
        cur.execute("INSERT INTO user_profiles (user_id) VALUES (%s)", (user_id,))
    return user_id


def get_by_email_with_hash(email):
    return fetch_one("SELECT user_id, name, email, role, is_active, password_hash FROM users WHERE email = %s",
                     (email,))


def get_by_id(user_id):
    return fetch_one(f"SELECT {PUBLIC_USER_COLUMNS} FROM users WHERE user_id = %s", (user_id,))


def email_exists(email):
    return fetch_one("SELECT 1 AS x FROM users WHERE email = %s", (email,)) is not None


def update_name(user_id, name):
    execute("UPDATE users SET name = %s WHERE user_id = %s", (name, user_id))


def list_users(search="", role="", limit=20, offset=0):
    where, params = ["1=1"], []
    if search:
        where.append("(u.name LIKE %s OR u.email LIKE %s)")
        params += [f"%{search}%", f"%{search}%"]
    if role in ("candidate", "admin"):
        where.append("u.role = %s")
        params.append(role)
    clause = " AND ".join(where)
    total = fetch_one(f"SELECT COUNT(*) AS n FROM users u WHERE {clause}", params)["n"]
    rows = fetch_all(
        f"""SELECT u.user_id, u.name, u.email, u.role, u.is_active, u.created_at,
                   (SELECT COUNT(*) FROM resumes r WHERE r.user_id = u.user_id AND r.is_active = 1) AS resume_count,
                   (SELECT COUNT(*) FROM candidate_skills s WHERE s.user_id = u.user_id) AS skill_count,
                   (SELECT COUNT(*) FROM applications a WHERE a.user_id = u.user_id) AS application_count
            FROM users u WHERE {clause} ORDER BY u.created_at DESC LIMIT %s OFFSET %s""",
        params + [limit, offset])
    return rows, total


def set_active(user_id, active):
    _, count = execute("UPDATE users SET is_active = %s WHERE user_id = %s", (1 if active else 0, user_id))
    if not active:
        execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,))
    return count


def promote_to_admin(user_id):
    execute("UPDATE users SET role = 'admin', is_active = 1 WHERE user_id = %s", (user_id,))


def delete_user(user_id):
    _, count = execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    return count


# ------------------------------------------------------------------ sessions

def create_session(user_id, token_hash, expires_at):
    execute("INSERT INTO user_sessions (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
            (user_id, token_hash, expires_at))
    # Opportunistic clean-up of expired sessions for this user.
    execute("DELETE FROM user_sessions WHERE user_id = %s AND expires_at < UTC_TIMESTAMP()", (user_id,))


def get_session_user(token_hash):
    return fetch_one(
        """SELECT u.user_id, u.name, u.email, u.role, u.is_active, u.created_at, u.updated_at
            FROM user_sessions s JOIN users u ON u.user_id = s.user_id
            WHERE s.token_hash = %s AND s.expires_at > UTC_TIMESTAMP()""", (token_hash,))


def delete_session(token_hash):
    execute("DELETE FROM user_sessions WHERE token_hash = %s", (token_hash,))


# ------------------------------------------------------------------ profiles

def get_profile(user_id):
    row = fetch_one("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    if row is None:
        execute("INSERT IGNORE INTO user_profiles (user_id) VALUES (%s)", (user_id,))
        row = fetch_one("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    return row


PROFILE_FIELDS = ("headline", "experience_years", "experience_summary", "education", "location",
                  "preferred_locations", "remote_preference", "social_links", "avatar_image", "avatar_color")


def get_avatar(user_id):
    return fetch_one("SELECT avatar_image, avatar_color FROM user_profiles WHERE user_id = %s", (user_id,)) or {}


def update_profile(user_id, fields):
    fields = {k: v for k, v in fields.items() if k in PROFILE_FIELDS}
    if not fields:
        return
    get_profile(user_id)  # ensure row exists
    assignments = ", ".join(f"{k} = %s" for k in fields)
    execute(f"UPDATE user_profiles SET {assignments} WHERE user_id = %s", list(fields.values()) + [user_id])


def get_interests(user_id):
    return [r["interest"] for r in fetch_all(
        "SELECT interest FROM user_interests WHERE user_id = %s ORDER BY interest", (user_id,))]


def set_interests(user_id, interests):
    with transaction() as cur:
        cur.execute("DELETE FROM user_interests WHERE user_id = %s", (user_id,))
        if interests:
            cur.executemany("INSERT INTO user_interests (user_id, interest) VALUES (%s, %s)",
                            [(user_id, i) for i in interests])
