"use client";

import { Card, CardTitle } from "@/components/ui/card";
import { useTimeseries } from "@/lib/api/hooks";
import { formatUsd } from "@/lib/utils";
import { ErrorState, LoadingSkeleton } from "@/components/ui/states";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function TimeseriesChart({ window = "24h" }: { window?: string }) {
  const ts = useTimeseries(window, "1h");

  if (ts.isLoading) return <LoadingSkeleton rows={4} />;
  if (ts.isError) {
    return (
      <ErrorState
        title="Timeseries no disponible"
        message="Requiere plan Pro+ (scope stats.timeseries)."
        onRetry={() => ts.refetch()}
      />
    );
  }
  if (!ts.data?.buckets.length) {
    return null;
  }

  const data = ts.data.buckets.map((b) => ({
    time: new Intl.DateTimeFormat("es-ES", { hour: "2-digit", minute: "2-digit" }).format(new Date(b.ts)),
    eventos: b.events,
    volumen: b.volume_usd,
    riesgo: b.high_risk,
  }));

  return (
    <Card>
      <CardTitle className="mb-4">Actividad histórica ({window})</CardTitle>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis dataKey="time" stroke="#71717a" fontSize={11} />
            <YAxis yAxisId="left" stroke="#71717a" fontSize={11} allowDecimals={false} />
            <YAxis yAxisId="right" orientation="right" stroke="#71717a" fontSize={11} tickFormatter={(v) => formatUsd(v)} />
            <Tooltip
              contentStyle={{ background: "#18181b", border: "1px solid #27272a", fontSize: 12 }}
              formatter={(value, name) => {
                if (name === "volumen") return [formatUsd(Number(value)), "Volumen"];
                return [value, name === "eventos" ? "Eventos" : "Alto riesgo"];
              }}
            />
            <Area yAxisId="left" type="monotone" dataKey="eventos" stroke="#22c55e" fill="#22c55e33" />
            <Area yAxisId="right" type="monotone" dataKey="volumen" stroke="#3b82f6" fill="#3b82f633" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
