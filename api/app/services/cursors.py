"""Cursores de indexación por provider/chain + lag."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ProviderState, WhaleEvent
from app.services.metrics import metrics


async def get_or_create_state(session: AsyncSession, provider: str, chain: str) -> ProviderState:
    row = (
        await session.execute(
            select(ProviderState).where(ProviderState.provider == provider, ProviderState.chain == chain)
        )
    ).scalar_one_or_none()
    if row:
        return row
    row = ProviderState(provider=provider, chain=chain, cursor=None, healthy=True)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def advance_cursor(
    session: AsyncSession,
    provider: str,
    chain: str,
    cursor: str,
    *,
    healthy: bool = True,
    error: str | None = None,
) -> ProviderState:
    state = await get_or_create_state(session, provider, chain)
    state.cursor = cursor
    state.healthy = healthy
    state.last_error = error
    if healthy:
        state.last_success_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(state)
    return state


async def compute_ingest_lag_seconds(session: AsyncSession) -> float | None:
    row = (
        await session.execute(select(WhaleEvent).order_by(WhaleEvent.detected_at.desc()).limit(1))
    ).scalar_one_or_none()
    if not row or not row.block_time:
        return None
    lag = (datetime.now(timezone.utc) - row.block_time.replace(tzinfo=timezone.utc)).total_seconds()
    metrics.set_gauge("apidesk_ingest_lag_seconds", lag)
    return lag


async def list_provider_states(session: AsyncSession) -> list[ProviderState]:
    return list((await session.execute(select(ProviderState))).scalars().all())
