"""Spillover de un asset vs BTC (señales auxiliares)."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

KRAKEN_PAIRS = {
    "BTC": "XBTUSD",
    "ETH": "ETHUSD",
    "SOL": "SOLUSD",
    "XMR": "XMRUSD",
}


@dataclass
class SpilloverResult:
    score: float
    btc_change_pct: float
    asset_change_pct: float
    beta_hint: float
    detail: dict


async def estimate_spillover_vs_btc(asset: str, stress: float, trade_pressure: float) -> SpilloverResult:
    asset = asset.upper()
    btc_chg = 0.0
    asset_chg = 0.0
    pair = KRAKEN_PAIRS.get(asset)
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            btc = await client.get("https://api.kraken.com/0/public/Ticker", params={"pair": "XBTUSD"})
            btc_row = next(iter(btc.json()["result"].values()))
            btc_chg = (float(btc_row["c"][0]) - float(btc_row["o"])) / float(btc_row["o"]) * 100
            if pair and asset != "BTC":
                ax = await client.get("https://api.kraken.com/0/public/Ticker", params={"pair": pair})
                ax_row = next(iter(ax.json()["result"].values()))
                asset_chg = (float(ax_row["c"][0]) - float(ax_row["o"])) / float(ax_row["o"]) * 100
            elif asset == "BTC":
                asset_chg = btc_chg
    except Exception:
        pass

    beta = 1.0
    if asset != "BTC" and abs(btc_chg) > 0.05:
        beta = max(-3.0, min(3.0, asset_chg / btc_chg))
    co_move = min(1.0, abs(asset_chg) / 3.0)
    score = min(1.0, round(stress * 0.55 + trade_pressure * 0.2 + co_move * 0.25, 4))
    return SpilloverResult(
        score=score,
        btc_change_pct=round(btc_chg, 4),
        asset_change_pct=round(asset_chg, 4),
        beta_hint=round(beta, 4),
        detail={"model": "asset_btc_comove_v1", "asset": asset, "co_move": round(co_move, 4)},
    )


# compat
async def estimate_xmr_spillover(xmr_stress: float, trade_pressure: float) -> SpilloverResult:
    return await estimate_spillover_vs_btc("XMR", xmr_stress, trade_pressure)
