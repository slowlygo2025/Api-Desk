"""Compat: helpers + Ethereum como EvmProvider del registry."""

from app.config import Settings
from app.providers.chains import EVM_CHAINS
from app.providers.evm import EvmProvider, _hex_to_int, _topic_to_address

__all__ = ["EthereumProvider", "_hex_to_int", "_topic_to_address"]


def EthereumProvider(settings: Settings, backend: str = "public") -> EvmProvider:  # noqa: N802
    return EvmProvider(settings, EVM_CHAINS["ethereum"])
