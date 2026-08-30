from fastapi import APIRouter

from app.api.v1 import admin, clients, market, system, whales, workspaces, xmr

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(whales.router)
api_router.include_router(clients.router)
api_router.include_router(market.router)
api_router.include_router(workspaces.router)
api_router.include_router(admin.router)
api_router.include_router(xmr.router)
