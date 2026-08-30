"""Sincroniza catálogo de exchanges → tabla entities."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.exchange_catalog import catalog_entries
from app.db.models import Entity


async def sync_exchange_catalog(session: AsyncSession) -> int:
    upserted = 0
    for row in catalog_entries():
        existing = (
            await session.execute(
                select(Entity).where(Entity.chain == row["chain"], Entity.address == row["address"])
            )
        ).scalar_one_or_none()
        if existing:
            existing.label = row["label"]
            existing.entity_type = row["entity_type"]
            existing.confidence = row["confidence"]
            existing.meta = {"source": "exchange_catalog"}
        else:
            session.add(
                Entity(
                    address=row["address"],
                    chain=row["chain"],
                    label=row["label"],
                    entity_type=row["entity_type"],
                    confidence=row["confidence"],
                    meta={"source": "exchange_catalog"},
                )
            )
            upserted += 1
    await session.commit()
    return upserted
