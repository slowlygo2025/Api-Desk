"""Tipos canónicos de microestructura de mercado (multi-asset)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class BookLevel:
    price: float
    amount: float


@dataclass
class MarketTrade:
    exchange: str
    pair: str
    asset: str
    price: float
    amount: float
    notional_usd: float
    side: str
    ts: datetime
    trade_id: str = ""


@dataclass
class MarketOrderBook:
    exchange: str
    pair: str
    asset: str
    bids: list[BookLevel]
    asks: list[BookLevel]
    ts: datetime
    mid: float = 0.0
    spread_bps: float = 0.0
    bid_depth: float = 0.0
    ask_depth: float = 0.0
    imbalance: float = 0.0


@dataclass
class MarketCandle:
    exchange: str
    pair: str
    asset: str
    interval: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float


@dataclass
class VenueSnapshot:
    exchange: str
    pair: str
    asset: str
    ok: bool
    error: str | None = None
    trades: list[MarketTrade] = field(default_factory=list)
    book: MarketOrderBook | None = None
    candles: list[MarketCandle] = field(default_factory=list)
    latency_ms: float = 0.0


@dataclass
class GlobalMarketSnapshot:
    asset: str
    venues: list[VenueSnapshot]
    trades: list[MarketTrade]
    books: list[MarketOrderBook]
    candles_by_exchange: dict[str, list[MarketCandle]]
    venues_ok: int
    venues_total: int
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    meta: dict[str, Any] = field(default_factory=dict)


def build_book(
    exchange: str,
    pair: str,
    asset: str,
    bids_raw: list[Any],
    asks_raw: list[Any],
    depth: int = 25,
) -> MarketOrderBook:
    bids = [BookLevel(float(r[0]), float(r[1])) for r in bids_raw[:depth] if float(r[1]) > 0]
    asks = [BookLevel(float(r[0]), float(r[1])) for r in asks_raw[:depth] if float(r[1]) > 0]
    bids.sort(key=lambda x: x.price, reverse=True)
    asks.sort(key=lambda x: x.price)
    best_bid = bids[0].price if bids else 0.0
    best_ask = asks[0].price if asks else 0.0
    mid = (best_bid + best_ask) / 2 if best_bid and best_ask else max(best_bid, best_ask)
    spread_bps = ((best_ask - best_bid) / mid * 10_000) if mid and best_ask >= best_bid else 0.0
    bid_depth = sum(l.price * l.amount for l in bids)
    ask_depth = sum(l.price * l.amount for l in asks)
    total = bid_depth + ask_depth
    imbalance = ((bid_depth - ask_depth) / total) if total else 0.0
    return MarketOrderBook(
        exchange=exchange,
        pair=pair,
        asset=asset,
        bids=bids,
        asks=asks,
        ts=datetime.now(timezone.utc),
        mid=mid,
        spread_bps=spread_bps,
        bid_depth=bid_depth,
        ask_depth=ask_depth,
        imbalance=imbalance,
    )
