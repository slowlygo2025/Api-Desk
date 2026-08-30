from app.domain.enums import EntityType, FlowType
from app.services.classification import ClassificationService
from app.services.impact import ImpactService
from app.services.risk import RiskService


def test_classify_real_binance_inflow():
    svc = ClassificationService()
    result = svc.classify(
        "ethereum",
        "USDT",
        "0x1111111111111111111111111111111111111111",
        "0x71660c4005BA85c37ccec55d0C4493E66Fe775d3",
    )
    assert result.to_party.label == "coinbase"
    assert result.to_party.entity_type == EntityType.EXCHANGE
    assert result.flow_type == FlowType.EXCHANGE_INFLOW


def test_classify_bridge():
    svc = ClassificationService()
    result = svc.classify(
        "ethereum",
        "ETH",
        "0x2222222222222222222222222222222222222222",
        "0x40ec5B33f54e0E8A33A975908C5BA1c14e5BbbD7",
    )
    assert result.flow_type == FlowType.BRIDGE


def test_risk_and_impact():
    risk = RiskService().assess(
        amount_usd=80_000_000,
        flow_type=FlowType.EXCHANGE_OUTFLOW,
        from_entity_type="exchange",
        to_entity_type="unknown",
        threshold_usd=10_000_000,
    )
    assert risk.score >= 0.4
    impact = ImpactService().predict(
        amount_usd=25_000_000,
        asset="BTC",
        flow_type=FlowType.EXCHANGE_INFLOW,
        risk_score=0.6,
        threshold_usd=10_000_000,
    )
    assert impact.details["model"] == "calibrated_v2"
