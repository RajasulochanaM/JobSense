"""Shared pytest fixtures.

Unit tests (NLP, TF-IDF, scoring, parsing, providers) need no database.
Integration tests marked `db` run against a separate MySQL database
(TEST_DB_NAME, default `jobsense_test`) that is rebuilt from database/schema.sql
and database/seed.sql at the start of the session. If MySQL is not reachable
they are skipped with an explanatory message.
"""
import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import TestConfig  # noqa: E402

SAMPLE_RESUME = """Priya Sharma
priya.sharma@example.com | +91 98765 43210
Summary
Frontend developer with 2 years of experience building responsive web applications.
Skills
ReactJS, JavaScript, HTML5, CSS3, NodeJS, MySQL, Git, REST APIs, Python3
Experience
Software Engineer, Acme Technologies, Chennai  Jan 2023 - Present
Built React dashboards and Node.js/Express REST APIs backed by MySQL.
Education
B.Tech in Computer Science, Anna University, 2022
"""


def make_pdf(text: str) -> bytes:
    """Build a small, valid, text-based PDF (Helvetica) without extra dependencies."""
    lines = [l.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for l in text.splitlines()]
    ops = ["BT", "/F1 11 Tf", "14 TL", "50 780 Td"]
    for line in lines:
        ops.append(f"({line}) Tj T*")
    ops.append("ET")
    stream = "\n".join(ops).encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 5 0 R >> >> "
        b"/Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return out.getvalue()


def make_docx(text: str) -> bytes:
    from docx import Document
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.fixture
def resume_text():
    return SAMPLE_RESUME


@pytest.fixture
def pdf_bytes():
    return make_pdf(SAMPLE_RESUME)


@pytest.fixture
def docx_bytes():
    return make_docx(SAMPLE_RESUME)


# ------------------------------------------------------------------ database

_db_state = {"checked": False, "ok": False, "reason": ""}


def _prepare_test_database():
    if _db_state["checked"]:
        return _db_state["ok"]
    _db_state["checked"] = True
    try:
        from app.cli import DATABASE_DIR, run_sql_file
        cfg = {k: getattr(TestConfig, k) for k in ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
                                                    "DB_SSL_DISABLED")}
        run_sql_file(DATABASE_DIR / "schema.sql", cfg, create_database=True)
        run_sql_file(DATABASE_DIR / "seed.sql", cfg)
        _db_state["ok"] = True
    except Exception as exc:  # noqa: BLE001
        _db_state["reason"] = f"MySQL test database unavailable ({type(exc).__name__}: {exc})"
    return _db_state["ok"]


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    if not _prepare_test_database():
        pytest.skip(_db_state["reason"])
    from app import create_app

    class Cfg(TestConfig):
        UPLOAD_FOLDER = str(tmp_path_factory.mktemp("uploads"))

    return create_app(Cfg)


@pytest.fixture
def client(app):
    return app.test_client()


_counter = {"n": 0}


def register(client, name="Test User", email=None, password="Passw0rd!"):
    _counter["n"] += 1
    email = email or f"user{_counter['n']}_{id(client)}@example.com"
    resp = client.post("/api/auth/register", json={
        "name": name, "email": email, "password": password, "password_confirmation": password})
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["data"]["token"], email


@pytest.fixture
def auth_headers(client):
    token, _ = register(client)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client):
    resp = client.post("/api/auth/login", json={"email": "admin@jobsense.local", "password": "Admin@12345"})
    assert resp.status_code == 200, resp.get_json()
    return {"Authorization": f"Bearer {resp.get_json()['data']['token']}"}
