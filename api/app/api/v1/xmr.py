"""Compat: /v1/xmr → market signals con asset=XMR (capa auxiliar, no principal)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import market as market_api
from app.config import Settings, get_settings
from app.db.session import get_db
from app.services.auth import optional_client

router = APIRouter(prefix="/xmr", tags=["market-signals-compat"])


@router.get("/exchanges")
async def xmr_exchanges(settings: Settings = Depends(get_settings), _client=Depends(optional_client)):
    assets = await market_api.market_assets(_client=_client)
    xmr = next((a for a in assets["assets"] if a["asset"] == "XMR"), None)
    return {"asset": "XMR", "compat": True, "redirect": "/v1/market/assets", "xmr": xmr}


@router.get("/snapshot")
async def xmr_snapshot(
    settings: Settings = Depends(get_settings),
    _client=Depends(optional_client),
):
    return await market_api.market_snapshot(asset="XMR", settings=settings, _client=_client)


@router.get("/analysis")
async def xmr_analysis(
    persist: bool = Query(default=True),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _client=Depends(optional_client),
):
    return await market_api.market_analysis(
        asset="XMR", persist=persist, session=session, settings=settings, _client=_client
    )


@router.get("/signals")
async def xmr_signals(
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    _client=Depends(optional_client),
):
    return await market_api.market_signals_history(asset="XMR", limit=limit, session=session, _client=_client)
