export interface AddressParty {
  address: string;
  label: string;
  entity_type: string;
}

export interface RiskInfo {
  score: number;
  level: string;
  factors: string[];
}

export interface ImpactInfo {
  score: number | null;
  horizon: string | null;
  confidence: number | null;
  details: Record<string, unknown>;
}

export interface WhaleEvent {
  id: string;
  tx_hash: string;
  asset: string;
  chain: string;
  amount: number;
  amount_usd: number;
  from: AddressParty;
  to: AddressParty;
  flow_type: string;
  risk: RiskInfo;
  impact: ImpactInfo;
  detected_at: string;
  block_time: string | null;
  provider: string;
}

export interface WhaleList {
  items: WhaleEvent[];
  next_cursor: string | null;
  count: number;
}

export interface StatsOverview {
  window: string;
  total_events: number;
  total_volume_usd: number;
  by_asset: Record<string, number>;
  by_flow_type: Record<string, number>;
  by_chain: Record<string, number>;
  high_risk_count: number;
}

export interface ClientMe {
  id: string;
  name: string;
  plan: string;
  api_key_prefix: string;
  scopes: string[];
  rate_limit_per_min: number;
  daily_quota: number;
  daily_usage: number;
  webhook_configured: boolean;
  created_at: string;
}

export interface AlertRule {
  id: string;
  client_id: string;
  name: string;
  min_usd: number;
  assets: string[];
  chains: string[];
  flow_types: string[];
  min_risk_level: string;
  channels: string[];
  destination: Record<string, unknown>;
  alert_kinds: string[];
  min_market_stress: number;
  signal_assets: string[];
  is_active: boolean;
}

export interface AlertDelivery {
  id: string;
  rule_id: string;
  rule_name?: string | null;
  channel: string;
  status: string;
  whale_id: string | null;
  market_signal_id: string | null;
  dedup_key?: string | null;
  response?: Record<string, unknown>;
  created_at: string;
}

export interface MarketVenueStatus {
  exchange: string;
  pair: string;
  ok: boolean;
  error?: string | null;
  trades: number;
  latency_ms: number;
  mid?: number | null;
}

export interface MarketSnapshot {
  kind: string;
  asset: string;
  fetched_at: string;
  venues_ok: number;
  venues_total: number;
  venues: MarketVenueStatus[];
  meta: Record<string, unknown>;
}

export interface MarketAnalysis {
  kind: string;
  asset: string;
  stress_score: number;
  spillover_hint: number;
  regime: string;
  mid_price: number | null;
  source: string;
  signals: MarketSignal[];
  fetched_at: string;
}

export interface MarketSignal {
  signal_type: string;
  severity: string;
  score: number;
  title: string;
  scope: string;
  detail: Record<string, unknown>;
  ts: string;
}

export interface ReadyStatus {
  status: string;
  database: boolean;
  providers_healthy: number;
  providers_total: number;
}

export interface WorkerStatus {
  running: boolean;
  cycles?: number;
  lag_seconds?: number;
}

export interface WsTicket {
  ticket: string;
  expires_in: number;
}

export interface TimeseriesBucket {
  ts: string;
  events: number;
  volume_usd: number;
  high_risk: number;
}

export interface Timeseries {
  window: string;
  bucket: string;
  buckets: TimeseriesBucket[];
}

export interface SankeyNode {
  id: string;
  label: string;
  entity_type: string;
}

export interface SankeyLink {
  source: string;
  target: string;
  value: number;
  count: number;
}

export interface FlowSankey {
  window: string;
  nodes: SankeyNode[];
  links: SankeyLink[];
}

export interface EntityRecord {
  address: string;
  chain: string;
  label: string;
  entity_type: string;
  confidence: number;
  meta: Record<string, unknown>;
}

export interface EntityList {
  items: EntityRecord[];
  total: number;
}

export interface Workspace {
  id: string;
  client_id: string;
  name: string;
  config: Record<string, unknown>;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminClient {
  id: string;
  name: string;
  plan: string;
  api_key_prefix: string;
  is_active: boolean;
  webhook_configured: boolean;
  created_at: string;
}

export interface OpsStatus {
  worker: WorkerStatus;
  queue: number;
  plans_scopes: Record<string, string[]>;
  providers: {
    provider: string;
    chain: string;
    cursor: string | null;
    healthy: boolean;
    lag_seconds: number | null;
    last_error: string | null;
    last_success_at: string | null;
  }[];
}

export interface EntityCatalogStats {
  total: number;
  by_label: Record<string, number>;
  by_chain: Record<string, number>;
}

export interface ClientCreate {
  id: string;
  name: string;
  plan: string;
  api_key: string;
}
