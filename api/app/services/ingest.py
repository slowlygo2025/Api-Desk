"""Ingest avanzado: umbrales por asset, cursores EVM, métricas."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import WhaleEvent
from app.providers.base import FetchLimits, RawTransfer
from app.providers.evm import EvmProvider
from app.providers.router import ProviderRouter
from app.services.classification import ClassificationService
from app.services.cursors import advance_cursor, get_or_create_state
from app.services.impact import ImpactService
from app.services.metrics import metrics
from app.services.pricing import PriceService
from app.services.risk import RiskService

logger = logging.getLogger(__name__)


class IngestService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.router = ProviderRouter(settings)
        self.prices = PriceService(settings)
        self.classifier = ClassificationService()
        self.risk = RiskService()
        self.impact = ImpactService()

    def threshold_for(self, asset: str) -> float:
        a = asset.upper()
        if a == "BTC" or a == "WBTC":
            return self.settings.threshold_btc_usd
        if a == "ETH":
            return self.settings.threshold_eth_usd
        if a in {"USDT", "USDC", "DAI", "FDUSD"}:
            return self.settings.threshold_stable_usd
        return self.settings.threshold_alt_usd or self.settings.whale_threshold_usd

    async def build_limits(self) -> FetchLimits:
        async def min_for(asset: str, fallback: float, thr: float) -> float:
            px = await self.prices.get_usd(asset)
            return thr / px if px > 0 else thr / fallback

        return FetchLimits(
            min_btc=await min_for("BTC", 100_000, self.settings.threshold_btc_usd),
            min_eth=await min_for("ETH", 3_500, self.settings.threshold_eth_usd),
            min_stable=self.settings.threshold_stable_usd,
            min_bnb=await min_for("BNB", 600, self.settings.threshold_alt_usd),
            min_avax=await min_for("AVAX", 35, self.settings.threshold_alt_usd),
            min_pol=await min_for("POL", 0.45, self.settings.threshold_alt_usd),
            min_sol=await min_for("SOL", 150, self.settings.threshold_alt_usd),
        )

    async def process_raw(self, session: AsyncSession, raw: RawTransfer) -> tuple[WhaleEvent | None, bool]:
        amount_usd = await self.prices.to_usd(raw.asset, raw.amount)
        thr = self.threshold_for(raw.asset)
        if amount_usd < thr:
            return None, False

        log_index = raw.log_index if raw.log_index is not None else 0
        q = await session.execute(
            select(WhaleEvent).where(
                WhaleEvent.chain == raw.chain,
                WhaleEvent.tx_hash == raw.tx_hash,
                WhaleEvent.log_index == log_index,
            )
        )
        existing = q.scalar_one_or_none()
        if existing:
            return existing, False

        clf = self.classifier.classify(raw.chain, raw.asset, raw.from_address, raw.to_address)
        risk = self.risk.assess(
            amount_usd=amount_usd,
            flow_type=clf.flow_type,
            from_entity_type=clf.from_party.entity_type.value,
            to_entity_type=clf.to_party.entity_type.value,
            threshold_usd=thr,
            asset=raw.asset,
        )
        impact = self.impact.predict(
            amount_usd=amount_usd,
            asset=raw.asset,
            flow_type=clf.flow_type,
            risk_score=risk.score,
            threshold_usd=thr,
        )

        event = WhaleEvent(
            tx_hash=raw.tx_hash,
            log_index=log_index,
            asset=raw.asset.upper(),
            chain=raw.chain,
            amount=raw.amount,
            amount_usd=amount_usd,
            from_address=raw.from_address,
            to_address=raw.to_address,
            from_label=clf.from_party.label,
            to_label=clf.to_party.label,
            from_entity_type=clf.from_party.entity_type.value,
            to_entity_type=clf.to_party.entity_type.value,
            flow_type=clf.flow_type.value,
            risk_score=risk.score,
            risk_level=risk.level.value,
            risk_factors=risk.factors,
            impact_score=impact.score,
            impact_horizon=impact.horizon,
            impact_confidence=impact.confidence,
            impact_details=impact.details,
            provider=raw.provider,
            block_time=raw.block_time,
            raw_ref=raw.raw,
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        metrics.inc("apidesk_whales_detected_total", chain=event.chain, asset=event.asset)
        return event, True

    async def run_once(self, session: AsyncSession) -> list[WhaleEvent]:
        limits = await self.build_limits()
        created: list[WhaleEvent] = []

        # EVM con cursores
        for p in self.router.evm_providers:
            assert isinstance(p, EvmProvider)
            state = await get_or_create_state(session, p.name, p.chain)
            cursor_block = int(state.cursor) if state.cursor and state.cursor.isdigit() else None
            try:
                raws = await p.fetch_recent_transfers(limits, cursor_block=cursor_block)
                tip = getattr(p, "last_tip", None)
                for raw in raws:
                    event, is_new = await self.process_raw(session, raw)
                    if event and is_new:
                        created.append(event)
                if tip is not None:
                    await advance_cursor(session, p.name, p.chain, str(tip), healthy=True)
            except Exception as exc:
                logger.exception("evm ingest %s", p.chain)
                await advance_cursor(session, p.name, p.chain, state.cursor or "0", healthy=False, error=str(exc))
                metrics.inc("apidesk_ingest_errors_total", chain=p.chain)

        # BTC / Tron / Solana (sin cursor de bloque EVM)
        for provider in [
            await self.router._first_healthy(self.router.btc_pool),
            self.router.tron if await self.router.tron.health() else None,
            self.router.solana if await self.router.solana.health() else None,
        ]:
            if not provider:
                continue
            try:
                raws = await provider.fetch_recent_transfers(limits)
                for raw in raws:
                    event, is_new = await self.process_raw(session, raw)
                    if event and is_new:
                        created.append(event)
                await advance_cursor(session, provider.name, provider.chain, "tip", healthy=True)
            except Exception as exc:
                logger.exception("ingest %s", getattr(provider, "name", "?"))
                metrics.inc("apidesk_ingest_errors_total", chain=getattr(provider, "chain", "?"))
                await advance_cursor(
                    session, provider.name, provider.chain, "tip", healthy=False, error=str(exc)
                )

        metrics.inc("apidesk_ingest_cycles_total")
        metrics.set_gauge("apidesk_whales_created_last_cycle", float(len(created)))
        return created
