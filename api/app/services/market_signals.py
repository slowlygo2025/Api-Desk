"""Motor de señales de mercado multi-asset (auxiliar al producto whale)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import median
from typing import Any

from app.config import Settings
from app.providers.market.aggregator import MarketAggregator
from app.providers.market.registry import MARKET_ASSETS
from app.providers.market.types import GlobalMarketSnapshot
from app.services.spillover import estimate_spillover_vs_btc


@dataclass
class MarketSignal:
    signal_type: str
    severity: str
    score: float
    title: str
    detail: dict[str, Any] = field(default_factory=dict)
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scope: str = "global"


@dataclass
class MarketAnalysis:
    asset: str
    source: str
    mid_price: float
    stress_score: float
    spillover_hint: float
    regime: str
    signals: list[MarketSignal]
    book_summary: dict[str, Any]
    volume_summary: dict[str, Any]
    trades_summary: dict[str, Any]
    venues_summary: dict[str, Any]
    components: dict[str, float]
    cross_exchange: dict[str, Any]
    fetched_at: datetime
    kind: str = "market_microstructure"


class MarketSignalEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.aggregator = MarketAggregator(settings)
        self.imbalance_abs = 0.35
        self.volume_z = 2.2
        self.cross_spread_alert_bps = 25.0

    async def analyze(self, asset: str) -> MarketAnalysis:
        asset = asset.upper()
        snap = await self.aggregator.fetch_asset(asset)
        if snap.venues_ok == 0:
            raise RuntimeError(f"Sin datos CEX reales para {asset}: {[(v.exchange, v.error) for v in snap.venues]}")
        analysis = self.build_analysis(snap)
        sp = await estimate_spillover_vs_btc(asset, analysis.stress_score, analysis.components.get("trade_pressure", 0))
        analysis.spillover_hint = sp.score
        analysis.cross_exchange["spillover_vs_btc"] = {
            "score": sp.score,
            "btc_change_pct": sp.btc_change_pct,
            "asset_change_pct": sp.asset_change_pct,
            "beta_hint": sp.beta_hint,
            **sp.detail,
        }
        return analysis

    async def analyze_many(self, assets: list[str] | None = None) -> list[MarketAnalysis]:
        assets = assets or list(MARKET_ASSETS.keys())
        out: list[MarketAnalysis] = []
        for a in assets:
            try:
                out.append(await self.analyze(a))
            except Exception:
                continue
        return out

    def build_analysis(self, snap: GlobalMarketSnapshot) -> MarketAnalysis:
        large_trade = float(snap.meta.get("large_trade_usd") or MARKET_ASSETS[snap.asset].large_trade_usd)
        signals: list[MarketSignal] = []
        components = {"trade_pressure": 0.0, "book_pressure": 0.0, "volume_pressure": 0.0, "cross_pressure": 0.0}

        trades_summary = self._trades_summary(snap)
        for t in snap.trades:
            if t.notional_usd < large_trade:
                continue
            sev = "high" if t.notional_usd >= large_trade * 4 else "medium"
            score = min(1.0, t.notional_usd / (large_trade * 8))
            signals.append(
                MarketSignal(
                    signal_type="large_trade",
                    severity=sev,
                    score=score,
                    title=f"{snap.asset} {t.exchange}: {t.side} ${t.notional_usd:,.0f}",
                    detail={
                        "exchange": t.exchange,
                        "side": t.side,
                        "price": t.price,
                        "amount": t.amount,
                        "notional_usd": round(t.notional_usd, 2),
                        "trade_id": t.trade_id,
                    },
                    ts=t.ts,
                    scope="venue",
                )
            )
            components["trade_pressure"] = max(components["trade_pressure"], score)

        buy_n, sell_n = trades_summary["buy_notional_usd"], trades_summary["sell_notional_usd"]
        flow_total = buy_n + sell_n
        if flow_total > 0:
            flow_imb = (buy_n - sell_n) / flow_total
            if abs(flow_imb) >= 0.4 and flow_total >= large_trade:
                signals.append(
                    MarketSignal(
                        signal_type="trade_flow_imbalance",
                        severity="medium" if abs(flow_imb) < 0.7 else "high",
                        score=min(1.0, abs(flow_imb)),
                        title=f"{snap.asset}: flujo buys/sells desequilibrado",
                        detail={"flow_imbalance": round(flow_imb, 4), **trades_summary},
                    )
                )
                components["trade_pressure"] = max(components["trade_pressure"], abs(flow_imb) * 0.85)

        book_summary = self._books_summary(snap)
        if book_summary.get("venues", 0) > 0:
            imb = abs(float(book_summary["imbalance_mean"]))
            components["book_pressure"] = min(1.0, imb / 0.8)
            if imb >= self.imbalance_abs:
                signals.append(
                    MarketSignal(
                        signal_type="book_imbalance",
                        severity="high" if imb >= 0.55 else "medium",
                        score=min(1.0, imb),
                        title=f"{snap.asset}: order book desequilibrado",
                        detail=book_summary,
                    )
                )
            if float(book_summary.get("spread_bps_mean", 0)) >= 15:
                signals.append(
                    MarketSignal(
                        signal_type="book_thin_liquidity",
                        severity="medium",
                        score=min(1.0, float(book_summary["spread_bps_mean"]) / 40),
                        title=f"{snap.asset}: spread ensanchado",
                        detail=book_summary,
                    )
                )
                components["book_pressure"] = max(
                    components["book_pressure"], min(1.0, float(book_summary["spread_bps_mean"]) / 40)
                )

        volume_summary = self._volume_summary(snap)
        ratio = float(volume_summary.get("anomaly_ratio", 1.0) or 1.0)
        if ratio >= self.volume_z:
            score = min(1.0, (ratio - 1) / 4)
            signals.append(
                MarketSignal(
                    signal_type="volume_anomaly",
                    severity="high" if ratio >= 3.5 else "medium",
                    score=score,
                    title=f"{snap.asset}: volumen 1m anómalo",
                    detail=volume_summary,
                )
            )
            components["volume_pressure"] = score
        else:
            components["volume_pressure"] = max(0.0, min(1.0, (ratio - 1) / 4))

        cross = {
            "spread_bps": snap.meta.get("cross_exchange_spread_bps", 0.0),
            "mid_mean": snap.meta.get("mid_mean", 0.0),
            "mid_min": snap.meta.get("mid_min", 0.0),
            "mid_max": snap.meta.get("mid_max", 0.0),
            "vwap_hint": snap.meta.get("vwap_hint", 0.0),
        }
        xb = float(cross["spread_bps"] or 0)
        components["cross_pressure"] = min(1.0, xb / 80.0)
        if xb >= self.cross_spread_alert_bps:
            signals.append(
                MarketSignal(
                    signal_type="cross_exchange_dispersion",
                    severity="high" if xb >= 50 else "medium",
                    score=min(1.0, xb / 80.0),
                    title=f"{snap.asset}: dispersión cross-exchange {xb:.1f} bps",
                    detail=cross,
                )
            )

        for k, v in list(components.items()):
            components[k] = max(0.0, min(1.0, float(v)))

        stress = round(
            components["trade_pressure"] * 0.35
            + components["book_pressure"] * 0.25
            + components["volume_pressure"] * 0.2
            + components["cross_pressure"] * 0.2,
            4,
        )
        spillover = round(min(1.0, stress * 0.75 + components["trade_pressure"] * 0.15), 4)
        regime = _regime(stress)
        if stress >= 0.45:
            signals.append(
                MarketSignal(
                    signal_type="composite_stress",
                    severity="high" if stress >= 0.7 else "medium",
                    score=stress,
                    title=f"{snap.asset} market stress ({regime})",
                    detail={"components": components, "spillover_hint": spillover},
                )
            )

        mid = float(cross["mid_mean"] or cross["vwap_hint"] or 0)
        sources = ",".join(sorted(v.exchange for v in snap.venues if v.ok))
        return MarketAnalysis(
            asset=snap.asset,
            source=sources,
            mid_price=mid,
            stress_score=stress,
            spillover_hint=spillover,
            regime=regime,
            signals=signals,
            book_summary=book_summary,
            volume_summary=volume_summary,
            trades_summary=trades_summary,
            venues_summary={
                "ok": snap.venues_ok,
                "total": snap.venues_total,
                "venues": [
                    {
                        "exchange": v.exchange,
                        "pair": v.pair,
                        "ok": v.ok,
                        "error": v.error,
                        "trades": len(v.trades),
                        "latency_ms": round(v.latency_ms, 1),
                        "mid": v.book.mid if v.book else None,
                    }
                    for v in snap.venues
                ],
            },
            components=components,
            cross_exchange=cross,
            fetched_at=snap.fetched_at,
        )

    def _trades_summary(self, snap: GlobalMarketSnapshot) -> dict[str, Any]:
        buy = sell = 0.0
        by_ex: dict[str, float] = {}
        for t in snap.trades:
            by_ex[t.exchange] = by_ex.get(t.exchange, 0.0) + t.notional_usd
            if t.side == "buy":
                buy += t.notional_usd
            elif t.side == "sell":
                sell += t.notional_usd
        notionals = [t.notional_usd for t in snap.trades]
        return {
            "count": len(snap.trades),
            "buy_notional_usd": round(buy, 2),
            "sell_notional_usd": round(sell, 2),
            "max_trade_usd": round(max(notionals), 2) if notionals else 0.0,
            "median_trade_usd": round(median(notionals), 2) if notionals else 0.0,
            "notional_by_exchange": {k: round(v, 2) for k, v in by_ex.items()},
        }

    def _books_summary(self, snap: GlobalMarketSnapshot) -> dict[str, Any]:
        if not snap.books:
            return {"venues": 0}
        imbs = [b.imbalance for b in snap.books]
        spreads = [b.spread_bps for b in snap.books]
        return {
            "venues": len(snap.books),
            "imbalance_mean": round(sum(imbs) / len(imbs), 4),
            "spread_bps_mean": round(sum(spreads) / len(spreads), 2),
            "bid_depth_usd_total": round(sum(b.bid_depth for b in snap.books), 2),
            "ask_depth_usd_total": round(sum(b.ask_depth for b in snap.books), 2),
            "per_venue": [
                {
                    "exchange": b.exchange,
                    "mid": b.mid,
                    "imbalance": round(b.imbalance, 4),
                    "spread_bps": round(b.spread_bps, 2),
                }
                for b in snap.books
            ],
        }

    def _volume_summary(self, snap: GlobalMarketSnapshot) -> dict[str, Any]:
        series = [[c.quote_volume for c in candles] for candles in snap.candles_by_exchange.values() if candles]
        if not series:
            return {"anomaly_ratio": 0.0, "last_quote_volume": 0.0, "venues": 0}
        min_len = min(len(s) for s in series)
        agg = [sum(s[i] for s in series) for i in range(-min_len, 0)]
        last = agg[-1]
        hist = agg[:-1] or agg
        med = median(hist) or 1.0
        return {
            "interval": "1m",
            "venues": len(series),
            "last_quote_volume": round(last, 2),
            "median_quote_volume": round(med, 2),
            "anomaly_ratio": round(last / med if med else 0.0, 4),
            "candles_aligned": min_len,
        }


def _regime(stress: float) -> str:
    if stress >= 0.75:
        return "extreme"
    if stress >= 0.5:
        return "stressed"
    if stress >= 0.28:
        return "building"
    return "calm"
