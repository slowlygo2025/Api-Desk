from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass
class RawTransfer:
    tx_hash: str
    chain: str
    asset: str
    amount: float
    from_address: str
    to_address: str
    block_time: datetime | None = None
    log_index: int | None = 0
    provider: str = "unknown"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class FetchLimits:
    """Umbrales en unidades nativas (desde USD vía PriceService)."""

    min_btc: float
    min_eth: float
    min_stable: float
    min_bnb: float = 0.0
    min_avax: float = 0.0
    min_pol: float = 0.0
    min_sol: float = 0.0


class NodeProvider(Protocol):
    name: str
    chain: str

    async def health(self) -> bool: ...

    async def fetch_recent_transfers(self, limits: FetchLimits) -> list[RawTransfer]: ...

    async def get_transfer(self, tx_hash: str) -> RawTransfer | None: ...
