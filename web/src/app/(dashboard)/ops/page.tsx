"use client";

import { Card, CardTitle, CardValue } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ErrorState, LoadingSkeleton } from "@/components/ui/states";
import { useOpsStatus, useReady } from "@/lib/api/hooks";
import { formatDate } from "@/lib/utils";

export default function OpsPage() {
  const ops = useOpsStatus();
  const ready = useReady();

  if (ops.isLoading) return <LoadingSkeleton rows={6} />;
  if (ops.isError) {
    return (
      <ErrorState
        title="Ops no disponible"
        message="Requiere plan Institutional (scope admin.ops)."
        onRetry={() => ops.refetch()}
      />
    );
  }

  const data = ops.data!;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Ops institucional</h1>
        <p className="text-sm text-muted-foreground">Worker, cola, providers y salud del sistema.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardTitle>Worker</CardTitle>
          <CardValue className={data.worker.running ? "text-emerald-400" : "text-red-400"}>
            {data.worker.running ? "Activo" : "Detenido"}
          </CardValue>
        </Card>
        <Card>
          <CardTitle>Cola jobs</CardTitle>
          <CardValue>{data.queue}</CardValue>
        </Card>
        <Card>
          <CardTitle>Ready</CardTitle>
          <CardValue className={ready.data?.status === "ready" ? "text-emerald-400" : "text-amber-400"}>
            {ready.data?.status ?? "—"}
          </CardValue>
        </Card>
      </div>

      <Card>
        <CardTitle className="mb-4">Providers ({data.providers.length})</CardTitle>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-border text-xs uppercase text-muted-foreground">
              <tr>
                <th className="py-2">Provider</th>
                <th className="py-2">Chain</th>
                <th className="py-2">Estado</th>
                <th className="py-2">Lag</th>
                <th className="py-2">Último OK</th>
                <th className="py-2">Error</th>
              </tr>
            </thead>
            <tbody>
              {data.providers.map((p) => (
                <tr key={`${p.provider}-${p.chain}`} className="border-b border-border/50">
                  <td className="py-2">{p.provider}</td>
                  <td className="py-2 capitalize">{p.chain}</td>
                  <td className="py-2">
                    <Badge className={p.healthy ? "border-emerald-900 text-emerald-400" : "border-red-900 text-red-400"}>
                      {p.healthy ? "OK" : "fail"}
                    </Badge>
                  </td>
                  <td className="py-2 font-mono text-xs">
                    {p.lag_seconds != null ? `${p.lag_seconds.toFixed(0)}s` : "—"}
                  </td>
                  <td className="py-2 text-xs text-muted-foreground">
                    {p.last_success_at ? formatDate(p.last_success_at) : "—"}
                  </td>
                  <td className="max-w-[200px] truncate py-2 text-xs text-red-400">{p.last_error ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
