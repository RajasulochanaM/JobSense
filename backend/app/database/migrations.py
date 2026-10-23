"""Idempotent, additive schema upgrades for databases created from an older schema.sql.

Fresh installs get these columns from database/schema.sql; this only fills the gap for
existing databases so they do not need to be dropped and re-seeded.
"""
import logging

from .db import DatabaseError, execute, fetch_all

logger = logging.getLogger(__name__)

# (table, column, column definition)
ADDED_COLUMNS = [
    ("user_profiles", "social_links", "TEXT NULL"),
    ("user_profiles", "avatar_image", "MEDIUMTEXT NULL"),
    ("user_profiles", "avatar_color", "VARCHAR(20) NULL"),
    ("applications", "posting_opened_at", "DATETIME NULL"),
]

# Whole tables added after the first release (same definitions as schema.sql).
ADDED_TABLES = {
    "application_events": """CREATE TABLE IF NOT EXISTS application_events (
        event_id        INT UNSIGNED NOT NULL AUTO_INCREMENT,
        application_id  INT UNSIGNED NOT NULL,
        event_type      ENUM('created', 'status_change', 'posting_opened') NOT NULL,
        from_status     VARCHAR(20) NULL,
        to_status       VARCHAR(20) NOT NULL,
        source          ENUM('user', 'auto') NOT NULL DEFAULT 'user',
        created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (event_id),
        KEY idx_app_events_application (application_id, created_at),
        CONSTRAINT fk_app_events_application FOREIGN KEY (application_id)
            REFERENCES applications (application_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
}


def apply_migrations():
    try:
        existing = {(r["t"], r["c"]) for r in fetch_all(
            "SELECT TABLE_NAME AS t, COLUMN_NAME AS c FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE()")}
        if not existing:
            return  # schema not created yet (init-db has not run)
        tables = {t for t, _ in existing}
        for table, ddl in ADDED_TABLES.items():
            if table not in tables:
                execute(ddl)
                logger.info("Migration: created table %s", table)
        for table, column, definition in ADDED_COLUMNS:
            if (table, column) not in existing:
                execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                logger.info("Migration: added %s.%s", table, column)
    except DatabaseError as exc:
        logger.warning("Schema migrations skipped: %s", exc)
