"""MySQL access layer built on mysql-connector-python connection pooling.

All SQL in the application goes through these helpers and uses parameterised
queries (%s placeholders) - values are never interpolated into SQL strings.
"""
import logging
from contextlib import contextmanager

import mysql.connector
from mysql.connector import pooling

logger = logging.getLogger(__name__)

_pool = None
_config = None


class DatabaseError(Exception):
    """Raised for database failures; the message never contains credentials."""


def init_db(config):
    global _pool, _config
    _config = {
        "host": config["DB_HOST"],
        "port": config["DB_PORT"],
        "database": config["DB_NAME"],
        "user": config["DB_USER"],
        "password": config["DB_PASSWORD"],
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "autocommit": False,
        "ssl_disabled": config["DB_SSL_DISABLED"],
        "connection_timeout": 10,
    }
    _pool = None
    try:
        _pool = pooling.MySQLConnectionPool(
            pool_name="jobsense_pool", pool_size=config["DB_POOL_SIZE"], pool_reset_session=True, **_config)
        logger.info("MySQL connection pool created (%s:%s/%s)", config["DB_HOST"], config["DB_PORT"], config["DB_NAME"])
    except mysql.connector.Error as exc:
        # The app still starts so health checks / non-DB routes respond; DB calls retry lazily.
        logger.error("Could not create MySQL pool: %s", exc.msg if hasattr(exc, "msg") else exc)


def _connect():
    global _pool
    if _config is None:
        raise DatabaseError("Database not initialised")
    try:
        if _pool is None:
            _pool = pooling.MySQLConnectionPool(
                pool_name="jobsense_pool", pool_size=5, pool_reset_session=True, **_config)
        return _pool.get_connection()
    except mysql.connector.errors.PoolError:
        # Pool exhausted - fall back to a direct connection rather than failing the request.
        return mysql.connector.connect(**_config)
    except mysql.connector.Error as exc:
        logger.error("Database connection failed: %s", getattr(exc, "msg", exc))
        raise DatabaseError("Database connection failed") from exc


@contextmanager
def transaction():
    """Yield a cursor inside a transaction; commits on success, rolls back on error."""
    conn = _connect()
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
        conn.commit()
    except mysql.connector.Error as exc:
        conn.rollback()
        logger.error("Database error: %s", getattr(exc, "msg", exc))
        raise DatabaseError("A database error occurred") from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def fetch_all(sql, params=None):
    with transaction() as cur:
        cur.execute(sql, params or ())
        return cur.fetchall()


def fetch_one(sql, params=None):
    with transaction() as cur:
        cur.execute(sql, params or ())
        row = cur.fetchone()
        cur.fetchall()  # drain any remaining rows
        return row


def execute(sql, params=None):
    """Execute a write statement; returns (lastrowid, rowcount)."""
    with transaction() as cur:
        cur.execute(sql, params or ())
        return cur.lastrowid, cur.rowcount


def execute_many(sql, seq_params):
    with transaction() as cur:
        cur.executemany(sql, seq_params)
        return cur.rowcount


def ping():
    try:
        fetch_one("SELECT 1 AS ok")
        return True
    except Exception:  # noqa: BLE001 - health check must never raise
        return False
