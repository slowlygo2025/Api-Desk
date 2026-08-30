"""Tests panel/BFF endpoints."""

from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.ws_auth import create_ws_ticket, verify_ws_ticket


@pytest.mark.asyncio
async def test_clients_me_requires_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/v1/clients/me")
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_register_and_me():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post("/v1/clients", json={"name": "panel-test", "plan": "pro"})
        assert reg.status_code == 200
        key = reg.json()["api_key"]
        me = await client.get("/v1/clients/me", headers={"X-API-Key": key})
        assert me.status_code == 200
        body = me.json()
        assert body["plan"] == "pro"
        assert "alerts.manage" in body["scopes"]


@pytest.mark.asyncio
async def test_ws_ticket_roundtrip():
    from app.config import get_settings

    settings = get_settings()
    ticket = create_ws_ticket("client-1", "pro", ttl_sec=15, settings=settings)
    payload = verify_ws_ticket(ticket, settings)
    assert payload is not None
    assert payload["sub"] == "client-1"
    assert payload["plan"] == "pro"
