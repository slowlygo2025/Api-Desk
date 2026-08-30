"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { proxyJson } from "@/lib/api/client";
import type {
  AdminClient,
  AlertDelivery,
  AlertRule,
  ClientMe,
  EntityCatalogStats,
  EntityList,
  FlowSankey,
  MarketAnalysis,
  MarketSignal,
  MarketSnapshot,
  OpsStatus,
  ReadyStatus,
  StatsOverview,
  Timeseries,
  WhaleEvent,
  WhaleList,
  WorkerStatus,
  Workspace,
} from "@/lib/api/types";

function qs(params: Record<string, string | number | undefined>) {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => proxyJson<ClientMe>("/clients/me"),
  });
}

export function useStats(window = "24h") {
  return useQuery({
    queryKey: ["stats", window],
    queryFn: () => proxyJson<StatsOverview>(`/stats/overview${qs({ window })}`),
    refetchInterval: 30_000,
  });
}

export function useWhales(
  filters: {
    asset?: string;
    chain?: string;
    flow_type?: string;
    min_usd?: number;
    cursor?: string;
    limit?: number;
  },
  options?: { pauseFeed?: boolean },
) {
  return useQuery({
    queryKey: ["whales", filters],
    queryFn: () =>
      proxyJson<WhaleList>(
        `/whales${qs({
          asset: filters.asset,
          chain: filters.chain,
          flow_type: filters.flow_type,
          min_usd: filters.min_usd,
          cursor: filters.cursor,
          limit: filters.limit ?? 50,
        })}`,
      ),
    refetchInterval: options?.pauseFeed ? false : 30_000,
  });
}

export function useWhale(id: string) {
  return useQuery({
    queryKey: ["whale", id],
    queryFn: () => proxyJson<WhaleEvent>(`/whales/${id}`),
    enabled: !!id,
  });
}

export function useReady() {
  return useQuery({
    queryKey: ["ready"],
    queryFn: () => proxyJson<ReadyStatus>("/ready"),
    refetchInterval: 60_000,
  });
}

export function useWorker() {
  return useQuery({
    queryKey: ["worker"],
    queryFn: () => proxyJson<WorkerStatus>("/worker"),
    refetchInterval: 15_000,
  });
}

export function useMarketAnalysis(asset: string) {
  return useQuery({
    queryKey: ["market", "analysis", asset],
    queryFn: () => proxyJson<MarketAnalysis>(`/market/analysis${qs({ asset, persist: "false" })}`),
    enabled: !!asset,
    staleTime: 30_000,
    retry: 2,
    retryDelay: (attempt) => Math.min(3000 * 2 ** attempt, 10_000),
  });
}

export function useMarketSnapshot(asset: string, enabled = false) {
  return useQuery({
    queryKey: ["market", "snapshot", asset],
    queryFn: () => proxyJson<MarketSnapshot>(`/market/snapshot${qs({ asset })}`),
    enabled: !!asset && enabled,
    staleTime: 30_000,
    retry: 2,
  });
}

export function useMarketSignals(asset: string) {
  return useQuery({
    queryKey: ["market", "signals", asset],
    queryFn: () => proxyJson<MarketSignal[]>(`/market/signals${qs({ asset, limit: 30 })}`),
    enabled: !!asset,
  });
}

export function useAlertRules() {
  return useQuery({
    queryKey: ["alerts", "rules"],
    queryFn: () => proxyJson<AlertRule[]>("/alerts/rules"),
  });
}

export function useAlertDeliveries() {
  return useQuery({
    queryKey: ["alerts", "deliveries"],
    queryFn: () => proxyJson<AlertDelivery[]>("/alerts/deliveries?limit=50"),
    refetchInterval: 30_000,
  });
}

export function useTimeseries(window = "24h", bucket = "1h") {
  return useQuery({
    queryKey: ["stats", "timeseries", window, bucket],
    queryFn: () => proxyJson<Timeseries>(`/stats/timeseries${qs({ window, bucket })}`),
    refetchInterval: 60_000,
    retry: false,
  });
}

export function useFlowSankey(window = "24h") {
  return useQuery({
    queryKey: ["stats", "flows", window],
    queryFn: () => proxyJson<FlowSankey>(`/stats/flows/sankey${qs({ window })}`),
    refetchInterval: 60_000,
    retry: false,
  });
}

export function useEntities(params: { q?: string; chain?: string; entity_type?: string; limit?: number }) {
  return useQuery({
    queryKey: ["entities", params],
    queryFn: () =>
      proxyJson<EntityList>(
        `/entities${qs({
          q: params.q,
          chain: params.chain,
          entity_type: params.entity_type,
          limit: params.limit ?? 50,
        })}`,
      ),
    retry: false,
  });
}

export function useEntityCatalogStats() {
  return useQuery({
    queryKey: ["entities", "catalog", "stats"],
    queryFn: () => proxyJson<EntityCatalogStats>("/entities/catalog/stats"),
  });
}

export function useWorkspaces() {
  return useQuery({
    queryKey: ["workspaces"],
    queryFn: () => proxyJson<Workspace[]>("/workspaces"),
    retry: false,
  });
}

export function useOpsStatus() {
  return useQuery({
    queryKey: ["ops"],
    queryFn: () => proxyJson<OpsStatus>("/ops/status"),
    refetchInterval: 15_000,
    retry: false,
  });
}

export function useAdminClients() {
  return useQuery({
    queryKey: ["admin", "clients"],
    queryFn: () => proxyJson<AdminClient[]>("/admin/clients"),
    retry: false,
  });
}

export function useInvalidateWhales() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: ["whales"] });
    qc.invalidateQueries({ queryKey: ["stats"] });
  };
}
