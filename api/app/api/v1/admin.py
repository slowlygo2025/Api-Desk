from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ApiClient
from app.db.session import get_db
from app.schemas.whales import AdminClientOut
from app.services.auth import require_scope

router = APIRouter(tags=["admin"])


@router.get("/admin/clients", response_model=list[AdminClientOut])
async def list_clients(
    session: AsyncSession = Depends(get_db),
    _client=Depends(require_scope("admin.ops")),
):
    rows = (await session.execute(select(ApiClient).order_by(ApiClient.created_at.desc()))).scalars().all()
    return [
        AdminClientOut(
            id=c.id,
            name=c.name,
            plan=c.plan,
            api_key_prefix=c.api_key_prefix,
            is_active=c.is_active,
            webhook_configured=bool(c.webhook_url),
            created_at=c.created_at,
        )
        for c in rows
    ]
