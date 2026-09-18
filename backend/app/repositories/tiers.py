import sqlite3


def list_ordered(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT id, up_to, price, sort_order FROM tiers ORDER BY sort_order").fetchall()
    return [dict(r) for r in rows]


def as_calc_rows(conn: sqlite3.Connection) -> list[dict]:
    return [{"up_to": r["up_to"], "price": r["price"]} for r in list_ordered(conn)]
