from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.models import AlertDelivery, AlertRule, ApiClient
from app.db.session import get_db
from app.schemas.whales import (
    AlertDeliveryOut,
    AlertRuleIn,
    AlertRuleOut,
    ClientCreateIn,
    ClientCreateOut,
    ClientMeOut,
    WsTicketOut,
)
from app.services.auth import create_client, require_client, require_scope
from app.services.plans import daily_quota_for_plan, has_scope, rate_limit_for_plan, scopes_for_plan
from app.services.ws_auth import create_ws_ticket

router = APIRouter(tags=["clients-alerts"])


def _rule_out(rule: AlertRule) -> AlertRuleOut:
    return AlertRuleOut(
        id=rule.id,
        client_id=rule.client_id,
        name=rule.name,
        min_usd=rule.min_usd,
        assets=rule.assets or [],
        chains=rule.chains or [],
        flow_types=rule.flow_types or [],
        min_risk_level=rule.min_risk_level,
        channels=rule.channels or [],
        destination=rule.destination or {},
        alert_kinds=rule.alert_kinds or ["whale"],
        min_market_stress=getattr(rule, "min_market_stress", None) or 0.45,
        signal_assets=rule.signal_assets or [],
        is_active=rule.is_active,
    )


@router.post("/clients", response_model=ClientCreateOut)
async def register_client(
    payload: ClientCreateIn,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not settings.effective_allow_client_registration:
        raise HTTPException(status_code=403, detail="Client registration disabled")
    # En production solo el plan público (retail). En development el demo puede pedir pro.
    requested = (payload.plan or settings.public_registration_plan or "retail").lower()
    allowed = (settings.public_registration_plan or "retail").lower()
    if settings.is_production and requested != allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Public registration only allows plan '{allowed}'. Contact sales for upgrades.",
        )
    plan = allowed if settings.is_production else requested
    client, raw_key = await create_client(
        session,
        name=payload.name,
        plan=plan,
        webhook_url=payload.webhook_url,
    )
    return ClientCreateOut(
        id=client.id,
        name=client.name,
        plan=client.plan,
        api_key=raw_key,
        webhook_url=client.webhook_url,
    )


@router.get("/clients/me", response_model=ClientMeOut)
async def get_client_me(
    session: AsyncSession = Depends(get_db),
    client: ApiClient = Depends(require_client),
    settings: Settings = Depends(get_settings),
):
    from app.db.models import UsageDaily

    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    usage = (
        await session.execute(
            select(UsageDaily).where(UsageDaily.client_id == client.id, UsageDaily.day == day)
        )
    ).scalar_one_or_none()
    return ClientMeOut(
        id=client.id,
        name=client.name,
        plan=client.plan,
        api_key_prefix=client.api_key_prefix,
        scopes=sorted(scopes_for_plan(client.plan)),
        rate_limit_per_min=rate_limit_for_plan(settings, client.plan),
        daily_quota=daily_quota_for_plan(settings, client.plan),
        daily_usage=usage.request_count if usage else 0,
        webhook_configured=bool(client.webhook_url),
        created_at=client.created_at,
    )


@router.post("/auth/ws-ticket", response_model=WsTicketOut)
async def issue_ws_ticket(
    client: ApiClient = Depends(require_client),
    settings: Settings = Depends(get_settings),
):
    if not has_scope(client.plan, "ws.feed"):
        raise HTTPException(status_code=403, detail="Plan lacks ws.feed scope")
    ttl = settings.ws_ticket_ttl_sec
    ticket = create_ws_ticket(client.id, client.plan, ttl_sec=ttl, settings=settings)
    return WsTicketOut(ticket=ticket, expires_in=ttl)


@router.post("/alerts/rules", response_model=AlertRuleOut)
async def create_alert_rule(
    payload: AlertRuleIn,
    session: AsyncSession = Depends(get_db),
    client: ApiClient = Depends(require_scope("alerts.manage")),
):
    rule = AlertRule(
        client_id=client.id,
        name=payload.name,
        min_usd=payload.min_usd,
        assets=payload.assets,
        chains=payload.chains,
        flow_types=payload.flow_types,
        min_risk_level=payload.min_risk_level,
        channels=payload.channels,
        destination=payload.destination,
        alert_kinds=payload.alert_kinds,
        min_market_stress=payload.min_market_stress,
        signal_assets=payload.signal_assets,
        is_active=payload.is_active,
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return _rule_out(rule)


@router.get("/alerts/rules", response_model=list[AlertRuleOut])
async def list_alert_rules(
    session: AsyncSession = Depends(get_db),
    client: ApiClient = Depends(require_scope("alerts.manage")),
):
    rows = (
        await session.execute(select(AlertRule).where(AlertRule.client_id == client.id))
    ).scalars().all()
    return [_rule_out(r) for r in rows]


@router.patch("/alerts/rules/{rule_id}", response_model=AlertRuleOut)
async def update_alert_rule(
    rule_id: str,
    payload: AlertRuleIn,
    session: AsyncSession = Depends(get_db),
    client: ApiClient = Depends(require_scope("alerts.manage")),
):
    rule = await session.get(AlertRule, rule_id)
    if not rule or rule.client_id != client.id:
        raise HTTPException(status_code=404, detail="Rule not found")
    for field, value in payload.model_dump().items():
        setattr(rule, field, value)
    await session.commit()
    await session.refresh(rule)
    return _rule_out(rule)


@router.delete("/alerts/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    session: AsyncSession = Depends(get_db),
    client: ApiClient = Depends(require_scope("alerts.manage")),
):
    rule = await session.get(AlertRule, rule_id)
    if not rule or rule.client_id != client.id:
        raise HTTPException(status_code=404, detail="Rule not found")
    await session.delete(rule)
    await session.commit()
    return {"status": "deleted", "id": rule_id}


@router.get("/alerts/deliveries", response_model=list[AlertDeliveryOut])
async def list_alert_deliveries(
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
    client: ApiClient = Depends(require_scope("alerts.manage")),
):
    rule_ids = (
        await session.execute(select(AlertRule.id).where(AlertRule.client_id == client.id))
    ).scalars().all()
    if not rule_ids:
        return []
    rows = (
        await session.execute(
            select(AlertDelivery)
            .where(AlertDelivery.rule_id.in_(rule_ids))
            .order_by(AlertDelivery.created_at.desc())
            .limit(min(limit, 200))
        )
    ).scalars().all()
    rule_map = {r.id: r.name for r in (await session.execute(select(AlertRule).where(AlertRule.id.in_(rule_ids)))).scalars().all()}
    return [
        AlertDeliveryOut(
            id=d.id,
            rule_id=d.rule_id,
            rule_name=rule_map.get(d.rule_id),
            channel=d.channel,
            status=d.status,
            whale_id=d.whale_id,
            market_signal_id=d.xmr_signal_id,
            dedup_key=d.dedup_key or None,
            response=d.response or {},
            created_at=d.created_at,
        )
        for d in rows
    ]


@router.post("/alerts/rules/{rule_id}/test")
async def test_alert_rule(
    rule_id: str,
    session: AsyncSession = Depends(get_db),
    client: ApiClient = Depends(require_scope("alerts.manage")),
):
    rule = await session.get(AlertRule, rule_id)
    if not rule or rule.client_id != client.id:
        raise HTTPException(status_code=404, detail="Rule not found")
    if "webhook" not in (rule.channels or []) and not client.webhook_url:
        raise HTTPException(status_code=400, detail="No webhook configured")
    return {"status": "ok", "message": "Test webhook queued", "rule_id": rule_id}
