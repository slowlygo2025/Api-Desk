"use client";

import Link from "next/link";
import { useState } from "react";
import { Card, CardTitle, CardValue } from "@/components/ui/card";
import { WhaleTable } from "@/components/whales/whale-table";
import { KpiDrilldown, type DrillMetric } from "@/components/overview/kpi-drilldown";
import { TimeseriesChart } from "@/components/overview/timeseries-chart";
import { useReady, useStats, useWhales, useWorker } from "@/lib/api/hooks";
import { formatUsd } from "@/lib/utils";
import { ErrorState, TableSkeleton } from "@/components/ui/states";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function OverviewPage() {
  const stats = useStats("24h");
  const whales = useWhales({ limit: 5 });
  const ready = useReady();
  const worker = useWorker();
  const [drill, setDrill] = useState<{ metric: DrillMetric; value?: string } | null>(null);

  const chartData = stats.data
    ? Object.entries(stats.data.by_asset).map(([asset, count]) => ({ asset, count }))
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Overview</h1>
        <p className="text-sm text-muted-foreground">
          Producto principal: whales on-chain multi-chain. Ventana 24h. KPIs clickeables.
        </p>
      </div>

      {stats.isError && (
        <ErrorState message="Error cargando estadísticas." onRetry={() => stats.refetch()} />
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card
          className="cursor-pointer transition-colors hover:border-primary/40"
          onClick={() => setDrill({ metric: "events" })}
        >
          <CardTitle>Eventos</CardTitle>
          <CardValue>{stats.data?.total_events ?? "—"}</CardValue>
        </Card>
        <Card
          className="cursor-pointer transition-colors hover:border-primary/40"
          onClick={() => setDrill({ metric: "volume" })}
        >
          <CardTitle>Volumen USD</CardTitle>
          <CardValue>{stats.data ? formatUsd(stats.data.total_volume_usd) : "—"}</CardValue>
        </Card>
        <Card
          className="cursor-pointer transition-colors hover:border-primary/40"
          onClick={() => setDrill({ metric: "high_risk" })}
        >
          <CardTitle>Alto riesgo</CardTitle>
          <CardValue className="text-amber-400">{stats.data?.high_risk_count ?? "—"}</CardValue>
        </Card>
        <Card>
          <CardTitle>Sistema</CardTitle>
          <CardValue className="text-base">
            {ready.data?.status === "ready" ? (
              <span className="text-emerald-400">Operativo</span>
            ) : (
              <span className="text-amber-400">Degradado</span>
            )}
          </CardValue>
          <p className="mt-1 text-xs text-muted-foreground">
            Providers {ready.data?.providers_healthy}/{ready.data?.providers_total} · Worker{" "}
            {worker.data?.running ? "activo" : "detenido"}
          </p>
        </Card>
      </div>

      <TimeseriesChart window="24h" />

      {chartData.length > 0 && (
        <Card>
          <CardTitle className="mb-4">Por asset (24h) — clic para drill-down</CardTitle>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="asset" stroke="#71717a" fontSize={12} />
                <YAxis stroke="#71717a" fontSize={12} allowDecimals={false} />
                <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #27272a" }} />
                <Bar
                  dataKey="count"
                  fill="#22c55e"
                  radius={[4, 4, 0, 0]}
                  onClick={(barData) => {
                    const payload = barData?.payload as { asset?: string } | undefined;
                    if (payload?.asset) setDrill({ metric: "asset", value: payload.asset });
                  }}
                  style={{ cursor: "pointer" }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Últimas whales</h2>
          <Link href="/whales" className="text-sm text-primary hover:underline">
            Ver todas →
          </Link>
        </div>
        {whales.isLoading && <TableSkeleton />}
        {whales.isError && (
          <ErrorState message="Error cargando whales." onRetry={() => whales.refetch()} />
        )}
        {whales.data && <WhaleTable items={whales.data.items} />}
      </div>

      <KpiDrilldown
        metric={drill?.metric ?? null}
        filterValue={drill?.value}
        onClose={() => setDrill(null)}
      />
    </div>
  );
}
