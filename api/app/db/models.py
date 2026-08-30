from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid4())


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    address: Mapped[str] = mapped_column(String(128), index=True)
    chain: Mapped[str] = mapped_column(String(32), index=True)
    label: Mapped[str] = mapped_column(String(128), default="unknown")
    entity_type: Mapped[str] = mapped_column(String(32), default="unknown")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (UniqueConstraint("chain", "address", name="uq_entity_chain_address"),)


class WhaleEvent(Base):
    __tablename__ = "whale_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tx_hash: Mapped[str] = mapped_column(String(128), index=True)
    log_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    asset: Mapped[str] = mapped_column(String(32), index=True)
    chain: Mapped[str] = mapped_column(String(32), index=True)
    amount: Mapped[float] = mapped_column(Float)
    amount_usd: Mapped[float] = mapped_column(Float, index=True)
    from_address: Mapped[str] = mapped_column(String(128), index=True)
    to_address: Mapped[str] = mapped_column(String(128), index=True)
    from_label: Mapped[str] = mapped_column(String(128), default="unknown")
    to_label: Mapped[str] = mapped_column(String(128), default="unknown")
    from_entity_type: Mapped[str] = mapped_column(String(32), default="unknown")
    to_entity_type: Mapped[str] = mapped_column(String(32), default="unknown")
    flow_type: Mapped[str] = mapped_column(String(64), index=True, default="unknown")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(16), default="low")
    risk_factors: Mapped[list[Any]] = mapped_column(JSON, default=list)
    impact_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    impact_horizon: Mapped[str | None] = mapped_column(String(16), nullable=True)
    impact_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    impact_details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    provider: Mapped[str] = mapped_column(String(64), default="unknown")
    block_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw_ref: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    __table_args__ = (
        UniqueConstraint("chain", "tx_hash", "log_index", name="uq_whale_chain_tx_log"),
        Index("ix_whale_detected_at", "detected_at"),
    )


class ApiClient(Base):
    __tablename__ = "api_clients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(128))
    plan: Mapped[str] = mapped_column(String(32), default="retail")
    api_key_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    api_key_prefix: Mapped[str] = mapped_column(String(16), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    webhook_secret: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alert_rules: Mapped[list["AlertRule"]] = relationship(back_populates="client")


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("api_clients.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    min_usd: Mapped[float] = mapped_column(Float, default=10_000_000)
    assets: Mapped[list[Any]] = mapped_column(JSON, default=list)
    chains: Mapped[list[Any]] = mapped_column(JSON, default=list)
    flow_types: Mapped[list[Any]] = mapped_column(JSON, default=list)
    min_risk_level: Mapped[str] = mapped_column(String(16), default="low")
    channels: Mapped[list[Any]] = mapped_column(JSON, default=list)
    destination: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    # whale | market | both
    alert_kinds: Mapped[list[Any]] = mapped_column(JSON, default=lambda: ["whale"])
    min_market_stress: Mapped[float] = mapped_column(Float, default=0.45)
    signal_assets: Mapped[list[Any]] = mapped_column(JSON, default=list)  # vacío = todos market assets
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client: Mapped[ApiClient] = relationship(back_populates="alert_rules")


class MarketSignalEvent(Base):
    """Señales de microestructura CEX (auxiliar). No son whales on-chain."""

    __tablename__ = "market_signal_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    asset: Mapped[str] = mapped_column(String(16), index=True, default="")
    signal_type: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(16), default="low")
    score: Mapped[float] = mapped_column(Float, default=0.0)
    title: Mapped[str] = mapped_column(String(256), default="")
    stress_score: Mapped[float] = mapped_column(Float, default=0.0)
    spillover_hint: Mapped[float] = mapped_column(Float, default=0.0)
    regime: Mapped[str] = mapped_column(String(32), default="calm")
    source: Mapped[str] = mapped_column(String(64), default="")
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_market_signal_created", "created_at"),)


# Alias de compatibilidad
XmrSignalEvent = MarketSignalEvent


class AlertDelivery(Base):
    __tablename__ = "alert_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    rule_id: Mapped[str] = mapped_column(String(36), ForeignKey("alert_rules.id"), index=True)
    whale_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("whale_events.id"), nullable=True, index=True)
    xmr_signal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("market_signal_events.id"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(32))
    dedup_key: Mapped[str] = mapped_column(String(191), index=True, default="")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    response: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("dedup_key", name="uq_alert_dedup"),)


class ProviderState(Base):
    __tablename__ = "provider_states"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    provider: Mapped[str] = mapped_column(String(64))
    chain: Mapped[str] = mapped_column(String(32))
    cursor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    backfill_cursor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lag_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    healthy: Mapped[bool] = mapped_column(Boolean, default=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (UniqueConstraint("provider", "chain", name="uq_provider_chain"),)


class UsageDaily(Base):
    __tablename__ = "usage_daily"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("api_clients.id"), index=True)
    day: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    request_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (UniqueConstraint("client_id", "day", name="uq_usage_client_day"),)


class Workspace(Base):
    """Workspace Pro: filtros, layout y alertas guardados por cliente."""

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("api_clients.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
