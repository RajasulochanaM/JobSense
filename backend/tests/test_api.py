"""Integration tests: Flask API + MySQL test database (skipped when MySQL is unavailable)."""
import io

from tests.conftest import make_docx, make_pdf, register, SAMPLE_RESUME


def upload(client, headers, data, filename, mimetype):
    return client.post("/api/resumes", headers=headers, content_type="multipart/form-data",
                       data={"file": (io.BytesIO(data), filename, mimetype)})


# ------------------------------------------------------------ authentication

def test_register_login_me_logout(client):
    token, email = register(client, name="Asha")
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).get_json()
    assert me["success"] and me["data"]["user"]["email"] == email
    assert "password_hash" not in me["data"]["user"]
    assert me["data"]["user"]["role"] == "candidate"

    login = client.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"})
    assert login.status_code == 200
    token2 = login.get_json()["data"]["token"]

    assert client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token2}"}).status_code == 200
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {token2}"}).status_code == 401


def test_registration_validation(client):
    r = client.post("/api/auth/register", json={"name": "A B", "email": "bad", "password": "Passw0rd!",
                                                "password_confirmation": "Passw0rd!"})
    assert r.status_code == 422 and r.get_json()["error"]["code"] == "VALIDATION_ERROR"
    r = client.post("/api/auth/register", json={"name": "A B", "email": "ab@example.com", "password": "Passw0rd!",
                                                "password_confirmation": "different1"})
    assert r.status_code == 422
    _, email = register(client)
    r = client.post("/api/auth/register", json={"name": "Dup", "email": email, "password": "Passw0rd!",
                                                "password_confirmation": "Passw0rd!"})
    assert r.status_code == 409


def test_registration_cannot_self_assign_admin(client):
    r = client.post("/api/auth/register", json={"name": "Eve", "email": "eve-admin@example.com",
                                                "password": "Passw0rd!", "password_confirmation": "Passw0rd!",
                                                "role": "admin"})
    assert r.get_json()["data"]["user"]["role"] == "candidate"


def test_invalid_password(client):
    _, email = register(client)
    r = client.post("/api/auth/login", json={"email": email, "password": "wrong-password1"})
    assert r.status_code == 401
    body = r.get_json()
    assert body["success"] is False and body["data"] is None
    assert body["error"]["code"] == "INVALID_CREDENTIALS"


def test_protected_route_requires_token(client):
    for path in ("/api/profile", "/api/resumes", "/api/matches", "/api/saved-jobs", "/api/applications"):
        assert client.get(path).status_code == 401
    assert client.get("/api/profile", headers={"Authorization": "Bearer not-a-real-token"}).status_code == 401


def test_candidate_cannot_access_admin(client, auth_headers):
    for path in ("/api/admin/stats", "/api/admin/users", "/api/admin/careers", "/api/admin/analytics"):
        assert client.get(path, headers=auth_headers).status_code == 403
    assert client.post("/api/admin/careers", headers=auth_headers, json={}).status_code == 403


# --------------------------------------------------------------------- resume

def test_resume_upload_pdf_and_docx(client, auth_headers):
    r = upload(client, auth_headers, make_pdf(SAMPLE_RESUME), "my resume.pdf", "application/pdf")
    assert r.status_code == 201, r.get_json()
    data = r.get_json()["data"]
    assert "React" in data["skills"] and data["stages"][-1] == "profile_updated"
    assert data["resume"]["file_name"] == "my_resume.pdf"
    assert "file_path" not in data["resume"]

    r = upload(client, auth_headers, make_docx(SAMPLE_RESUME),  "cv.docx",
               "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    assert r.status_code == 201
    resumes = client.get("/api/resumes", headers=auth_headers).get_json()["data"]["items"]
    assert len(resumes) == 2 and sum(1 for x in resumes if x["is_active"]) == 1

    skills = client.get("/api/profile/skills", headers=auth_headers).get_json()["data"]["items"]
    assert {"React", "Node.js", "MySQL"} <= {s["skill_name"] for s in skills}


def test_resume_rejects_unsupported_and_spoofed(client, auth_headers):
    r = upload(client, auth_headers, b"just text", "resume.txt", "text/plain")
    assert r.status_code == 415
    r = upload(client, auth_headers, b"MZ fake exe content", "resume.pdf", "application/pdf")
    assert r.status_code == 415


def test_users_cannot_access_other_users_resumes(client, auth_headers):
    r = upload(client, auth_headers, make_pdf(SAMPLE_RESUME), "a.pdf", "application/pdf")
    resume_id = r.get_json()["data"]["resume"]["resume_id"]
    token, _ = register(client)
    other = {"Authorization": f"Bearer {token}"}
    assert client.get(f"/api/resumes/{resume_id}", headers=other).status_code == 404
    assert client.delete(f"/api/resumes/{resume_id}", headers=other).status_code == 404
    assert client.get(f"/api/resumes/{resume_id}", headers=auth_headers).status_code == 200


# ------------------------------------------------------ jobs / matching flow

def test_search_match_save_apply_flow(client, auth_headers):
    upload(client, auth_headers, make_pdf(SAMPLE_RESUME), "cv.pdf", "application/pdf")

    r = client.post("/api/jobs/search", headers=auth_headers,
                    json={"query": "React Developer", "location": "Chennai"})
    assert r.status_code == 200, r.get_json()
    body = r.get_json()["data"]
    assert body["is_mock"] is True and body["items"]
    job = body["items"][0]
    assert job["is_mock"] and job["match"] is not None
    m = job["match"]
    assert 0 <= m["final_score"] <= 100 and 0 <= m["text_similarity"] <= 100
    assert m["matched_skills"]

    # searching again does not duplicate jobs
    again = client.post("/api/jobs/search", headers=auth_headers,
                        json={"query": "React Developer", "location": "Chennai"}).get_json()["data"]
    assert [j["job_id"] for j in again["items"]] == [j["job_id"] for j in body["items"]]

    detail = client.get(f"/api/jobs/{job['job_id']}", headers=auth_headers).get_json()["data"]
    assert detail["job"]["description"] and detail["explanation"]["weights"]["skill_match"] == 0.6

    matches = client.get("/api/matches?sort=score", headers=auth_headers).get_json()["data"]
    scores = [i["match"]["final_score"] for i in matches["items"]]
    assert scores == sorted(scores, reverse=True)

    md = client.get(f"/api/matches/{job['job_id']}", headers=auth_headers).get_json()["data"]
    assert "learning_resources" in md

    # save / unsave
    assert client.post(f"/api/saved-jobs/{job['job_id']}", headers=auth_headers).status_code == 201
    saved = client.get("/api/saved-jobs", headers=auth_headers).get_json()["data"]["items"]
    assert saved[0]["job_id"] == job["job_id"] and saved[0]["match"] is not None
    assert client.delete(f"/api/saved-jobs/{job['job_id']}", headers=auth_headers).status_code == 200

    # application tracking: create + update status
    r = client.post("/api/applications", headers=auth_headers, json={"job_id": job["job_id"], "status": "Applied",
                                                                      "notes": "Applied via portal"})
    assert r.status_code == 201
    app_id = r.get_json()["data"]["application_id"]
    assert r.get_json()["data"]["applied_date"]
    assert client.post("/api/applications", headers=auth_headers,
                       json={"job_id": job["job_id"]}).status_code == 409
    r = client.put(f"/api/applications/{app_id}", headers=auth_headers, json={"status": "Interview"})
    assert r.status_code == 200 and r.get_json()["data"]["status"] == "Interview"
    assert client.put(f"/api/applications/{app_id}", headers=auth_headers,
                      json={"status": "Hired!"}).status_code == 422

    dash = client.get("/api/dashboard", headers=auth_headers).get_json()["data"]
    assert dash["stats"]["applications"] == 1 and dash["top_jobs"]


def test_career_recommendations_and_learning(client, auth_headers):
    upload(client, auth_headers, make_pdf(SAMPLE_RESUME), "cv.pdf", "application/pdf")
    client.put("/api/profile", headers=auth_headers, json={"interests": ["Web Development"],
                                                           "location": "Chennai"})
    recs = client.get("/api/career-recommendations", headers=auth_headers).get_json()["data"]
    assert recs["items"] and recs["profile_ready"]
    top = recs["items"][0]
    assert top["career_name"] in ("Frontend Developer", "Full Stack Developer")
    assert top["matched_skills"] and top["reasons"]

    detail = client.get(f"/api/careers/{top['career_id']}", headers=auth_headers).get_json()["data"]
    assert detail["recommendation"]["career_id"] == top["career_id"]
    assert isinstance(detail["learning_resources"], list)

    res = client.get("/api/learning-resources/React", headers=auth_headers).get_json()["data"]
    assert res["items"] and all(i["resource_url"].startswith("https://") for i in res["items"])


def test_profile_update_and_manual_skills(client, auth_headers):
    r = client.put("/api/profile", headers=auth_headers, json={"experience_years": "abc"})
    assert r.status_code == 422
    r = client.put("/api/profile", headers=auth_headers, json={
        "experience_years": 2, "education": "B.E. CSE", "remote_preference": "remote", "role": "admin"})
    data = r.get_json()["data"]
    assert data["user"]["role"] == "candidate"
    assert data["profile"]["remote_preference"] == "remote"
    r = client.post("/api/profile/skills", headers=auth_headers, json={"skill_name": "reactjs"})
    assert r.status_code == 201
    assert any(s["skill_name"] == "React" and s["source"] == "manual" for s in r.get_json()["data"]["items"])
    assert client.post("/api/profile/skills", headers=auth_headers,
                       json={"skill_name": "React"}).status_code == 409


def test_profile_social_links_avatar_and_custom_interests(client, auth_headers):
    r = client.put("/api/profile", headers=auth_headers, json={
        "social_links": {"linkedin": "linkedin.com/in/priya", "github": "", "unknown": "https://x.y"},
        "interests": ["Medical", "medical", "Electrical Engineering", "Underwater Welding"],
        "avatar_color": "teal"})
    data = r.get_json()["data"]
    assert r.status_code == 200
    assert data["profile"]["social_links"] == {"linkedin": "https://linkedin.com/in/priya"}
    assert sorted(data["interests"]) == ["Electrical Engineering", "Medical", "Underwater Welding"]
    assert data["profile"]["avatar_color"] == "teal"
    assert any(g["group"] == "Healthcare & Science" for g in data["options"]["interest_groups"])
    assert client.put("/api/profile", headers=auth_headers,
                      json={"social_links": {"github": "not a url"}}).status_code == 422
    assert client.put("/api/profile", headers=auth_headers, json={"avatar_color": "neon"}).status_code == 422

    png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    r = client.put("/api/profile/avatar", headers=auth_headers, json={"image": png})
    assert r.status_code == 200 and r.get_json()["data"]["profile"]["avatar_image"] == png
    assert client.get("/api/auth/me", headers=auth_headers).get_json()["data"]["user"]["avatar_image"] == png
    assert client.put("/api/profile/avatar", headers=auth_headers,
                      json={"image": "data:text/html;base64,PHA+"}).status_code == 422
    r = client.delete("/api/profile/avatar", headers=auth_headers)
    assert r.get_json()["data"]["profile"]["avatar_image"] is None


def test_job_search_experience_years(client, auth_headers):
    r = client.post("/api/jobs/search", headers=auth_headers, json={"query": "React Developer", "experience_years": 2})
    items = r.get_json()["data"]["items"]
    assert r.status_code == 200 and items
    assert all(j["min_experience_years"] is None or j["min_experience_years"] <= 2 for j in items)
    for bad in (51, -1, "ten"):
        assert client.post("/api/jobs/search", headers=auth_headers,
                           json={"query": "React Developer", "experience_years": bad}).status_code == 422


# --------------------------------------------------------------------- admin

def test_admin_endpoints(client, admin_headers):
    stats = client.get("/api/admin/stats", headers=admin_headers).get_json()["data"]
    assert stats["total_users"] >= 1 and stats["total_careers"] >= 14

    r = client.post("/api/admin/careers", headers=admin_headers, json={
        "career_name": "Site Reliability Engineer", "description": "Keeps services reliable.",
        "interest_area": "DevOps", "skills": [{"skill_name": "linux", "importance": 3}, "Kubernetes"]})
    assert r.status_code == 201, r.get_json()
    career = r.get_json()["data"]
    assert {s["skill_name"] for s in career["skills"]} == {"Linux", "Kubernetes"}
    r = client.put(f"/api/admin/careers/{career['career_id']}", headers=admin_headers, json={
        "career_name": "SRE", "description": "Reliability.", "interest_area": "DevOps"})
    assert r.status_code == 200 and r.get_json()["data"]["career_name"] == "SRE"
    assert client.delete(f"/api/admin/careers/{career['career_id']}", headers=admin_headers).status_code == 200

    r = client.post("/api/admin/learning-resources", headers=admin_headers, json={
        "skill_name": "Python", "resource_name": "Bad", "resource_url": "ftp://x"})
    assert r.status_code == 422

    analytics = client.get("/api/admin/analytics", headers=admin_headers).get_json()["data"]
    assert "top_missing_skills" in analytics and len(analytics["application_status"]) == 6
    users = client.get("/api/admin/users?limit=5", headers=admin_headers).get_json()["data"]
    assert users["items"] and all("password_hash" not in u for u in users["items"])


def test_error_envelope_for_unknown_route(client):
    r = client.get("/api/does-not-exist")
    body = r.get_json()
    assert r.status_code == 404 and body["success"] is False and body["error"]["code"] == "NOT_FOUND"


def test_mock_jobs_hidden_when_real_provider_active(app, client, auth_headers, monkeypatch):
    """Sample jobs from development must not appear in matches once JSearch is configured."""
    upload(client, auth_headers, make_pdf(SAMPLE_RESUME), "cv.pdf", "application/pdf")
    client.post("/api/jobs/search", headers=auth_headers, json={"query": "Python Developer"})
    mock_view = client.get("/api/matches?limit=50", headers=auth_headers).get_json()["data"]
    assert any(j["is_mock"] for j in mock_view["items"])

    monkeypatch.setitem(app.config, "JOB_PROVIDER", "jsearch")
    monkeypatch.setitem(app.config, "JSEARCH_API_KEY", "test-key")   # no request is made below
    real_view = client.get("/api/matches?limit=50", headers=auth_headers).get_json()["data"]
    assert not any(j["is_mock"] for j in real_view["items"])
    stored = client.get("/api/jobs?limit=50", headers=auth_headers).get_json()["data"]
    assert not any(j["is_mock"] for j in stored["items"])
    dash = client.get("/api/dashboard", headers=auth_headers).get_json()["data"]
    assert not any(j["is_mock"] for j in dash["top_jobs"] + dash["recent_matches"])
