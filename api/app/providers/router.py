"""Router multi-chain: EVM (todas) + BTC + Tron + Solana. Sin mocks."""

from __future__ import annotations

import asyncio
import logging

from app.config import Settings
from app.providers.base import FetchLimits, NodeProvider, RawTransfer
from app.providers.bitcoin import BitcoinProvider
from app.providers.chains import EVM_CHAINS
from app.providers.evm import EvmProvider
from app.providers.solana import SolanaProvider
from app.providers.tron import TronProvider

logger = logging.getLogger(__name__)


class ProviderRouter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.evm_providers = [EvmProvider(settings, cfg) for cfg in EVM_CHAINS.values()]
        self.btc_pool: list[NodeProvider] = [
            BitcoinProvider(settings, "mempool"),
            BitcoinProvider(settings, "blockstream"),
        ]
        self.tron = TronProvider(settings)
        self.solana = SolanaProvider(settings)

    @property
    def providers(self) -> list[NodeProvider]:
        return [*self.evm_providers, *self.btc_pool, self.tron, self.solana]

    async def _first_healthy(self, pool: list[NodeProvider]) -> NodeProvider | None:
        for p in pool:
            try:
                if await p.health():
                    return p
            except Exception:
                continue
        return None

    async def healthy_providers(self) -> list[NodeProvider]:
        healthy: list[NodeProvider] = []
        for p in self.evm_providers:
            try:
                if await p.health():
                    healthy.append(p)
            except Exception:
                continue
        btc = await self._first_healthy(self.btc_pool)
        if btc:
            healthy.append(btc)
        if await self.tron.health():
            healthy.append(self.tron)
        if await self.solana.health():
            healthy.append(self.solana)
        return healthy

    async def fetch_all(self, limits: FetchLimits) -> list[RawTransfer]:
        out: list[RawTransfer] = []
        seen: set[tuple[str, str, int | None]] = set()
        lock = asyncio.Lock()

        async def collect(provider: NodeProvider | None) -> None:
            if not provider:
                return
            try:
                transfers = await provider.fetch_recent_transfers(limits)
                logger.info("%s returned %s transfers", provider.name, len(transfers))
                async with lock:
                    for t in transfers:
                        key = (t.chain, t.tx_hash, t.log_index)
                        if key in seen:
                            continue
                        seen.add(key)
                        out.append(t)
            except Exception:
                logger.exception("Provider %s failed", getattr(provider, "name", provider))

        # EVM en paralelo (cada chain un provider)
        evm_tasks = [collect(p) for p in self.evm_providers]
        other = [
            collect(await self._first_healthy(self.btc_pool)),
            collect(self.tron if await self.tron.health() else None),
            collect(self.solana if await self.solana.health() else None),
        ]
        await asyncio.gather(*evm_tasks, *other)
        return out
