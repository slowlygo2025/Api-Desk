"""Clasificación con catálogo real de exchanges + bridges."""

from __future__ import annotations

from dataclasses import dataclass

from app.data.exchange_catalog import lookup_entity
from app.domain.enums import EntityType, FlowType


@dataclass
class Party:
    address: str
    label: str
    entity_type: EntityType
    confidence: float


@dataclass
class Classification:
    from_party: Party
    to_party: Party
    flow_type: FlowType


class ClassificationService:
    def resolve(self, chain: str, address: str) -> Party:
        hit = lookup_entity(chain, address)
        if hit:
            label, et, conf = hit
            return Party(address=address, label=label, entity_type=et, confidence=conf)
        return Party(address, "unknown", EntityType.UNKNOWN, 0.2)

    def classify(self, chain: str, asset: str, from_addr: str, to_addr: str) -> Classification:
        src = self.resolve(chain, from_addr)
        dst = self.resolve(chain, to_addr)

        if asset.upper() in {"USDT", "USDC"}:
            if src.entity_type == EntityType.CONTRACT and "treasury" in src.label:
                return Classification(src, dst, FlowType.MINT)
            if dst.entity_type == EntityType.CONTRACT and "treasury" in dst.label:
                return Classification(src, dst, FlowType.BURN)

        if src.entity_type == EntityType.OTC_DESK or dst.entity_type == EntityType.OTC_DESK:
            return Classification(src, dst, FlowType.OTC)

        if src.entity_type == EntityType.BRIDGE or dst.entity_type == EntityType.BRIDGE:
            return Classification(src, dst, FlowType.BRIDGE)

        if src.entity_type != EntityType.EXCHANGE and dst.entity_type == EntityType.EXCHANGE:
            return Classification(src, dst, FlowType.EXCHANGE_INFLOW)

        if src.entity_type == EntityType.EXCHANGE and dst.entity_type != EntityType.EXCHANGE:
            return Classification(src, dst, FlowType.EXCHANGE_OUTFLOW)

        if src.entity_type == EntityType.UNKNOWN and dst.entity_type == EntityType.UNKNOWN:
            return Classification(src, dst, FlowType.WALLET_TO_WALLET)

        return Classification(src, dst, FlowType.UNKNOWN)
