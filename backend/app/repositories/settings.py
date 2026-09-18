import sqlite3

from app.config import DEFAULT_PEAK_FACTOR


def get_map(conn: sqlite3.Connection) -> dict[str, str]:
    return {r["key"]: r["value"] for r in conn.execute("SELECT * FROM settings").fetchall()}


def peak_factor(conn: sqlite3.Connection) -> float:
    row = conn.execute("SELECT value FROM settings WHERE key='peak_factor'").fetchone()
    if not row:
        return DEFAULT_PEAK_FACTOR
    return float(row["value"])
