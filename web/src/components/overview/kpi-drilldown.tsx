"use client";

import { Drawer } from "@/components/ui/drawer";
import { WhaleTable } from "@/components/whales/whale-table";
import { useWhales } from "@/lib/api/hooks";
import { formatUsd } from "@/lib/utils";
import { ErrorState, LoadingSkeleton } from "@/components/ui/states";

export type DrillMetric = "events" | "volume" | "high_risk" | "asset" | "chain" | "flow";

interface Props {
  metric: DrillMetric | null;
  window?: string;
  filterValue?: string;
  onClose: () => void;
}

export function KpiDrilldown({ metric, filterValue, onClose }: Props) {
  const filters: Parameters<typeof useWhales>[0] = { limit: 30 };

  if (metric === "high_risk") {
    // API no tiene min_risk_level; filtramos en cliente post-fetch o usamos min_usd alto
    filters.min_usd = 10_000_000;
  }
  if (metric === "asset" && filterValue) filters.asset = filterValue;
  if (metric === "chain" && filterValue) filters.chain = filterValue;
  if (metric === "flow" && filterValue) filters.flow_type = filterValue;

  const whales = useWhales(filters);
  const items =
    metric === "high_risk"
      ? (whales.data?.items ?? []).filter((w) => w.risk.level === "high")
      : (whales.data?.items ?? []);

  const titles: Record<DrillMetric, string> = {
    events: "Detalle: eventos",
    volume: "Detalle: volumen",
    high_risk: "Detalle: alto riesgo",
    asset: `Detalle: ${filterValue}`,
    chain: `Detalle: ${filterValue}`,
    flow: `Detalle: ${filterValue}`,
  };

  return (
    <Drawer
      open={!!metric}
      onClose={onClose}
      title={metric ? titles[metric] : "Detalle"}
      width="max-w-2xl"
    >
      {whales.isLoading && <LoadingSkeleton />}
      {whales.isError && (
        <ErrorState message="Error cargando detalle." onRetry={() => whales.refetch()} />
      )}
      {whales.data && (
        <div className="space-y-4">
          {metric === "volume" && (
            <p className="text-sm text-muted-foreground">
              Volumen en página:{" "}
              <span className="font-mono text-foreground">
                {formatUsd(items.reduce((s, w) => s + w.amount_usd, 0))}
              </span>
            </p>
          )}
          <WhaleTable items={items} onSelect={() => {}} />
        </div>
      )}
    </Drawer>
  );
}
