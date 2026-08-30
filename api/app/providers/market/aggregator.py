"""Agregador multi-venue para un asset de señales de mercado."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.config import Settings
from app.providers.market.registry import MARKET_ASSETS, AssetMarketSpec
from app.providers.market.types import GlobalMarketSnapshot
from app.providers.market.venues import VENUES

logger = logging.getLogger(__name__)


class MarketAggregator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _pairs_for(self, spec: AssetMarketSpec) -> list[tuple[str, str]]:
        mapping = {
            "kraken": spec.kraken,
            "kucoin": spec.kucoin,
            "mexc": spec.mexc,
            "bitfinex": spec.bitfinex,
            "htx": spec.htx,
        }
        enabled = {
            x.strip().lower()
            for x in (getattr(self.settings, "market_venues", "") or "").split(",")
            if x.strip()
        }
        out = []
        for venue, pair in mapping.items():
            if not pair:
                continue
            if enabled and venue not in enabled:
                continue
            out.append((venue, pair))
        return out

    async def fetch_asset(
        self,
        asset: str,
        trade_limit: int = 80,
        book_depth: int = 25,
        candle_limit: int = 60,
    ) -> GlobalMarketSnapshot:
        asset = asset.upper()
        spec = MARKET_ASSETS.get(asset)
        if not spec:
            raise ValueError(f"Asset no soportado en market signals: {asset}")

        async def _fetch_with_retry(venue_name: str, pair: str):
            venue = VENUES[venue_name]
            snap = await venue.fetch(asset, pair, trade_limit, book_depth, candle_limit)
            if not snap.ok:
                logger.warning("venue %s retry for %s: %s", venue_name, asset, snap.error)
                snap = await venue.fetch(asset, pair, trade_limit, book_depth, candle_limit)
            return snap

        jobs = [_fetch_with_retry(venue_name, pair) for venue_name, pair in self._pairs_for(spec)]
        results = list(await asyncio.gather(*jobs)) if jobs else []
        ok = [v for v in results if v.ok]
        trades, books, candles_by = [], [], {}
        for v in ok:
            trades.extend(v.trades)
            if v.book:
                books.append(v.book)
            if v.candles:
                candles_by[v.exchange] = v.candles
        trades.sort(key=lambda t: t.ts)

        mids = [b.mid for b in books if b.mid > 0]
        cross_bps = 0.0
        if len(mids) >= 2:
            cross_bps = (max(mids) - min(mids)) / (sum(mids) / len(mids)) * 10_000
        vwap = 0.0
        den = sum(t.amount for t in trades)
        if den:
            vwap = sum(t.price * t.amount for t in trades) / den

        return GlobalMarketSnapshot(
            asset=asset,
            venues=results,
            trades=trades,
            books=books,
            candles_by_exchange=candles_by,
            venues_ok=len(ok),
            venues_total=len(results),
            fetched_at=datetime.now(timezone.utc),
            meta={
                "cross_exchange_spread_bps": round(cross_bps, 4),
                "vwap_hint": round(vwap, 6),
                "mid_mean": round(sum(mids) / len(mids), 6) if mids else 0.0,
                "mid_min": round(min(mids), 6) if mids else 0.0,
                "mid_max": round(max(mids), 6) if mids else 0.0,
                "large_trade_usd": spec.large_trade_usd,
            },
        )
