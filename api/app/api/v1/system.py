from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.data.exchange_catalog import catalog_stats
from app.db.session import get_db
from app.providers.chains import coverage_manifest
from app.providers.router import ProviderRouter
from app.realtime.hub import ws_manager
from app.schemas.whales import ChainCoverageOut, HealthOut, ReadyOut
from app.services.auth import optional_client
from app.services.cursors import list_provider_states
from app.services.metrics import metrics
from app.services.plans import PLAN_SCOPES, has_scope
from app.services.queue import job_queue
from app.services.ws_auth import verify_ws_ticket
from app.workers.runtime import worker

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthOut)
async def health(settings: Settings = Depends(get_settings)):
    return HealthOut(status="ok", app=settings.app_name, env=settings.app_env)


@router.get("/ready", response_model=ReadyOut)
async def ready(
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    db_ok = True
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    router_p = ProviderRouter(settings)
    healthy = await router_p.healthy_providers()
    status = "ready" if db_ok and len(healthy) > 0 else "degraded"
    return ReadyOut(
        status=status,
        database=db_ok,
        providers_healthy=len(healthy),
        providers_total=len(router_p.providers),
    )


@router.get("/chains", response_model=ChainCoverageOut)
async def list_chains():
    items = coverage_manifest()
    return ChainCoverageOut(chains=items, total=len(items))


@router.get("/worker")
async def worker_status(_client=Depends(optional_client)):
    return worker.status()


@router.get("/entities/catalog/stats")
async def entities_catalog_stats(_client=Depends(optional_client)):
    return catalog_stats()


@router.get("/metrics")
async def prometheus_metrics():
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(metrics.render_prometheus(), media_type="text/plain; version=0.0.4")


@router.get("/ops/status")
async def ops_status(session: AsyncSession = Depends(get_db), _client=Depends(optional_client)):
    states = await list_provider_states(session)
    q = await job_queue.size()
    return {
        "worker": worker.status(),
        "queue": q,
        "plans_scopes": {k: sorted(v) for k, v in PLAN_SCOPES.items()},
        "providers": [
            {
                "provider": s.provider,
                "chain": s.chain,
                "cursor": s.cursor,
                "healthy": s.healthy,
                "lag_seconds": s.lag_seconds,
                "last_error": s.last_error,
                "last_success_at": s.last_success_at.isoformat() if s.last_success_at else None,
            }
            for s in states
        ],
    }


@router.websocket("/ws/feed")
@router.websocket("/ws/whales")
async def live_feed(websocket: WebSocket, ticket: str | None = Query(default=None)):
    settings = get_settings()
    require_ticket = settings.require_api_key or settings.app_env == "production"
    if require_ticket:
        if not ticket:
            await websocket.close(code=4401, reason="Missing ticket")
            return
        payload = verify_ws_ticket(ticket, settings)
        if not payload or not has_scope(payload.get("plan", ""), "ws.feed"):
            await websocket.close(code=4401, reason="Invalid ticket")
            return
    await ws_manager.connect(websocket)
    try:
        await websocket.send_json({"event": "connected", "channel": "feed"})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
