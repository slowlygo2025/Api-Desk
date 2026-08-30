"""Mapeo packs RapidAPI (Opción A) → cuotas / scopes internos.

RapidAPI aplica el cupo mensual en el Gateway.
Estos valores sirven para keys internas (hidden X-API-Key) y documentación.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RapidPack:
    hub_name: str
    price_usd_month: float
    requests_per_month: int
    rate_per_hour: int
    daily_quota: int
    rate_per_min: int
    internal_plan: str  # retail | pro | institutional
    endpoints_tier: str  # basic | ultra


# Opción A — decidido 2026-08-30
RAPID_PACKS: dict[str, RapidPack] = {
    "BASIC": RapidPack(
        hub_name="BASIC",
        price_usd_month=0,
        requests_per_month=1_000,
        rate_per_hour=30,
        daily_quota=100,
        rate_per_min=10,
        internal_plan="retail",
        endpoints_tier="basic",
    ),
    "PRO": RapidPack(
        hub_name="PRO",
        price_usd_month=29,
        requests_per_month=50_000,
        rate_per_hour=600,
        daily_quota=2_000,
        rate_per_min=60,
        internal_plan="retail",
        endpoints_tier="basic",
    ),
    "ULTRA": RapidPack(
        hub_name="ULTRA",
        price_usd_month=79,
        requests_per_month=250_000,
        rate_per_hour=2_000,
        daily_quota=10_000,
        rate_per_min=120,
        internal_plan="pro",
        endpoints_tier="ultra",
    ),
    "MEGA": RapidPack(
        hub_name="MEGA",
        price_usd_month=199,
        requests_per_month=1_000_000,
        rate_per_hour=6_000,
        daily_quota=40_000,
        rate_per_min=300,
        internal_plan="institutional",
        endpoints_tier="ultra",
    ),
}

BASIC_HUB_PATHS = (
    "GET /v1/health",
    "GET /v1/ready",
    "GET /v1/chains",
    "GET /v1/whales",
    "GET /v1/whales/{id}",
    "GET /v1/whales/tx/{tx_hash}",
    "GET /v1/stats/overview",
    "GET /v1/entities/{address}",
)

ULTRA_EXTRA_PATHS = (
    "GET /v1/stats/timeseries",
    "GET /v1/market/assets",
    "GET /v1/market/analysis",
)
