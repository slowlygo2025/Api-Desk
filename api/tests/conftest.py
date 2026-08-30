"""Fixtures compartidas para tests HTTP."""

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    from app.db import session as db_session

    original_engine = db_session.engine
    original_session_local = db_session.SessionLocal
    db_session.engine = engine
    db_session.SessionLocal = SessionLocal

    from app.middleware import rate_limit as rl_mod

    original_rl_session = rl_mod.SessionLocal
    rl_mod.SessionLocal = SessionLocal

    yield

    db_session.engine = original_engine
    db_session.SessionLocal = original_session_local
    rl_mod.SessionLocal = original_rl_session
    await engine.dispose()
