"""Provider EVM genérico: cualquier L1/L2 del registry (USDT/USDC + nativo)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import Settings
from app.providers.base import FetchLimits, RawTransfer
from app.providers.chains import EvmChainConfig
from app.providers.constants import TRANSFER_TOPIC


def _topic_to_address(topic: str) -> str:
    return "0x" + topic[-40:]


def _hex_to_int(value: str) -> int:
    return int(value, 16) if value else 0


class EvmProvider:
    def __init__(self, settings: Settings, config: EvmChainConfig, rpc_override: str | None = None) -> None:
        self.settings = settings
        self.config = config
        self.chain = config.chain
        self.name = f"evm_{config.chain}"
        self._rpc_override = rpc_override
        self._token_meta = {t.address.lower(): t for t in config.tokens}

    def rpc_urls(self) -> list[str]:
        if self._rpc_override:
            return [self._rpc_override]
        # Keys Alchemy por red (si existen)
        key = self.settings.alchemy_api_key
        alchemy_hosts = {
            "ethereum": "eth-mainnet",
            "polygon": "polygon-mainnet",
            "arbitrum": "arb-mainnet",
            "optimism": "opt-mainnet",
            "base": "base-mainnet",
            "avalanche": "avax-mainnet",
            "bsc": None,  # Alchemy BSC limitado / variar
        }
        urls: list[str] = []
        host = alchemy_hosts.get(self.config.chain)
        if key and host:
            urls.append(f"https://{host}.g.alchemy.com/v2/{key}")
        urls.extend(self.config.rpcs)
        return urls

    async def _rpc(self, method: str, params: list[Any]) -> Any:
        last_err: Exception | None = None
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        async with httpx.AsyncClient(timeout=30.0) as client:
            for url in self.rpc_urls():
                try:
                    r = await client.post(url, json=payload)
                    data = r.json()
                    if "error" in data:
                        last_err = RuntimeError(str(data["error"]))
                        continue
                    return data.get("result")
                except Exception as exc:
                    last_err = exc
                    continue
        raise RuntimeError(f"{self.name} RPC failed: {last_err}")

    async def health(self) -> bool:
        try:
            tip = await self._rpc("eth_blockNumber", [])
            return tip is not None
        except Exception:
            return False

    def _min_native(self, limits: FetchLimits) -> float:
        asset = self.config.native_asset.upper()
        if asset == "ETH":
            return limits.min_eth
        if asset == "BNB":
            return limits.min_bnb
        if asset == "AVAX":
            return limits.min_avax
        if asset == "POL":
            return limits.min_pol
        return limits.min_eth

    async def fetch_recent_transfers(
        self, limits: FetchLimits, *, cursor_block: int | None = None
    ) -> list[RawTransfer]:
        tip = _hex_to_int(await self._rpc("eth_blockNumber", []))
        self.last_tip = tip
        lookback = self.config.erc20_lookback
        if cursor_block is not None and cursor_block >= 0:
            from_block = cursor_block + 1
            # seguridad: no escanear más de 400 bloques por ciclo
            if tip - from_block > 400:
                from_block = tip - 400
            if from_block > tip:
                return []
        else:
            from_block = max(0, tip - lookback)

        out: list[RawTransfer] = []
        out.extend(await self._fetch_erc20_range(from_block, tip, limits.min_stable))
        if self.config.scan_native:
            native_from = max(from_block, tip - self.config.native_lookback)
            out.extend(await self._fetch_native_range(native_from, tip, self._min_native(limits)))
        return out

    async def _fetch_erc20(self, tip: int, min_stable: float) -> list[RawTransfer]:
        from_block = max(0, tip - self.config.erc20_lookback)
        return await self._fetch_erc20_range(from_block, tip, min_stable)

    async def _fetch_erc20_range(self, from_block: int, tip: int, min_stable: float) -> list[RawTransfer]:
        addresses = [t.address for t in self.config.tokens]
        logs = await self._rpc(
            "eth_getLogs",
            [
                {
                    "fromBlock": hex(from_block),
                    "toBlock": hex(tip),
                    "address": addresses,
                    "topics": [TRANSFER_TOPIC],
                }
            ],
        )
        if not logs:
            return []

        block_ts: dict[int, datetime] = {}
        results: list[RawTransfer] = []
        seen: set[tuple[str, int]] = set()

        for log in logs:
            token = self._token_meta.get((log.get("address") or "").lower())
            if not token:
                continue
            topics = log.get("topics") or []
            if len(topics) < 3:
                continue
            amount = _hex_to_int(log.get("data", "0x0")) / (10 ** token.decimals)
            if token.asset in {"USDT", "USDC", "DAI", "FDUSD"}:
                if amount < min_stable:
                    continue
            elif token.asset == "WBTC":
                # amount en BTC; umbral aprox vía min_stable/$100k
                if amount < (min_stable / 100_000):
                    continue

            tx_hash = log["transactionHash"]
            log_index = _hex_to_int(log.get("logIndex", "0x0"))
            if (tx_hash, log_index) in seen:
                continue
            seen.add((tx_hash, log_index))

            block_num = _hex_to_int(log.get("blockNumber", "0x0"))
            if block_num not in block_ts:
                block = await self._rpc("eth_getBlockByNumber", [hex(block_num), False])
                ts = _hex_to_int((block or {}).get("timestamp", "0x0"))
                block_ts[block_num] = datetime.fromtimestamp(ts, tz=timezone.utc)

            results.append(
                RawTransfer(
                    tx_hash=tx_hash,
                    chain=self.chain,
                    asset=token.asset,
                    amount=amount,
                    from_address=_topic_to_address(topics[1]),
                    to_address=_topic_to_address(topics[2]),
                    block_time=block_ts[block_num],
                    log_index=log_index,
                    provider=self.name,
                    raw={"blockNumber": log.get("blockNumber"), "address": log.get("address")},
                )
            )
        return results

    async def _fetch_native(self, tip: int, min_native: float) -> list[RawTransfer]:
        from_block = max(0, tip - self.config.native_lookback)
        return await self._fetch_native_range(from_block, tip, min_native)

    async def _fetch_native_range(self, from_block: int, tip: int, min_native: float) -> list[RawTransfer]:
        results: list[RawTransfer] = []
        for block_num in range(from_block, tip + 1):
            block = await self._rpc("eth_getBlockByNumber", [hex(block_num), True])
            if not block:
                continue
            ts = _hex_to_int(block.get("timestamp", "0x0"))
            block_time = datetime.fromtimestamp(ts, tz=timezone.utc)
            for tx in block.get("transactions") or []:
                amount = _hex_to_int(tx.get("value", "0x0")) / 1e18
                if amount < min_native:
                    continue
                to_addr = tx.get("to")
                if not to_addr:
                    continue
                results.append(
                    RawTransfer(
                        tx_hash=tx["hash"],
                        chain=self.chain,
                        asset=self.config.native_asset,
                        amount=amount,
                        from_address=tx.get("from", ""),
                        to_address=to_addr,
                        block_time=block_time,
                        log_index=0,
                        provider=self.name,
                        raw={"blockNumber": hex(block_num), "type": "native"},
                    )
                )
        return results

    async def get_transfer(self, tx_hash: str) -> RawTransfer | None:
        receipt = await self._rpc("eth_getTransactionReceipt", [tx_hash])
        if not receipt:
            return None
        best: RawTransfer | None = None
        for log in receipt.get("logs") or []:
            token = self._token_meta.get((log.get("address") or "").lower())
            topics = log.get("topics") or []
            if not token or len(topics) < 3:
                continue
            if topics[0].lower() != TRANSFER_TOPIC.lower():
                continue
            amount = _hex_to_int(log.get("data", "0x0")) / (10 ** token.decimals)
            cand = RawTransfer(
                tx_hash=tx_hash,
                chain=self.chain,
                asset=token.asset,
                amount=amount,
                from_address=_topic_to_address(topics[1]),
                to_address=_topic_to_address(topics[2]),
                log_index=_hex_to_int(log.get("logIndex", "0x0")),
                provider=self.name,
                raw=log,
            )
            if best is None or cand.amount > best.amount:
                best = cand
        return best
