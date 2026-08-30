"""R1 RapidAPI hardening: proxy secret, hub whitelist, ingest scope."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import app


@pytest.fixture(autouse=True)
def _clear_settings_cache(monkeypatch):
    # defaults limpios entre tests
    monkeypatch.delenv("RAPIDAPI_PROXY_SECRET", raising=False)
    monkeypatch.delenv("RAPIDAPI_REQUIRE_PROXY", raising=False)
    monkeypatch.delenv("RAPIDAPI_HUB_ONLY", raising=False)
    monkeypatch.delenv("RAPIDAPI_ENFORCE_IN_PRODUCTION", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_ingest_requires_admin_ops():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post("/v1/clients", json={"name": "pro-ingest", "plan": "pro"})
        assert reg.status_code == 200
        key = reg.json()["api_key"]
        r = await client.post("/v1/whales/ingest/run", headers={"X-API-Key": key})
        assert r.status_code == 403

        inst = await client.post("/v1/clients", json={"name": "inst-ingest", "plan": "institutional"})
        ikey = inst.json()["api_key"]
        with patch("app.api.v1.whales.IngestService.run_once", new_callable=AsyncMock, return_value=[]):
            r2 = await client.post("/v1/whales/ingest/run", headers={"X-API-Key": ikey})
        assert r2.status_code == 200
        assert r2.json()["count"] == 0


@pytest.mark.asyncio
async def test_proxy_secret_rejects_wrong(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_PROXY_SECRET", "test-secret-rapid")
    monkeypatch.setenv("RAPIDAPI_REQUIRE_PROXY", "false")
    monkeypatch.setenv("RAPIDAPI_HUB_ONLY", "true")
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        bad = await client.get(
            "/v1/whales?limit=1",
            headers={"X-RapidAPI-Proxy-Secret": "wrong"},
        )
        assert bad.status_code == 403

        ok = await client.get(
            "/v1/whales?limit=1",
            headers={"X-RapidAPI-Proxy-Secret": "test-secret-rapid"},
        )
        assert ok.status_code == 200


@pytest.mark.asyncio
async def test_hub_whitelist_blocks_admin(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_PROXY_SECRET", "test-secret-rapid")
    monkeypatch.setenv("RAPIDAPI_HUB_ONLY", "true")
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        inst = await client.post("/v1/clients", json={"name": "hub-admin", "plan": "institutional"})
        key = inst.json()["api_key"]
        blocked = await client.get(
            "/v1/admin/clients",
            headers={
                "X-API-Key": key,
                "X-RapidAPI-Proxy-Secret": "test-secret-rapid",
            },
        )
        assert blocked.status_code == 403


@pytest.mark.asyncio
async def test_health_open_with_proxy_required(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_PROXY_SECRET", "test-secret-rapid")
    monkeypatch.setenv("RAPIDAPI_REQUIRE_PROXY", "true")
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/v1/health")
        assert health.status_code == 200
        denied = await client.get("/v1/whales?limit=1")
        assert denied.status_code == 403


@pytest.mark.asyncio
async def test_direct_panel_ok_without_proxy_when_not_required(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_PROXY_SECRET", "test-secret-rapid")
    monkeypatch.setenv("RAPIDAPI_REQUIRE_PROXY", "false")
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # panel: sin header RapidAPI → permitido en modo dual
        r = await client.get("/v1/whales?limit=1")
        assert r.status_code == 200
