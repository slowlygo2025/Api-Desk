"""Cobertura multi-chain: registro de redes y assets whale-relevant."""

from __future__ import annotations

from dataclasses import dataclass

from app.providers.constants import TRANSFER_TOPIC


@dataclass(frozen=True)
class EvmToken:
    address: str
    asset: str
    decimals: int = 6


@dataclass(frozen=True)
class EvmChainConfig:
    chain: str
    native_asset: str
    rpcs: tuple[str, ...]
    tokens: tuple[EvmToken, ...]
    scan_native: bool = True
    erc20_lookback: int = 12
    native_lookback: int = 3


# --- EVM chains (mismo topic Transfer en todas) ---

EVM_CHAINS: dict[str, EvmChainConfig] = {
    "ethereum": EvmChainConfig(
        chain="ethereum",
        native_asset="ETH",
        rpcs=(
            "https://ethereum.publicnode.com",
            "https://eth.llamarpc.com",
            "https://rpc.ankr.com/eth",
            "https://1rpc.io/eth",
        ),
        tokens=(
            EvmToken("0xdAC17F958D2ee523a2206206994597C13D831ec7", "USDT", 6),
            EvmToken("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "USDC", 6),
            EvmToken("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", "WBTC", 8),
            EvmToken("0x6B175474E89094C44Da98b954EedeAC495271d0F", "DAI", 18),
            EvmToken("0xc5f0f7b667101F91d381B9ce6F2EeE8C3c79b1d9", "FDUSD", 18),
        ),
        erc20_lookback=48,
        native_lookback=6,
    ),
    "bsc": EvmChainConfig(
        chain="bsc",
        native_asset="BNB",
        rpcs=(
            "https://bsc-dataseed.binance.org",
            "https://bsc.publicnode.com",
            "https://rpc.ankr.com/bsc",
        ),
        tokens=(
            EvmToken("0x55d398326f99059fF775485246999027B3197955", "USDT", 18),
            EvmToken("0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d", "USDC", 18),
        ),
        erc20_lookback=20,
        native_lookback=4,
    ),
    "polygon": EvmChainConfig(
        chain="polygon",
        native_asset="POL",
        rpcs=(
            "https://polygon-bor.publicnode.com",
            "https://polygon-rpc.com",
            "https://rpc.ankr.com/polygon",
        ),
        tokens=(
            EvmToken("0xc2132D05D31c914a87C6611C10748AEb04B58e8F", "USDT", 6),
            EvmToken("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", "USDC", 6),
            EvmToken("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", "USDC", 6),  # bridged
        ),
        scan_native=True,
        native_lookback=2,
    ),
    "arbitrum": EvmChainConfig(
        chain="arbitrum",
        native_asset="ETH",
        rpcs=(
            "https://arbitrum-one.publicnode.com",
            "https://arb1.arbitrum.io/rpc",
            "https://rpc.ankr.com/arbitrum",
        ),
        tokens=(
            EvmToken("0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9", "USDT", 6),
            EvmToken("0xaf88d065e77c8cC2239327C5EDb3A432268e5831", "USDC", 6),
        ),
        native_lookback=3,
    ),
    "optimism": EvmChainConfig(
        chain="optimism",
        native_asset="ETH",
        rpcs=(
            "https://optimism.publicnode.com",
            "https://mainnet.optimism.io",
            "https://rpc.ankr.com/optimism",
        ),
        tokens=(
            EvmToken("0x94b008aA00579c1307B0EF2c499aD98a8ce58e58", "USDT", 6),
            EvmToken("0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85", "USDC", 6),
        ),
        native_lookback=3,
    ),
    "base": EvmChainConfig(
        chain="base",
        native_asset="ETH",
        rpcs=(
            "https://base.publicnode.com",
            "https://mainnet.base.org",
            "https://rpc.ankr.com/base",
        ),
        tokens=(
            EvmToken("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "USDC", 6),
            EvmToken("0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2", "USDT", 6),
        ),
        native_lookback=3,
    ),
    "avalanche": EvmChainConfig(
        chain="avalanche",
        native_asset="AVAX",
        rpcs=(
            "https://avalanche-c-chain.publicnode.com",
            "https://api.avax.network/ext/bc/C/rpc",
            "https://rpc.ankr.com/avalanche",
        ),
        tokens=(
            EvmToken("0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7", "USDT", 6),
            EvmToken("0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E", "USDC", 6),
        ),
        native_lookback=3,
    ),
}


@dataclass(frozen=True)
class NonEvmChainInfo:
    chain: str
    kind: str  # bitcoin | tron | solana
    assets: tuple[str, ...]
    notes: str = ""


NON_EVM_CHAINS: dict[str, NonEvmChainInfo] = {
    "bitcoin": NonEvmChainInfo("bitcoin", "bitcoin", ("BTC",), "UTXO outputs grandes"),
    "tron": NonEvmChainInfo("tron", "tron", ("USDT",), "TRC-20 USDT via TronGrid"),
    "solana": NonEvmChainInfo("solana", "solana", ("SOL", "USDT", "USDC"), "native + SPL"),
    "xmr_market": NonEvmChainInfo(
        "market_signals",
        "cex_microstructure",
        ("BTC", "ETH", "SOL", "BNB", "XMR"),
        "Capa auxiliar: señales CEX multi-asset (XMR solo uno más)",
    ),
}


def coverage_manifest() -> list[dict]:
    items: list[dict] = []
    for cfg in EVM_CHAINS.values():
        items.append(
            {
                "chain": cfg.chain,
                "kind": "evm",
                "native_asset": cfg.native_asset,
                "tokens": [t.asset for t in cfg.tokens],
                "scan_native": cfg.scan_native,
                "transfer_topic": TRANSFER_TOPIC,
                "rpc_count": len(cfg.rpcs),
            }
        )
    for info in NON_EVM_CHAINS.values():
        items.append(
            {
                "chain": info.chain,
                "kind": info.kind,
                "native_asset": info.assets[0],
                "tokens": list(info.assets),
                "scan_native": True,
                "notes": info.notes,
            }
        )
    return items


SUPPORTED_CHAIN_IDS: tuple[str, ...] = tuple(
    list(EVM_CHAINS.keys()) + list(NON_EVM_CHAINS.keys())
)
