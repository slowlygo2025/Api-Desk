"""Auth por API key + planes retail/pro/institutional."""

from __future__ import annotations

import hashlib
import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.models import ApiClient
from app.db.session import get_db
from app.domain.enums import Plan


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    raw = f"adsk_{secrets.token_urlsafe(32)}"
    return raw, hash_api_key(raw), raw[:12]


async def create_client(
    session: AsyncSession,
    name: str,
    plan: str = Plan.RETAIL.value,
    webhook_url: str | None = None,
) -> tuple[ApiClient, str]:
    raw, hashed, prefix = generate_api_key()
    client = ApiClient(
        name=name,
        plan=plan,
        api_key_hash=hashed,
        api_key_prefix=prefix,
        webhook_url=webhook_url,
        webhook_secret=secrets.token_urlsafe(24),
    )
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client, raw


async def get_client_by_key(session: AsyncSession, api_key: str) -> ApiClient | None:
    result = await session.execute(
        select(ApiClient).where(ApiClient.api_key_hash == hash_api_key(api_key), ApiClient.is_active.is_(True))
    )
    return result.scalar_one_or_none()


def rate_limit_for_plan(settings: Settings, plan: str) -> int:
    return {
        Plan.RETAIL.value: settings.rate_limit_retail,
        Plan.PRO.value: settings.rate_limit_pro,
        Plan.INSTITUTIONAL.value: settings.rate_limit_institutional,
    }.get(plan, settings.rate_limit_retail)


async def require_client(
    x_api_key: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_db),
) -> ApiClient:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-API-Key")
    client = await get_client_by_key(session, x_api_key)
    if not client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return client


async def optional_client(
    request: Request,
    x_api_key: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ApiClient | None:
    if x_api_key:
        return await require_client(x_api_key=x_api_key, session=session)
    if getattr(request.state, "from_rapidapi", False):
        return None
    if not settings.effective_require_api_key:
        return None
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-API-Key")


def require_scope(scope: str):
    """Dependency factory: exige scope del plan del cliente autenticado."""

    async def _dep(client: ApiClient = Depends(require_client)) -> ApiClient:
        from app.services.plans import has_scope

        if not has_scope(client.plan, scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Plan lacks {scope} scope",
            )
        return client

    return _dep
