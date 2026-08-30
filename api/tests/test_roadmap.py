"""Tests for stats timeseries and workspaces."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_timeseries_requires_pro():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post("/v1/clients", json={"name": "retail-ts", "plan": "retail"})
        key = reg.json()["api_key"]
        r = await client.get("/v1/stats/timeseries", headers={"X-API-Key": key})
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_timeseries_pro_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post("/v1/clients", json={"name": "pro-ts", "plan": "pro"})
        key = reg.json()["api_key"]
        r = await client.get("/v1/stats/timeseries?window=24h&bucket=1h", headers={"X-API-Key": key})
        assert r.status_code == 200
        body = r.json()
        assert body["window"] == "24h"
        assert "buckets" in body


@pytest.mark.asyncio
async def test_workspaces_crud():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post("/v1/clients", json={"name": "pro-ws", "plan": "pro"})
        key = reg.json()["api_key"]
        headers = {"X-API-Key": key}
        created = await client.post(
            "/v1/workspaces",
            json={"name": "Mi desk", "config": {"filters": {"minUsd": "10000000"}}, "is_default": True},
            headers=headers,
        )
        assert created.status_code == 200
        ws_id = created.json()["id"]
        listed = await client.get("/v1/workspaces", headers=headers)
        assert len(listed.json()) >= 1
        deleted = await client.delete(f"/v1/workspaces/{ws_id}", headers=headers)
        assert deleted.status_code == 200
