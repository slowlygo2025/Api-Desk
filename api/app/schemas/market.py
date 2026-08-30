from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MarketTradeOut(BaseModel):
    exchange: str
    pair: str
    asset: str
    price: float
    amount: float
    notional_usd: float
    side: str
    ts: datetime
    trade_id: str = ""


class MarketBookLevelOut(BaseModel):
    price: float
    amount: float


class MarketOrderBookOut(BaseModel):
    exchange: str
    pair: str
    asset: str
    mid: float
    spread_bps: float
    bid_depth_usd: float
    ask_depth_usd: float
    imbalance: float
    bids: list[MarketBookLevelOut]
    asks: list[MarketBookLevelOut]
    ts: datetime


class MarketCandleOut(BaseModel):
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


class MarketVenueStatusOut(BaseModel):
    exchange: str
    pair: str
    ok: bool
    error: str | None = None
    trades: int = 0
    latency_ms: float = 0.0
    mid: float | None = None


class MarketSnapshotOut(BaseModel):
    kind: str = "market_microstructure"
    asset: str
    fetched_at: datetime
    venues_ok: int
    venues_total: int
    venues: list[MarketVenueStatusOut]
    meta: dict[str, Any]
    trades: list[MarketTradeOut]
    books: list[MarketOrderBookOut]
    candles_by_exchange: dict[str, list[MarketCandleOut]]
    note: str = (
        "Capa auxiliar de señales CEX (trades/book/volumen). "
        "El producto principal son whales on-chain."
    )


class MarketSignalOut(BaseModel):
    signal_type: str
    severity: str
    score: float
    title: str
    scope: str = "global"
    detail: dict[str, Any] = Field(default_factory=dict)
    ts: datetime


class MarketAnalysisOut(BaseModel):
    asset: str
    kind: str = "market_microstructure"
    source: str
    mid_price: float
    stress_score: float
    spillover_hint: float
    regime: str
    components: dict[str, float]
    book_summary: dict[str, Any]
    volume_summary: dict[str, Any]
    trades_summary: dict[str, Any]
    venues_summary: dict[str, Any]
    cross_exchange: dict[str, Any]
    signals: list[MarketSignalOut]
    fetched_at: datetime
    note: str = "Señales auxiliares para análisis. No sustituyen detección de whales."
