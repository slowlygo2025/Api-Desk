"""Bitcoin real: outputs grandes en bloques recientes (Mempool.space / Blockstream)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import Settings
from app.providers.base import FetchLimits, RawTransfer
from app.providers.constants import BTC_LOOKBACK_BLOCKS


class BitcoinProvider:
    chain = "bitcoin"

    def __init__(self, settings: Settings, backend: str = "mempool") -> None:
        self.settings = settings
        self.backend = backend
        self.name = f"btc_{backend}"

    def _base(self) -> str:
        if self.backend == "blockstream":
            return self.settings.blockstream_base_url.rstrip("/")
        return self.settings.mempool_base_url.rstrip("/")

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                r = await client.get(f"{self._base()}/blocks/tip/height")
                return r.status_code == 200
        except Exception:
            return False

    async def _get_json(self, client: httpx.AsyncClient, path: str) -> Any:
        r = await client.get(f"{self._base()}{path}")
        r.raise_for_status()
        if "application/json" in r.headers.get("content-type", ""):
            return r.json()
        # tip hash a veces text/plain
        text = r.text.strip()
        try:
            return r.json()
        except Exception:
            return text

    async def fetch_recent_transfers(self, limits: FetchLimits) -> list[RawTransfer]:
        min_sats = int(limits.min_btc * 1e8)
        results: list[RawTransfer] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            tip_hash = await self._get_json(client, "/blocks/tip/hash")
            if isinstance(tip_hash, dict):
                tip_hash = tip_hash.get("hash") or tip_hash.get("id")
            block_hash = str(tip_hash).strip()

            for _ in range(BTC_LOOKBACK_BLOCKS):
                block = await self._get_json(client, f"/block/{block_hash}")
                block_time = datetime.fromtimestamp(int(block.get("timestamp", 0)), tz=timezone.utc)
                # txs del bloque (paginado de 25)
                start = 0
                while True:
                    page = await self._get_json(client, f"/block/{block_hash}/txs/{start}")
                    if not page:
                        break
                    if not isinstance(page, list):
                        break
                    for tx in page:
                        results.extend(self._extract_large_outputs(tx, min_sats, block_time))
                    if len(page) < 25:
                        break
                    start += 25
                    # límite de seguridad por ciclo (rate limits públicos)
                    if start >= 100:
                        break

                prev = block.get("previousblockhash")
                if not prev:
                    break
                block_hash = prev

        return results

    def _extract_large_outputs(
        self, tx: dict[str, Any], min_sats: int, block_time: datetime
    ) -> list[RawTransfer]:
        txid = tx.get("txid") or tx.get("hash")
        if not txid:
            return []

        vins = tx.get("vin") or []
        # dirección de origen aproximada: primer prevout conocido
        from_addr = "unknown"
        for vin in vins:
            prev = vin.get("prevout") or {}
            addr = prev.get("scriptpubkey_address")
            if addr:
                from_addr = addr
                break

        out: list[RawTransfer] = []
        for idx, vout in enumerate(tx.get("vout") or []):
            value = int(vout.get("value") or 0)  # sats
            if value < min_sats:
                continue
            to_addr = vout.get("scriptpubkey_address") or "unknown"
            out.append(
                RawTransfer(
                    tx_hash=txid,
                    chain="bitcoin",
                    asset="BTC",
                    amount=value / 1e8,
                    from_address=from_addr,
                    to_address=to_addr,
                    block_time=block_time,
                    log_index=idx,
                    provider=self.name,
                    raw={"value_sats": value, "vout": idx},
                )
            )
        return out

    async def get_transfer(self, tx_hash: str) -> RawTransfer | None:
        async with httpx.AsyncClient(timeout=20.0) as client:
            tx = await self._get_json(client, f"/tx/{tx_hash}")
        if not isinstance(tx, dict):
            return None
        status = tx.get("status") or {}
        block_time = None
        if status.get("block_time"):
            block_time = datetime.fromtimestamp(int(status["block_time"]), tz=timezone.utc)
        # devolver el output más grande
        best: RawTransfer | None = None
        for item in self._extract_large_outputs(tx, min_sats=0, block_time=block_time or datetime.now(timezone.utc)):
            if best is None or item.amount > best.amount:
                best = item
        return best
