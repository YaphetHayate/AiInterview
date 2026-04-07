import os

import psycopg2
import psycopg2.extras
from threading import Lock
from contextlib import contextmanager

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "dbname": os.environ.get("DB_NAME", "interview"),
}

_pool: list[psycopg2.extensions.connection] = []
_pool_lock = Lock()
_POOL_SIZE = 5


def _create_connection() -> psycopg2.extensions.connection:
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    return conn


def get_connection() -> psycopg2.extensions.connection:
    with _pool_lock:
        if _pool:
            conn = _pool.pop()
            if conn.closed == 0:
                return conn
    return _create_connection()


def release_connection(conn: psycopg2.extensions.connection):
    if conn.closed != 0:
        return
    try:
        conn.rollback()
    except Exception:
        return
    with _pool_lock:
        if len(_pool) < _POOL_SIZE:
            _pool.append(conn)
        else:
            conn.close()


@contextmanager
def db_cursor(dict_cursor: bool = False):
    conn = get_connection()
    cur = None
    try:
        if dict_cursor:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cur = conn.cursor()
        yield cur, conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        release_connection(conn)


def init_db():
    from db.schema import SCHEMA_SQL, SEED_SQL

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(SCHEMA_SQL)
        cur.execute(SEED_SQL)
        conn.commit()
        cur.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def close_all():
    with _pool_lock:
        for conn in _pool:
            try:
                if conn.closed == 0:
                    conn.close()
            except Exception:
                pass
        _pool.clear()
