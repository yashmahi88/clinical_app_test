import sqlite3
from collections.abc import Iterator

from app.database import connect


def get_conn() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def to_dicts(rows) -> list[dict]:
    return [dict(r) for r in rows]


def to_dict(row) -> dict | None:
    return dict(row) if row is not None else None
