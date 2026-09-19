import sqlite3


def list_all(conn: sqlite3.Connection) -> list[dict]:
    q = """
    SELECT r.*, a.name AS account_name, a.meter_no AS meter_no
    FROM readings r LEFT JOIN accounts a ON a.id = r.account_id
    ORDER BY r.id
    """
    return [dict(r) for r in conn.execute(q).fetchall()]


def for_account(conn: sqlite3.Connection, account_id: int) -> list[dict]:
    q = "SELECT * FROM readings WHERE account_id=? ORDER BY id"
    return [dict(r) for r in conn.execute(q, (account_id,)).fetchall()]


def find_by_period(conn: sqlite3.Connection, account_id: int, period: str) -> dict | None:
    q = "SELECT * FROM readings WHERE account_id=? AND period=?"
    row = conn.execute(q, (account_id, period)).fetchone()
    return dict(row) if row else None


def insert(conn: sqlite3.Connection, account_id: int, period: str, kwh: float, peak: bool) -> int:
    cur = conn.execute(
        "INSERT INTO readings(account_id, period, kwh, peak) VALUES (?,?,?,?)",
        (account_id, period, kwh, 1 if peak else 0),
    )
    return int(cur.lastrowid)


def update(conn: sqlite3.Connection, reading_id: int, kwh: float, peak: bool) -> None:
    conn.execute(
        "UPDATE readings SET kwh=?, peak=? WHERE id=?",
        (kwh, 1 if peak else 0, reading_id),
    )


def persist_rows(conn: sqlite3.Connection, rows: list[dict]) -> tuple[int, int]:
    inserted = replaced = 0
    for row in rows:
        kwh = float(row["kwh"])
        existing = find_by_period(conn, row["account_id"], row["period"])
        if existing:
            update(conn, existing["id"], kwh, bool(row["peak"]))
            replaced += 1
        else:
            insert(conn, row["account_id"], row["period"], kwh, bool(row["peak"]))
            inserted += 1
    return inserted, replaced
