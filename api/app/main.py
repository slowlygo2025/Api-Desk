from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import get_settings
from app.db.models import Base
from app.db.session import SessionLocal, engine
from app.middleware.rapidapi_proxy import RapidApiProxyMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.entity_sync import sync_exchange_catalog
from app.workers.runtime import worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        n = await sync_exchange_catalog(session)
        logging.getLogger(__name__).info("exchange catalog synced upserts=%s", n)
    await worker.start()
    yield
    await worker.stop()
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description=(
            "API de whales multi-chain (producto principal) + "
            "señales de mercado auxiliares multi-asset (BTC/ETH/SOL/BNB/XMR)."
        ),
        version="2.0.0",
        lifespan=lifespan,
    )
    origins = [o.strip() for o in settings.panel_origins.split(",") if o.strip()]
    if settings.app_env == "development" and not origins:
        origins = ["http://localhost:3000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Orden Starlette: el último add_middleware es el más externo (entra primero).
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RapidApiProxyMiddleware)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
