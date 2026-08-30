from datetime import datetime, timedelta, timezone

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.models import Entity, WhaleEvent
from app.db.session import get_db
from app.schemas.whales import (
    EntityListOut,
    EntityOut,
    FlowSankeyOut,
    SankeyLink,
    SankeyNode,
    StatsOverviewOut,
    TimeseriesBucket,
    TimeseriesOut,
    WhaleEventOut,
    WhaleListOut,
)
from app.services.auth import optional_client, require_scope
from app.services.ingest import IngestService
from app.services.serializers import whale_to_out

router = APIRouter(tags=["whales"])


@router.get("/whales", response_model=WhaleListOut)
async def list_whales(
    asset: str | None = None,
    chain: str | None = None,
    flow_type: str | None = None,
    min_usd: float | None = None,
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    _client=Depends(optional_client),
):
    q = select(WhaleEvent).order_by(WhaleEvent.detected_at.desc())
    if asset:
        q = q.where(WhaleEvent.asset == asset.upper())
    if chain:
        q = q.where(WhaleEvent.chain == chain.lower())
    if flow_type:
        q = q.where(WhaleEvent.flow_type == flow_type)
    if min_usd is not None:
        q = q.where(WhaleEvent.amount_usd >= min_usd)
    if cursor:
        q = q.where(WhaleEvent.detected_at < datetime.fromisoformat(cursor))

    q = q.limit(limit)
    rows = (await session.execute(q)).scalars().all()
    items = [whale_to_out(r) for r in rows]
    next_cursor = rows[-1].detected_at.isoformat() if rows else None
    return WhaleListOut(items=items, next_cursor=next_cursor, count=len(items))


@router.get("/whales/tx/{tx_hash}", response_model=list[WhaleEventOut])
async def get_by_tx(tx_hash: str, session: AsyncSession = Depends(get_db), _client=Depends(optional_client)):
    rows = (
        await session.execute(select(WhaleEvent).where(WhaleEvent.tx_hash == tx_hash))
    ).scalars().all()
    return [whale_to_out(r) for r in rows]


@router.get("/whales/{whale_id}", response_model=WhaleEventOut)
async def get_whale(whale_id: str, session: AsyncSession = Depends(get_db), _client=Depends(optional_client)):
    event = await session.get(WhaleEvent, whale_id)
    if not event:
        raise HTTPException(status_code=404, detail="Whale not found")
    return whale_to_out(event)


@router.post("/whales/ingest/run", response_model=WhaleListOut)
async def run_ingest(
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _client=Depends(require_scope("admin.ops")),
):
    """Ejecuta un ciclo de ingestión. Solo institutional (admin.ops)."""
    service = IngestService(settings)
    events = await service.run_once(session)
    items = [whale_to_out(e) for e in events]
    return WhaleListOut(items=items, next_cursor=None, count=len(items))


@router.get("/stats/overview", response_model=StatsOverviewOut)
async def stats_overview(
    window: str = Query(default="24h"),
    session: AsyncSession = Depends(get_db),
    _client=Depends(optional_client),
):
    hours = {"1h": 1, "24h": 24, "7d": 168}.get(window, 24)
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = (
        await session.execute(select(WhaleEvent).where(WhaleEvent.detected_at >= since))
    ).scalars().all()

    by_asset: dict[str, int] = {}
    by_flow: dict[str, int] = {}
    by_chain: dict[str, int] = {}
    volume = 0.0
    high_risk = 0
    for r in rows:
        by_asset[r.asset] = by_asset.get(r.asset, 0) + 1
        by_flow[r.flow_type] = by_flow.get(r.flow_type, 0) + 1
        by_chain[r.chain] = by_chain.get(r.chain, 0) + 1
        volume += r.amount_usd
        if r.risk_level == "high":
            high_risk += 1

    return StatsOverviewOut(
        window=window,
        total_events=len(rows),
        total_volume_usd=volume,
        by_asset=by_asset,
        by_flow_type=by_flow,
        by_chain=by_chain,
        high_risk_count=high_risk,
    )


def _window_since(window: str) -> datetime:
    hours = {"1h": 1, "24h": 24, "7d": 168}.get(window, 24)
    return datetime.now(timezone.utc) - timedelta(hours=hours)


def _bucket_delta(bucket: str) -> timedelta:
    return {"15m": timedelta(minutes=15), "1h": timedelta(hours=1), "4h": timedelta(hours=4), "1d": timedelta(days=1)}.get(
        bucket, timedelta(hours=1)
    )


@router.get("/stats/timeseries", response_model=TimeseriesOut)
async def stats_timeseries(
    window: str = Query(default="24h"),
    bucket: str = Query(default="1h"),
    session: AsyncSession = Depends(get_db),
    _client=Depends(require_scope("stats.timeseries")),
):
    since = _window_since(window)
    rows = (
        await session.execute(select(WhaleEvent).where(WhaleEvent.detected_at >= since))
    ).scalars().all()

    delta = _bucket_delta(bucket)
    buckets_map: dict[datetime, dict] = defaultdict(lambda: {"events": 0, "volume_usd": 0.0, "high_risk": 0})
    for r in rows:
        ts = r.detected_at.replace(minute=0, second=0, microsecond=0)
        if bucket == "15m":
            ts = ts.replace(minute=(r.detected_at.minute // 15) * 15)
        elif bucket == "4h":
            ts = ts.replace(hour=(r.detected_at.hour // 4) * 4)
        elif bucket == "1d":
            ts = ts.replace(hour=0)
        buckets_map[ts]["events"] += 1
        buckets_map[ts]["volume_usd"] += r.amount_usd
        if r.risk_level == "high":
            buckets_map[ts]["high_risk"] += 1

    buckets = [
        TimeseriesBucket(ts=ts, events=v["events"], volume_usd=v["volume_usd"], high_risk=v["high_risk"])
        for ts, v in sorted(buckets_map.items())
    ]
    return TimeseriesOut(window=window, bucket=bucket, buckets=buckets)


@router.get("/stats/flows/sankey", response_model=FlowSankeyOut)
async def stats_flows_sankey(
    window: str = Query(default="24h"),
    limit: int = Query(default=25, ge=5, le=50),
    session: AsyncSession = Depends(get_db),
    _client=Depends(require_scope("stats.flows")),
):
    since = _window_since(window)
    rows = (
        await session.execute(select(WhaleEvent).where(WhaleEvent.detected_at >= since))
    ).scalars().all()

    link_agg: dict[tuple[str, str, str, str], dict] = {}
    for r in rows:
        src = r.from_label or "unknown"
        tgt = r.to_label or "unknown"
        key = (src, r.from_entity_type, tgt, r.to_entity_type)
        if key not in link_agg:
            link_agg[key] = {"value": 0.0, "count": 0}
        link_agg[key]["value"] += r.amount_usd
        link_agg[key]["count"] += 1

    top = sorted(link_agg.items(), key=lambda x: x[1]["value"], reverse=True)[:limit]
    nodes_map: dict[str, SankeyNode] = {}
    links: list[SankeyLink] = []
    for (src, src_type, tgt, tgt_type), agg in top:
        src_id = f"{src}:{src_type}"
        tgt_id = f"{tgt}:{tgt_type}"
        nodes_map[src_id] = SankeyNode(id=src_id, label=src, entity_type=src_type)
        nodes_map[tgt_id] = SankeyNode(id=tgt_id, label=tgt, entity_type=tgt_type)
        links.append(
            SankeyLink(source=src_id, target=tgt_id, value=round(agg["value"], 2), count=agg["count"])
        )

    return FlowSankeyOut(window=window, nodes=list(nodes_map.values()), links=links)


@router.get("/entities", response_model=EntityListOut)
async def list_entities(
    q: str | None = None,
    chain: str | None = None,
    entity_type: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
    _client=Depends(optional_client),
):
    stmt = select(Entity)
    if chain:
        stmt = stmt.where(Entity.chain == chain.lower())
    if entity_type:
        stmt = stmt.where(Entity.entity_type == entity_type.lower())
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(Entity.label).like(like), func.lower(Entity.address).like(like)))

    total = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = (await session.execute(stmt.order_by(Entity.label).offset(offset).limit(limit))).scalars().all()
    items = [
        EntityOut(
            address=r.address,
            chain=r.chain,
            label=r.label,
            entity_type=r.entity_type,
            confidence=r.confidence,
            meta=r.meta or {},
        )
        for r in rows
    ]
    return EntityListOut(items=items, total=total)


@router.get("/entities/{address}", response_model=EntityOut)
async def get_entity(
    address: str,
    chain: str = Query(default="ethereum"),
    session: AsyncSession = Depends(get_db),
    _client=Depends(optional_client),
):
    row = (
        await session.execute(
            select(Entity).where(Entity.address == address, Entity.chain == chain.lower())
        )
    ).scalar_one_or_none()
    if not row:
        # fallback a classifier seed
        from app.services.classification import ClassificationService

        party = ClassificationService().resolve(chain, address)
        return EntityOut(
            address=address,
            chain=chain.lower(),
            label=party.label,
            entity_type=party.entity_type.value,
            confidence=party.confidence,
            meta={},
        )
    return EntityOut(
        address=row.address,
        chain=row.chain,
        label=row.label,
        entity_type=row.entity_type,
        confidence=row.confidence,
        meta=row.meta or {},
    )
