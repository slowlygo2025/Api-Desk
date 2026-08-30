"""Precios USD con caché (CoinGecko + fallback)."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import Settings

FALLBACK_USD: dict[str, float] = {
    "BTC": 95_000.0,
    "ETH": 3_500.0,
    "BNB": 600.0,
    "AVAX": 35.0,
    "POL": 0.45,
    "MATIC": 0.45,
    "SOL": 150.0,
    "USDT": 1.0,
    "USDC": 1.0,
    "DAI": 1.0,
    "FDUSD": 1.0,
    "WBTC": 95_000.0,
}

COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "AVAX": "avalanche-2",
    "POL": "polygon-ecosystem-token",
    "MATIC": "matic-network",
    "SOL": "solana",
    "USDT": "tether",
    "USDC": "usd-coin",
    "DAI": "dai",
    "FDUSD": "first-digital-usd",
    "WBTC": "wrapped-bitcoin",
}


class PriceService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._cache: dict[str, tuple[float, float]] = {}
        self._ttl = 60.0

    async def get_usd(self, asset: str) -> float:
        asset = asset.upper()
        if asset == "MATIC":
            asset = "POL"
        now = time.time()
        if asset in self._cache and now - self._cache[asset][1] < self._ttl:
            return self._cache[asset][0]

        price = await self._fetch(asset)
        self._cache[asset] = (price, now)
        return price

    async def _fetch(self, asset: str) -> float:
        cg_id = COINGECKO_IDS.get(asset)
        if not cg_id:
            return FALLBACK_USD.get(asset, 0.0)
        try:
            url = f"{self.settings.coingecko_base_url}/simple/price"
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(url, params={"ids": cg_id, "vs_currencies": "usd"})
                data: dict[str, Any] = r.json()
                return float(data[cg_id]["usd"])
        except Exception:
            return FALLBACK_USD.get(asset, 0.0)

    async def to_usd(self, asset: str, amount: float) -> float:
        return amount * await self.get_usd(asset)
