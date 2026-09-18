"""Progressive tier electricity: each kWh charged at its band price."""

from app.engines.helpers import kwh_qty, money


def calc_bill(kwh: float, tiers: list[dict], peak_factor: float = 1.0) -> dict:
    """tiers: [{up_to, price}] last up_to may be None for open end."""
    remain = float(kwh)
    if remain < 0:
        raise ValueError("kwh must be non-negative")
    segments = []
    total = 0.0
    prev = 0.0
    pf = float(peak_factor)
    for t in tiers:
        up = t.get("up_to")
        price = float(t["price"]) * pf
        if up is None:
            qty = remain
        else:
            span = float(up) - prev
            qty = min(remain, max(0.0, span))
        if qty > 1e-9:
            amount = money(qty * price)
            segments.append(
                {
                    "from_kwh": prev,
                    "to_kwh": prev + qty,
                    "qty": kwh_qty(qty),
                    "price": round(price, 4),
                    "amount": amount,
                }
            )
            total += amount
            remain -= qty
        if up is not None:
            prev = float(up)
        if remain <= 1e-9:
            break
    return {
        "kwh": kwh_qty(kwh),
        "peak_factor": pf,
        "total": money(total),
        "segments": segments,
    }
