"""Rate limit + daily quota + require key en production."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings
from app.db.models import UsageDaily
from app.db.session import SessionLocal
from app.domain.enums import Plan
from app.services.auth import get_client_by_key
from app.services.metrics import metrics
from app.services.plans import daily_quota_for_plan, rate_limit_for_plan


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _allow(self, key: str, limit: int, window: float = 60.0) -> tuple[bool, int, int]:
        now = time.time()
        q = self._hits[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            retry = int(window - (now - q[0])) + 1
            return False, 0, retry
        q.append(now)
        return True, limit - len(q), 0

    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        path = request.url.path

        if request.method == "OPTIONS" or path.endswith("/health") or path.endswith("/metrics") or "/ws/" in path:
            return await call_next(request)

        api_key = request.headers.get("x-api-key")
        plan = Plan.RETAIL.value
        client_id: str | None = None
        identity = f"ip:{request.client.host if request.client else 'unknown'}"

        require_key = settings.effective_require_api_key
        registration_open = settings.effective_allow_client_registration
        is_public_register = path.rstrip("/").endswith("/clients") and request.method == "POST"

        if require_key and not api_key:
            if not (is_public_register and registration_open):
                return JSONResponse(status_code=401, content={"detail": "Missing X-API-Key"})
        elif is_public_register and not registration_open:
            return JSONResponse(status_code=403, content={"detail": "Client registration disabled"})

        if api_key:
            async with SessionLocal() as session:
                client = await get_client_by_key(session, api_key)
                if not client:
                    return JSONResponse(status_code=401, content={"detail": "Invalid API key"})
                plan = client.plan
                client_id = client.id
                identity = f"client:{client.id}"

                # daily quota
                day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                usage = (
                    await session.execute(
                        select(UsageDaily).where(UsageDaily.client_id == client.id, UsageDaily.day == day)
                    )
                ).scalar_one_or_none()
                quota = daily_quota_for_plan(settings, plan)
                used = usage.request_count if usage else 0
                if used >= quota:
                    metrics.inc("apidesk_quota_exceeded_total", plan=plan)
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Daily quota exceeded", "plan": plan, "quota": quota},
                    )
                if usage:
                    usage.request_count += 1
                else:
                    session.add(UsageDaily(client_id=client.id, day=day, request_count=1))
                await session.commit()
                request.state.api_client_id = client_id
                request.state.api_plan = plan

        elif settings.app_env == "development":
            plan = Plan.PRO.value
            identity = "dev:anonymous"
        elif require_key:
            return JSONResponse(status_code=401, content={"detail": "Missing X-API-Key"})

        limit = rate_limit_for_plan(settings, plan)
        ok, remaining, retry = self._allow(identity, limit)
        if not ok:
            metrics.inc("apidesk_rate_limited_total", plan=plan)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded", "plan": plan, "limit_per_min": limit},
                headers={"Retry-After": str(retry), "X-RateLimit-Limit": str(limit), "X-RateLimit-Remaining": "0"},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Plan"] = plan
        return response
