import pytest

from app.engines.peak_compare import compare_plain_vs_peak
from app.engines.tier_progressive import calc_bill

TIERS = [{"up_to": 180, "price": 0.52}, {"up_to": 260, "price": 0.62}, {"up_to": None, "price": 0.82}]


def test_tier_first_band_only():
    r = calc_bill(120, TIERS, 1.0)
    assert r["total"] == 62.40
    assert len(r["segments"]) == 1


def test_tier_three_bands():
    r = calc_bill(400, TIERS, 1.0)
    assert r["total"] == 258.00
    assert len(r["segments"]) == 3


def test_peak_factor_multiplies_prices():
    plain = calc_bill(400, TIERS, 1.0)
    peak = calc_bill(400, TIERS, 1.2)
    assert peak["total"] == 309.60
    assert peak["total"] > plain["total"]


def test_compare_delta():
    c = compare_plain_vs_peak(400, TIERS, 1.2)
    assert c["plain_total"] == 258.00
    assert c["peak_total"] == 309.60
    assert c["delta"] == 51.60


def test_negative_kwh_raises():
    with pytest.raises(ValueError):
        calc_bill(-1, TIERS, 1.0)
