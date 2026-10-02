"""Flask CLI commands.

    flask --app run init-db              # run database/schema.sql + database/seed.sql
    flask --app run create-admin         # create/promote an administrator account
"""
import getpass
from pathlib import Path

import click
import mysql.connector
from flask import current_app

from .auth.security import hash_password
from .config.settings import PROJECT_DIR
from .utils.validation import EMAIL_RE

DATABASE_DIR = PROJECT_DIR / "database"


def split_sql(script):
    """Split a SQL script into statements (handles quotes and -- comments)."""
    statements, buf, quote = [], [], None
    i = 0
    while i < len(script):
        ch = script[i]
        if quote:
            buf.append(ch)
            if ch == "\\" and i + 1 < len(script):
                buf.append(script[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in ("'", '"', "`"):
            quote = ch
            buf.append(ch)
        elif ch == "-" and script[i:i + 2] == "--":
            while i < len(script) and script[i] != "\n":
                i += 1
            continue
        elif ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
        else:
            buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def run_sql_file(path: Path, config, create_database=False):
    params = dict(host=config["DB_HOST"], port=config["DB_PORT"], user=config["DB_USER"],
                  password=config["DB_PASSWORD"], charset="utf8mb4", ssl_disabled=config["DB_SSL_DISABLED"])
    conn = mysql.connector.connect(**params)
    try:
        cur = conn.cursor()
        if create_database:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{config['DB_NAME']}` "
                        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.execute(f"USE `{config['DB_NAME']}`")
        for stmt in split_sql(path.read_text(encoding="utf-8")):
            cur.execute(stmt)
            if cur.with_rows:
                cur.fetchall()
        conn.commit()
        cur.close()
    finally:
        conn.close()


@click.command("init-db")
@click.option("--no-seed", is_flag=True, help="Create tables only.")
@click.option("--yes", is_flag=True, help="Do not ask for confirmation.")
def init_db_command(no_seed, yes):
    """(Re)create all tables and load seed data. DESTROYS existing data."""
    cfg = current_app.config
    if not yes:
        click.confirm(f"This drops and recreates all JobSense tables in '{cfg['DB_NAME']}'. Continue?", abort=True)
    run_sql_file(DATABASE_DIR / "schema.sql", cfg, create_database=True)
    click.echo("Schema created.")
    if not no_seed:
        run_sql_file(DATABASE_DIR / "seed.sql", cfg)
        click.echo("Seed data loaded.")


@click.command("create-admin")
@click.option("--name", default="Administrator")
@click.option("--email", prompt=True)
@click.option("--password", default=None, help="Omit to be prompted securely.")
def create_admin(name, email, password):
    """Create an admin account, or promote an existing user to admin."""
    from .models import user_model

    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        raise click.BadParameter("Invalid email address")
    existing = user_model.get_by_email_with_hash(email)
    if existing:
        user_model.promote_to_admin(existing["user_id"])
        click.echo(f"Promoted {email} to admin.")
        return
    if not password:
        password = getpass.getpass("Password (min 8 chars, letters + numbers): ")
    if len(password) < 8:
        raise click.BadParameter("Password must be at least 8 characters")
    user_model.create_user(name, email, hash_password(password), "admin")
    click.echo(f"Admin {email} created.")
