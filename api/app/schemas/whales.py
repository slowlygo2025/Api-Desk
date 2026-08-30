from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AddressParty(BaseModel):
    address: str
    label: str = "unknown"
    entity_type: str = "unknown"


class RiskInfo(BaseModel):
    score: float = Field(ge=0, le=1)
    level: str
    factors: list[str] = Field(default_factory=list)


class ImpactInfo(BaseModel):
    score: float | None = None
    horizon: str | None = None
    confidence: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class WhaleEventOut(BaseModel):
    id: str
    tx_hash: str
    asset: str
    chain: str
    amount: float
    amount_usd: float
    from_: AddressParty = Field(alias="from")
    to: AddressParty
    flow_type: str
    risk: RiskInfo
    impact: ImpactInfo
    detected_at: datetime
    block_time: datetime | None = None
    provider: str

    model_config = {"from_attributes": True, "populate_by_name": True}


class WhaleListOut(BaseModel):
    items: list[WhaleEventOut]
    next_cursor: str | None = None
    count: int


class EntityOut(BaseModel):
    address: str
    chain: str
    label: str
    entity_type: str
    confidence: float
    meta: dict[str, Any] = Field(default_factory=dict)


class StatsOverviewOut(BaseModel):
    window: str
    total_events: int
    total_volume_usd: float
    by_asset: dict[str, int]
    by_flow_type: dict[str, int]
    by_chain: dict[str, int]
    high_risk_count: int


class TimeseriesBucket(BaseModel):
    ts: datetime
    events: int
    volume_usd: float
    high_risk: int


class TimeseriesOut(BaseModel):
    window: str
    bucket: str
    buckets: list[TimeseriesBucket]


class SankeyNode(BaseModel):
    id: str
    label: str
    entity_type: str = "unknown"


class SankeyLink(BaseModel):
    source: str
    target: str
    value: float
    count: int


class FlowSankeyOut(BaseModel):
    window: str
    nodes: list[SankeyNode]
    links: list[SankeyLink]


class EntityListOut(BaseModel):
    items: list[EntityOut]
    total: int


class WorkspaceIn(BaseModel):
    name: str
    config: dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False


class WorkspaceOut(WorkspaceIn):
    id: str
    client_id: str
    created_at: datetime
    updated_at: datetime


class AdminClientOut(BaseModel):
    id: str
    name: str
    plan: str
    api_key_prefix: str
    is_active: bool
    webhook_configured: bool
    created_at: datetime


class AlertRuleIn(BaseModel):
    name: str
    min_usd: float = 10_000_000
    assets: list[str] = Field(default_factory=list)
    chains: list[str] = Field(default_factory=list)
    flow_types: list[str] = Field(default_factory=list)
    min_risk_level: str = "low"
    channels: list[str] = Field(default_factory=lambda: ["webhook"])
    destination: dict[str, Any] = Field(default_factory=dict)
    alert_kinds: list[str] = Field(default_factory=lambda: ["whale"])
    min_market_stress: float = 0.45
    signal_assets: list[str] = Field(default_factory=list)
    is_active: bool = True


class AlertRuleOut(AlertRuleIn):
    id: str
    client_id: str


class ClientCreateIn(BaseModel):
    name: str
    plan: str = "retail"
    webhook_url: str | None = None


class ClientCreateOut(BaseModel):
    id: str
    name: str
    plan: str
    api_key: str
    webhook_url: str | None = None


class ClientMeOut(BaseModel):
    id: str
    name: str
    plan: str
    api_key_prefix: str
    scopes: list[str]
    rate_limit_per_min: int
    daily_quota: int
    daily_usage: int
    webhook_configured: bool
    created_at: datetime


class AlertDeliveryOut(BaseModel):
    id: str
    rule_id: str
    rule_name: str | None = None
    channel: str
    status: str
    whale_id: str | None = None
    market_signal_id: str | None = None
    dedup_key: str | None = None
    response: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class WsTicketOut(BaseModel):
    ticket: str
    expires_in: int


class HealthOut(BaseModel):
    status: str
    app: str
    env: str


class ReadyOut(BaseModel):
    status: str
    database: bool
    providers_healthy: int
    providers_total: int


class ChainCoverageOut(BaseModel):
    chains: list[dict[str, Any]]
    total: int
