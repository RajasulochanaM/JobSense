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
]


def apply_migrations():
    try:
        existing = {(r["t"], r["c"]) for r in fetch_all(
            "SELECT TABLE_NAME AS t, COLUMN_NAME AS c FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE()")}
        if not existing:
            return  # schema not created yet (init-db has not run)
        for table, column, definition in ADDED_COLUMNS:
            if (table, column) not in existing:
                execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                logger.info("Migration: added %s.%s", table, column)
    except DatabaseError as exc:
        logger.warning("Schema migrations skipped: %s", exc)
