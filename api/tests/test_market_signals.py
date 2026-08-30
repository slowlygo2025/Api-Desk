from datetime import datetime, timezone

from app.config import Settings
from app.providers.market.types import (
    BookLevel,
    GlobalMarketSnapshot,
    MarketCandle,
    MarketOrderBook,
    MarketTrade,
    VenueSnapshot,
)
from app.services.market_signals import MarketSignalEngine


def test_market_analysis_multi_asset_layers():
    now = datetime.now(timezone.utc)
    book = MarketOrderBook(
        exchange="kraken",
        pair="XBTUSD",
        asset="BTC",
        bids=[BookLevel(60000, 2)],
        asks=[BookLevel(60100, 0.5)],
        ts=now,
        mid=60050,
        spread_bps=16.0,
        bid_depth=120000,
        ask_depth=30050,
        imbalance=0.6,
    )
    candles = [
        MarketCandle("kraken", "XBTUSD", "BTC", "1m", now, 60000, 60100, 59900, 60000, 1, 60000)
        for _ in range(20)
    ] + [MarketCandle("kraken", "XBTUSD", "BTC", "1m", now, 60000, 61000, 59900, 60500, 10, 600000)]

    snap = GlobalMarketSnapshot(
        asset="BTC",
        venues=[VenueSnapshot("kraken", "XBTUSD", "BTC", True, trades=[], book=book, candles=candles)],
        trades=[MarketTrade("kraken", "XBTUSD", "BTC", 60000, 2, 120000, "buy", now, "1")],
        books=[book],
        candles_by_exchange={"kraken": candles},
        venues_ok=1,
        venues_total=1,
        meta={"large_trade_usd": 100000, "cross_exchange_spread_bps": 5.0, "mid_mean": 60050, "vwap_hint": 60000},
        fetched_at=now,
    )
    analysis = MarketSignalEngine(Settings()).build_analysis(snap)
    types = {s.signal_type for s in analysis.signals}
    assert analysis.asset == "BTC"
    assert "large_trade" in types
    assert analysis.kind == "market_microstructure"
