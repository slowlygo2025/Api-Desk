"""Impact calibrado: liquidez del asset + tipo de flujo + horizonte."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import FlowType
from app.services.risk import ASSET_LIQ


@dataclass
class ImpactResult:
    score: float
    horizon: str
    confidence: float
    details: dict


class ImpactService:
    FLOW_IMPACT = {
        FlowType.EXCHANGE_INFLOW: 0.62,
        FlowType.EXCHANGE_OUTFLOW: 0.48,
        FlowType.OTC: 0.28,
        FlowType.MINT: 0.42,
        FlowType.BURN: 0.38,
        FlowType.BRIDGE: 0.22,
        FlowType.WALLET_TO_WALLET: 0.16,
        FlowType.UNKNOWN: 0.24,
    }

    def predict(
        self,
        amount_usd: float,
        asset: str,
        flow_type: FlowType,
        risk_score: float,
        threshold_usd: float,
    ) -> ImpactResult:
        base = self.FLOW_IMPACT.get(flow_type, 0.2)
        size_factor = min(1.0, amount_usd / (threshold_usd * 8))
        asset_liq = ASSET_LIQ.get(asset.upper(), 0.5)
        # Más líquido → score de impacto de precio algo menor a igualdad de tamaño
        liq_dampen = 0.55 + asset_liq * 0.45
        score = min(1.0, round((base * 0.45 + size_factor * 0.4 + risk_score * 0.15) / liq_dampen, 4))

        if flow_type in {FlowType.EXCHANGE_INFLOW, FlowType.EXCHANGE_OUTFLOW} and size_factor > 0.25:
            horizon = "1h"
            confidence = min(0.88, 0.5 + asset_liq * 0.32)
        elif size_factor > 0.55:
            horizon = "24h"
            confidence = min(0.82, 0.45 + asset_liq * 0.28)
        else:
            horizon = "5m"
            confidence = min(0.72, 0.38 + asset_liq * 0.22)

        direction = "bearish_pressure" if flow_type == FlowType.EXCHANGE_INFLOW else "neutral_bias"
        if flow_type == FlowType.EXCHANGE_OUTFLOW:
            direction = "supply_shock_reduction"

        return ImpactResult(
            score=score,
            horizon=horizon,
            confidence=round(confidence, 4),
            details={
                "model": "calibrated_v2",
                "direction_bias": direction,
                "size_factor": round(size_factor, 4),
                "asset_liquidity_proxy": asset_liq,
                "flow_base": base,
                "liq_dampen": round(liq_dampen, 4),
            },
        )
