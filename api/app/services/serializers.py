from app.db.models import WhaleEvent
from app.schemas.whales import AddressParty, ImpactInfo, RiskInfo, WhaleEventOut


def whale_to_out(event: WhaleEvent) -> WhaleEventOut:
    return WhaleEventOut(
        id=event.id,
        tx_hash=event.tx_hash,
        asset=event.asset,
        chain=event.chain,
        amount=event.amount,
        amount_usd=event.amount_usd,
        **{
            "from": AddressParty(
                address=event.from_address,
                label=event.from_label,
                entity_type=event.from_entity_type,
            )
        },
        to=AddressParty(
            address=event.to_address,
            label=event.to_label,
            entity_type=event.to_entity_type,
        ),
        flow_type=event.flow_type,
        risk=RiskInfo(score=event.risk_score, level=event.risk_level, factors=event.risk_factors or []),
        impact=ImpactInfo(
            score=event.impact_score,
            horizon=event.impact_horizon,
            confidence=event.impact_confidence,
            details=event.impact_details or {},
        ),
        detected_at=event.detected_at,
        block_time=event.block_time,
        provider=event.provider,
    )
