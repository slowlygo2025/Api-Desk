from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Workspace
from app.db.session import get_db
from app.schemas.whales import WorkspaceIn, WorkspaceOut
from app.services.auth import require_scope

router = APIRouter(tags=["workspaces"])


def _workspace_out(ws: Workspace) -> WorkspaceOut:
    return WorkspaceOut(
        id=ws.id,
        client_id=ws.client_id,
        name=ws.name,
        config=ws.config or {},
        is_default=ws.is_default,
        created_at=ws.created_at,
        updated_at=ws.updated_at,
    )


@router.get("/workspaces", response_model=list[WorkspaceOut])
async def list_workspaces(
    session: AsyncSession = Depends(get_db),
    client=Depends(require_scope("workspaces.manage")),
):
    rows = (
        await session.execute(select(Workspace).where(Workspace.client_id == client.id).order_by(Workspace.name))
    ).scalars().all()
    return [_workspace_out(w) for w in rows]


@router.post("/workspaces", response_model=WorkspaceOut)
async def create_workspace(
    payload: WorkspaceIn,
    session: AsyncSession = Depends(get_db),
    client=Depends(require_scope("workspaces.manage")),
):
    if payload.is_default:
        existing = (
            await session.execute(select(Workspace).where(Workspace.client_id == client.id, Workspace.is_default.is_(True)))
        ).scalars().all()
        for w in existing:
            w.is_default = False

    ws = Workspace(
        client_id=client.id,
        name=payload.name,
        config=payload.config,
        is_default=payload.is_default,
    )
    session.add(ws)
    await session.commit()
    await session.refresh(ws)
    return _workspace_out(ws)


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceOut)
async def update_workspace(
    workspace_id: str,
    payload: WorkspaceIn,
    session: AsyncSession = Depends(get_db),
    client=Depends(require_scope("workspaces.manage")),
):
    ws = await session.get(Workspace, workspace_id)
    if not ws or ws.client_id != client.id:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if payload.is_default:
        existing = (
            await session.execute(
                select(Workspace).where(
                    Workspace.client_id == client.id,
                    Workspace.is_default.is_(True),
                    Workspace.id != workspace_id,
                )
            )
        ).scalars().all()
        for w in existing:
            w.is_default = False

    ws.name = payload.name
    ws.config = payload.config
    ws.is_default = payload.is_default
    await session.commit()
    await session.refresh(ws)
    return _workspace_out(ws)


@router.delete("/workspaces/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    session: AsyncSession = Depends(get_db),
    client=Depends(require_scope("workspaces.manage")),
):
    ws = await session.get(Workspace, workspace_id)
    if not ws or ws.client_id != client.id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    await session.delete(ws)
    await session.commit()
    return {"status": "deleted", "id": workspace_id}
