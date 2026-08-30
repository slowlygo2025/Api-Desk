"""Planes, scopes y quotas diarias."""

from __future__ import annotations

from app.config import Settings
from app.domain.enums import Plan

# Scopes por plan (producto avanzado)
PLAN_SCOPES: dict[str, set[str]] = {
    Plan.RETAIL.value: {
        "whales.read",
        "stats.read",
        "chains.read",
        "market.read",
        "ws.feed",
    },
    Plan.PRO.value: {
        "whales.read",
        "whales.history",
        "stats.read",
        "stats.timeseries",
        "chains.read",
        "entities.read",
        "market.read",
        "market.signals",
        "alerts.manage",
        "impact.read",
        "workspaces.manage",
        "ws.feed",
        "backfill.read",
    },
    Plan.INSTITUTIONAL.value: {
        "whales.read",
        "whales.history",
        "stats.read",
        "stats.timeseries",
        "stats.flows",
        "chains.read",
        "entities.read",
        "entities.write",
        "market.read",
        "market.signals",
        "alerts.manage",
        "impact.read",
        "workspaces.manage",
        "ws.feed",
        "backfill.read",
        "backfill.run",
        "metrics.read",
        "admin.ops",
    },
}


def scopes_for_plan(plan: str) -> set[str]:
    return set(PLAN_SCOPES.get(plan, PLAN_SCOPES[Plan.RETAIL.value]))


def has_scope(plan: str, scope: str) -> bool:
    return scope in scopes_for_plan(plan)


def daily_quota_for_plan(settings: Settings, plan: str) -> int:
    return {
        Plan.RETAIL.value: settings.daily_quota_retail,
        Plan.PRO.value: settings.daily_quota_pro,
        Plan.INSTITUTIONAL.value: settings.daily_quota_institutional,
    }.get(plan, settings.daily_quota_retail)


def rate_limit_for_plan(settings: Settings, plan: str) -> int:
    return {
        Plan.RETAIL.value: settings.rate_limit_retail,
        Plan.PRO.value: settings.rate_limit_pro,
        Plan.INSTITUTIONAL.value: settings.rate_limit_institutional,
    }.get(plan, settings.rate_limit_retail)
