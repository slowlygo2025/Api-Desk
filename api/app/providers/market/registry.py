"""Registro de assets para señales de mercado (microestructura).

Whales on-chain = producto principal.
Esta capa = análisis auxiliar (trades + book + volumen) para cryptos clave.
XMR es un asset más (opaco on-chain), no el centro del producto.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AssetMarketSpec:
    asset: str
    # pair por venue
    kraken: str | None = None
    kucoin: str | None = None
    mexc: str | None = None
    bitfinex: str | None = None
    htx: str | None = None
    large_trade_usd: float = 50_000
    quote: str = "USD"  # o USDT


# Orden = prioridad de análisis en el worker
MARKET_ASSETS: dict[str, AssetMarketSpec] = {
    "BTC": AssetMarketSpec(
        "BTC",
        kraken="XBTUSD",
        kucoin="BTC-USDT",
        mexc="BTCUSDT",
        bitfinex="tBTCUSD",
        htx="btcusdt",
        large_trade_usd=100_000,
    ),
    "ETH": AssetMarketSpec(
        "ETH",
        kraken="ETHUSD",
        kucoin="ETH-USDT",
        mexc="ETHUSDT",
        bitfinex="tETHUSD",
        htx="ethusdt",
        large_trade_usd=75_000,
    ),
    "SOL": AssetMarketSpec(
        "SOL",
        kraken="SOLUSD",
        kucoin="SOL-USDT",
        mexc="SOLUSDT",
        bitfinex="tSOLUSD",
        htx="solusdt",
        large_trade_usd=40_000,
    ),
    "BNB": AssetMarketSpec(
        "BNB",
        kraken=None,  # Kraken limited
        kucoin="BNB-USDT",
        mexc="BNBUSDT",
        bitfinex=None,
        htx="bnbusdt",
        large_trade_usd=40_000,
    ),
    "XMR": AssetMarketSpec(
        "XMR",
        kraken="XMRUSD",
        kucoin="XMR-USDT",
        mexc="XMRUSDT",
        bitfinex="tXMRUSD",
        htx="xmrusdt",
        large_trade_usd=25_000,
    ),
}


def list_market_assets() -> list[dict]:
    return [
        {
            "asset": spec.asset,
            "large_trade_usd": spec.large_trade_usd,
            "venues": [
                name
                for name, pair in {
                    "kraken": spec.kraken,
                    "kucoin": spec.kucoin,
                    "mexc": spec.mexc,
                    "bitfinex": spec.bitfinex,
                    "htx": spec.htx,
                }.items()
                if pair
            ],
            "role": "opaque_auxiliary" if spec.asset == "XMR" else "liquid_auxiliary",
            "note": (
                "Señales CEX para análisis (no sustituye whales on-chain)."
                if spec.asset != "XMR"
                else "Opaco on-chain; solo microestructura CEX para señales."
            ),
        }
        for spec in MARKET_ASSETS.values()
    ]
