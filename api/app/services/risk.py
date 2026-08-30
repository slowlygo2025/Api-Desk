"""Risk calibrado por asset/liquidez + tamaño relativo."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import FlowType, RiskLevel


@dataclass
class RiskResult:
    score: float
    level: RiskLevel
    factors: list[str]


# Liquidez proxy 0..1 (mayor = más absorción, menos riesgo de impacto extremo)
ASSET_LIQ = {
    "BTC": 0.92,
    "ETH": 0.88,
    "USDT": 0.95,
    "USDC": 0.94,
    "BNB": 0.75,
    "SOL": 0.78,
    "AVAX": 0.55,
    "POL": 0.5,
    "WBTC": 0.7,
    "FDUSD": 0.6,
    "DAI": 0.65,
}


class RiskService:
    def assess(
        self,
        amount_usd: float,
        flow_type: FlowType,
        from_entity_type: str,
        to_entity_type: str,
        threshold_usd: float,
        asset: str = "USDT",
    ) -> RiskResult:
        liq = ASSET_LIQ.get(asset.upper(), 0.5)
        # En assets ilíquidos el mismo $ duele más
        illiq_boost = 1.0 + (1.0 - liq) * 0.45
        score = 0.0
        factors: list[str] = []

        rel = amount_usd / max(threshold_usd, 1.0)
        if rel >= 5:
            score += 0.38 * illiq_boost
            factors.append("size_gte_5x_threshold")
        elif rel >= 2:
            score += 0.28 * illiq_boost
            factors.append("size_gte_2x_threshold")
        elif rel >= 1:
            score += 0.18 * illiq_boost
            factors.append("size_gte_threshold")

        flow_w = {
            FlowType.EXCHANGE_OUTFLOW: 0.22,
            FlowType.EXCHANGE_INFLOW: 0.2,
            FlowType.OTC: 0.14,
            FlowType.MINT: 0.18,
            FlowType.BURN: 0.16,
            FlowType.BRIDGE: 0.1,
            FlowType.WALLET_TO_WALLET: 0.08,
            FlowType.UNKNOWN: 0.12,
        }
        score += flow_w.get(flow_type, 0.1)
        factors.append(f"flow:{flow_type.value}")

        if from_entity_type == "mixer" or to_entity_type == "mixer":
            score += 0.28
            factors.append("mixer_involved")
        if from_entity_type == "unknown" and to_entity_type == "unknown":
            score += 0.08
            factors.append("unknown_counterparties")
        if from_entity_type == "exchange" or to_entity_type == "exchange":
            factors.append("exchange_touch")

        score = min(1.0, round(score, 4))
        if score >= 0.72:
            level = RiskLevel.HIGH
        elif score >= 0.42:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        return RiskResult(score=score, level=level, factors=factors)
