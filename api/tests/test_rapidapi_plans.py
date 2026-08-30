"""Tests Opción A — packs RapidAPI."""

from app.services.rapidapi_plans import BASIC_HUB_PATHS, RAPID_PACKS, ULTRA_EXTRA_PATHS


def test_option_a_prices():
    assert RAPID_PACKS["BASIC"].price_usd_month == 0
    assert RAPID_PACKS["PRO"].price_usd_month == 29
    assert RAPID_PACKS["ULTRA"].price_usd_month == 79
    assert RAPID_PACKS["MEGA"].price_usd_month == 199


def test_option_a_quotas_monotonic():
    order = ["BASIC", "PRO", "ULTRA", "MEGA"]
    prev = 0
    for name in order:
        n = RAPID_PACKS[name].requests_per_month
        assert n > prev
        prev = n


def test_endpoint_tiers_documented():
    assert len(BASIC_HUB_PATHS) >= 7
    assert any("timeseries" in p for p in ULTRA_EXTRA_PATHS)
    assert any("market/analysis" in p for p in ULTRA_EXTRA_PATHS)
