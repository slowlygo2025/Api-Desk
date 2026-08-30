"""Tron real: transferencias USDT (TRC-20) vía TronGrid."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import Settings
from app.providers.base import FetchLimits, RawTransfer
from app.providers.constants import TRON_EVENT_LIMIT, USDT_TRON, USDT_TRON_DECIMALS


class TronProvider:
    chain = "tron"
    name = "tron_trongrid"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base = "https://api.trongrid.io"

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.settings.trongrid_api_key:
            headers["TRON-PRO-API-KEY"] = self.settings.trongrid_api_key
        return headers

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                r = await client.get(f"{self.base}/wallet/getnowblock", headers=self._headers())
                return r.status_code == 200
        except Exception:
            return False

    async def fetch_recent_transfers(self, limits: FetchLimits) -> list[RawTransfer]:
        min_raw = int(limits.min_stable * (10**USDT_TRON_DECIMALS))
        url = f"{self.base}/v1/contracts/{USDT_TRON}/events"
        params = {
            "event_name": "Transfer",
            "only_confirmed": "true",
            "limit": TRON_EVENT_LIMIT,
            "order_by": "block_timestamp,desc",
        }
        async with httpx.AsyncClient(timeout=25.0) as client:
            r = await client.get(url, params=params, headers=self._headers())
            r.raise_for_status()
            payload = r.json()

        events = payload.get("data") or []
        results: list[RawTransfer] = []
        for ev in events:
            result = self._parse_event(ev, min_raw)
            if result:
                results.append(result)
        return results

    def _parse_event(self, ev: dict[str, Any], min_raw: int) -> RawTransfer | None:
        result = ev.get("result") or {}
        # formatos TronGrid: from/to/value o from_address...
        raw_amount = result.get("value") or result.get("amount") or result.get("0")
        if raw_amount is None:
            return None
        try:
            amount_raw = int(raw_amount)
        except (TypeError, ValueError):
            return None
        if amount_raw < min_raw:
            return None

        from_addr = result.get("from") or result.get("from_address") or result.get("0") or "unknown"
        to_addr = result.get("to") or result.get("to_address") or result.get("1") or "unknown"
        # a veces vienen hex; TronGrid suele devolver base58 en result
        if isinstance(from_addr, str) and from_addr.startswith("0x"):
            from_addr = from_addr  # se deja; clasificación tolerará unknown
        if isinstance(to_addr, str) and to_addr.startswith("0x"):
            to_addr = to_addr

        ts_ms = ev.get("block_timestamp") or 0
        block_time = datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc) if ts_ms else None
        tx_hash = ev.get("transaction_id") or ev.get("transaction") or ""
        event_idx = ev.get("event_index", 0)

        return RawTransfer(
            tx_hash=tx_hash,
            chain="tron",
            asset="USDT",
            amount=amount_raw / (10**USDT_TRON_DECIMALS),
            from_address=str(from_addr),
            to_address=str(to_addr),
            block_time=block_time,
            log_index=int(event_idx) if event_idx is not None else 0,
            provider=self.name,
            raw={"block_number": ev.get("block_number"), "event": "Transfer"},
        )

    async def get_transfer(self, tx_hash: str) -> RawTransfer | None:
        url = f"{self.base}/v1/transactions/{tx_hash}/events"
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, headers=self._headers())
            if r.status_code != 200:
                return None
            data = r.json().get("data") or []
        best: RawTransfer | None = None
        for ev in data:
            if ev.get("event_name") != "Transfer":
                continue
            parsed = self._parse_event(ev, min_raw=0)
            if parsed and (best is None or parsed.amount > best.amount):
                best = parsed
        return best
