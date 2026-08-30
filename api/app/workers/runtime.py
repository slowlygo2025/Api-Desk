"""Worker: whales (principal) + market signals multi-asset (auxiliar)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.config import Settings, get_settings
from app.db.models import MarketSignalEvent
from app.db.session import SessionLocal
from app.providers.market.registry import MARKET_ASSETS
from app.realtime.hub import ws_manager
from app.services.alerts import AlertService
from app.services.cursors import compute_ingest_lag_seconds, list_provider_states
from app.services.entity_sync import sync_exchange_catalog
from app.services.ingest import IngestService
from app.services.market_signals import MarketSignalEngine
from app.services.metrics import metrics
from app.services.queue import job_queue
from app.services.serializers import whale_to_out

logger = logging.getLogger(__name__)


class ContinuousWorker:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self.last_whale_at: datetime | None = None
        self.last_market_at: datetime | None = None
        self.last_catalog_at: datetime | None = None
        self.cycles = 0
        self.last_error: str | None = None
        self.last_lag_seconds: float | None = None

        job_queue.register("ingest_whales", self._job_whales)
        job_queue.register("analyze_market", self._job_market)

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def status(self) -> dict:
        return {
            "enabled": self.settings.worker_enabled,
            "running": self.running,
            "cycles": self.cycles,
            "last_whale_at": self.last_whale_at.isoformat() if self.last_whale_at else None,
            "last_market_at": self.last_market_at.isoformat() if self.last_market_at else None,
            "last_catalog_at": self.last_catalog_at.isoformat() if self.last_catalog_at else None,
            "last_lag_seconds": self.last_lag_seconds,
            "last_error": self.last_error,
            "market_assets": list(MARKET_ASSETS.keys()),
            "whale_interval_sec": self.settings.worker_whale_interval_sec,
            "market_interval_sec": self.settings.worker_market_interval_sec,
        }

    async def start(self) -> None:
        if not self.settings.worker_enabled:
            logger.info("worker disabled by config")
            return
        if self.running:
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._loop(), name="apidesk-worker")
        logger.info("worker started (whales primary + market signals auxiliary)")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=20)
            except Exception:
                self._task.cancel()
            self._task = None

    async def _loop(self) -> None:
        whale_every = max(15.0, float(self.settings.worker_whale_interval_sec))
        market_every = max(20.0, float(self.settings.worker_market_interval_sec))
        catalog_every = max(300.0, float(self.settings.worker_catalog_interval_sec))
        next_whale = next_market = next_catalog = 0.0

        while not self._stop.is_set():
            now = asyncio.get_event_loop().time()
            try:
                if now >= next_whale:
                    await job_queue.enqueue("ingest_whales")
                    next_whale = now + whale_every
                if now >= next_market:
                    await job_queue.enqueue("analyze_market")
                    next_market = now + market_every
                if now >= next_catalog:
                    await self._cycle_catalog()
                    next_catalog = now + catalog_every

                for _ in range(5):
                    if not await job_queue.process_once():
                        break

                self.cycles += 1
                qsize = await job_queue.size()
                metrics.set_gauge("apidesk_queue_pending", float(qsize["pending"]))
                await ws_manager.broadcast(
                    {
                        "event": "worker.heartbeat",
                        "cycles": self.cycles,
                        "lag_seconds": self.last_lag_seconds,
                        "queue": qsize,
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }
                )
            except Exception as exc:
                self.last_error = str(exc)
                logger.exception("worker cycle error")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                pass

    async def _job_whales(self, _job) -> None:
        await self._cycle_whales()

    async def _job_market(self, _job) -> None:
        await self._cycle_market()

    async def _cycle_whales(self) -> None:
        alerts = AlertService(self.settings)
        async with SessionLocal() as session:
            created = await IngestService(self.settings).run_once(session)
            self.last_whale_at = datetime.now(timezone.utc)
            lag = await compute_ingest_lag_seconds(session)
            self.last_lag_seconds = lag
            if lag is not None and lag > self.settings.worker_lag_alert_sec:
                metrics.inc("apidesk_lag_alerts_total")
                await ws_manager.broadcast(
                    {"event": "ops.lag_alert", "lag_seconds": lag, "threshold": self.settings.worker_lag_alert_sec}
                )
            for whale in created:
                await alerts.evaluate_and_dispatch(session, whale)
                payload = whale_to_out(whale).model_dump(by_alias=True, mode="json")
                await ws_manager.broadcast({"event": "whale.detected", "data": payload})

    async def _cycle_market(self) -> None:
        engine = MarketSignalEngine(self.settings)
        alerts = AlertService(self.settings)
        assets = [a.strip().upper() for a in (self.settings.market_assets or "").split(",") if a.strip()]
        if not assets:
            assets = list(MARKET_ASSETS.keys())

        for asset in assets:
            try:
                analysis = await engine.analyze(asset)
            except Exception as exc:
                logger.warning("market cycle %s skipped: %s", asset, exc)
                continue

            last_signal = None
            async with SessionLocal() as session:
                for s in analysis.signals:
                    row = MarketSignalEvent(
                        asset=analysis.asset,
                        signal_type=s.signal_type,
                        severity=s.severity,
                        score=s.score,
                        title=s.title,
                        stress_score=analysis.stress_score,
                        spillover_hint=analysis.spillover_hint,
                        regime=analysis.regime,
                        source=analysis.source,
                        detail={**s.detail, "scope": s.scope, "cross": analysis.cross_exchange},
                    )
                    session.add(row)
                    last_signal = row
                await session.commit()
                if last_signal:
                    await session.refresh(last_signal)
                await alerts.evaluate_market(
                    session,
                    asset=analysis.asset,
                    stress=analysis.stress_score,
                    spillover=analysis.spillover_hint,
                    regime=analysis.regime,
                    signal=last_signal,
                )

            metrics.set_gauge("apidesk_market_stress", analysis.stress_score, asset=asset)
            await ws_manager.broadcast(
                {
                    "event": "market.analysis",
                    "data": {
                        "asset": analysis.asset,
                        "stress_score": analysis.stress_score,
                        "spillover_hint": analysis.spillover_hint,
                        "regime": analysis.regime,
                        "mid_price": analysis.mid_price,
                        "source": analysis.source,
                        "signals_count": len(analysis.signals),
                    },
                }
            )

        self.last_market_at = datetime.now(timezone.utc)

    async def _cycle_catalog(self) -> None:
        async with SessionLocal() as session:
            n = await sync_exchange_catalog(session)
            self.last_catalog_at = datetime.now(timezone.utc)
            metrics.inc("apidesk_catalog_sync_total")
            states = await list_provider_states(session)
            await ws_manager.broadcast(
                {"event": "ops.catalog_synced", "upserts": n, "providers": len(states)}
            )


worker = ContinuousWorker()
