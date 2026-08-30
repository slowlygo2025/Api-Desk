from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.models import MarketSignalEvent
from app.db.session import get_db
from app.providers.market.aggregator import MarketAggregator
from app.providers.market.registry import MARKET_ASSETS, list_market_assets
from app.schemas.market import (
    MarketAnalysisOut,
    MarketBookLevelOut,
    MarketCandleOut,
    MarketOrderBookOut,
    MarketSignalOut,
    MarketSnapshotOut,
    MarketTradeOut,
    MarketVenueStatusOut,
)
from app.services.auth import optional_client, require_scope
from app.services.market_signals import MarketSignalEngine

router = APIRouter(prefix="/market", tags=["market-signals"])


def _snapshot_out(snap) -> MarketSnapshotOut:
    return MarketSnapshotOut(
        asset=snap.asset,
        fetched_at=snap.fetched_at,
        venues_ok=snap.venues_ok,
        venues_total=snap.venues_total,
        venues=[
            MarketVenueStatusOut(
                exchange=v.exchange,
                pair=v.pair,
                ok=v.ok,
                error=v.error,
                trades=len(v.trades),
                latency_ms=round(v.latency_ms, 1),
                mid=v.book.mid if v.book else None,
            )
            for v in snap.venues
        ],
        meta=snap.meta,
        trades=[
            MarketTradeOut(
                exchange=t.exchange,
                pair=t.pair,
                asset=t.asset,
                price=t.price,
                amount=t.amount,
                notional_usd=t.notional_usd,
                side=t.side,
                ts=t.ts,
                trade_id=t.trade_id,
            )
            for t in snap.trades
        ],
        books=[
            MarketOrderBookOut(
                exchange=b.exchange,
                pair=b.pair,
                asset=b.asset,
                mid=b.mid,
                spread_bps=b.spread_bps,
                bid_depth_usd=b.bid_depth,
                ask_depth_usd=b.ask_depth,
                imbalance=b.imbalance,
                bids=[MarketBookLevelOut(price=x.price, amount=x.amount) for x in b.bids],
                asks=[MarketBookLevelOut(price=x.price, amount=x.amount) for x in b.asks],
                ts=b.ts,
            )
            for b in snap.books
        ],
        candles_by_exchange={
            ex: [
                MarketCandleOut(
                    exchange=c.exchange,
                    pair=c.pair,
                    asset=c.asset,
                    interval=c.interval,
                    open_time=c.open_time,
                    open=c.open,
                    high=c.high,
                    low=c.low,
                    close=c.close,
                    volume=c.volume,
                    quote_volume=c.quote_volume,
                )
                for c in candles
            ]
            for ex, candles in snap.candles_by_exchange.items()
        },
    )


def _analysis_out(a) -> MarketAnalysisOut:
    return MarketAnalysisOut(
        asset=a.asset,
        source=a.source,
        mid_price=a.mid_price,
        stress_score=a.stress_score,
        spillover_hint=a.spillover_hint,
        regime=a.regime,
        components=a.components,
        book_summary=a.book_summary,
        volume_summary=a.volume_summary,
        trades_summary=a.trades_summary,
        venues_summary=a.venues_summary,
        cross_exchange=a.cross_exchange,
        signals=[
            MarketSignalOut(
                signal_type=s.signal_type,
                severity=s.severity,
                score=s.score,
                title=s.title,
                scope=s.scope,
                detail=s.detail,
                ts=s.ts,
            )
            for s in a.signals
        ],
        fetched_at=a.fetched_at,
    )


@router.get("/assets")
async def market_assets(_client=Depends(optional_client)):
    return {"assets": list_market_assets(), "total": len(MARKET_ASSETS)}


@router.get("/snapshot", response_model=MarketSnapshotOut)
async def market_snapshot(
    asset: str = Query(default="BTC", description="BTC|ETH|SOL|BNB|XMR"),
    settings: Settings = Depends(get_settings),
    _client=Depends(optional_client),
):
    asset = asset.upper()
    if asset not in MARKET_ASSETS:
        raise HTTPException(status_code=400, detail=f"Unsupported asset. Use: {list(MARKET_ASSETS)}")
    snap = await MarketAggregator(settings).fetch_asset(asset)
    if snap.venues_ok == 0:
        raise HTTPException(status_code=503, detail={"error": "no_venue_data", "asset": asset})
    return _snapshot_out(snap)


@router.get("/analysis", response_model=MarketAnalysisOut)
async def market_analysis(
    asset: str = Query(default="BTC"),
    persist: bool = Query(default=True),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _client=Depends(optional_client),
):
    asset = asset.upper()
    if asset not in MARKET_ASSETS:
        raise HTTPException(status_code=400, detail=f"Unsupported asset. Use: {list(MARKET_ASSETS)}")
    try:
        analysis = await MarketSignalEngine(settings).analyze(asset)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if persist:
        for s in analysis.signals:
            session.add(
                MarketSignalEvent(
                    asset=analysis.asset,
                    signal_type=s.signal_type,
                    severity=s.severity,
                    score=s.score,
                    title=s.title,
                    stress_score=analysis.stress_score,
                    spillover_hint=analysis.spillover_hint,
                    regime=analysis.regime,
                    source=analysis.source,
                    detail={**s.detail, "scope": s.scope},
                )
            )
        await session.commit()
    return _analysis_out(analysis)


@router.get("/signals", response_model=list[MarketSignalOut])
async def market_signals_history(
    asset: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    client=Depends(require_scope("market.signals")),
):
    q = select(MarketSignalEvent).order_by(MarketSignalEvent.created_at.desc()).limit(limit)
    if asset:
        q = q.where(MarketSignalEvent.asset == asset.upper())
    rows = (await session.execute(q)).scalars().all()
    return [
        MarketSignalOut(
            signal_type=r.signal_type,
            severity=r.severity,
            score=r.score,
            title=r.title,
            scope=(r.detail or {}).get("scope", "global"),
            detail={**(r.detail or {}), "asset": r.asset},
            ts=r.created_at,
        )
        for r in rows
    ]
