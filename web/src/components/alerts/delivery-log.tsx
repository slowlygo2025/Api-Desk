"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/ui/states";
import { useAlertDeliveries } from "@/lib/api/hooks";
import { formatDate } from "@/lib/utils";
import { useState } from "react";

function statusColor(status: string) {
  switch (status) {
    case "delivered":
    case "sent":
      return "border-emerald-900 text-emerald-400";
    case "failed":
      return "border-red-900 text-red-400";
    default:
      return "border-amber-900 text-amber-400";
  }
}

export function DeliveryLog() {
  const [statusFilter, setStatusFilter] = useState("");
  const deliveries = useAlertDeliveries();

  if (deliveries.isLoading) return <LoadingSkeleton rows={4} />;
  if (deliveries.isError) {
    return (
      <ErrorState message="No se pudo cargar el log de entregas." onRetry={() => deliveries.refetch()} />
    );
  }

  const items = (deliveries.data ?? []).filter((d) => !statusFilter || d.status === statusFilter);

  if (!deliveries.data?.length) {
    return (
      <EmptyState
        title="Sin entregas aún"
        description="Las alertas enviadas aparecerán aquí con canal, estado y respuesta del webhook."
      />
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {["", "delivered", "sent", "failed", "pending"].map((s) => (
          <button
            key={s || "all"}
            onClick={() => setStatusFilter(s)}
            className={`rounded-md border px-2 py-0.5 text-xs ${
              statusFilter === s ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground"
            }`}
          >
            {s || "Todos"}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="border-b border-border bg-muted/30 text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-3 py-2">Fecha</th>
              <th className="px-3 py-2">Regla</th>
              <th className="px-3 py-2">Canal</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2">Whale</th>
              <th className="px-3 py-2">Respuesta</th>
            </tr>
          </thead>
          <tbody>
            {items.map((d) => (
              <tr key={d.id} className="border-b border-border/60 hover:bg-muted/20">
                <td className="px-3 py-2 whitespace-nowrap text-xs text-muted-foreground">
                  {formatDate(d.created_at)}
                </td>
                <td className="px-3 py-2 text-xs">{d.rule_name ?? d.rule_id.slice(0, 8)}</td>
                <td className="px-3 py-2">{d.channel}</td>
                <td className="px-3 py-2">
                  <Badge className={statusColor(d.status)}>{d.status}</Badge>
                </td>
                <td className="px-3 py-2">
                  {d.whale_id ? (
                    <Link href={`/whales/${d.whale_id}`} className="text-xs text-primary hover:underline">
                      Ver whale
                    </Link>
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </td>
                <td className="max-w-[180px] truncate px-3 py-2 font-mono text-xs text-muted-foreground">
                  {Object.keys(d.response ?? {}).length
                    ? JSON.stringify(d.response).slice(0, 80)
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
