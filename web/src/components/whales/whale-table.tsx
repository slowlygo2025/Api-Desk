"use client";

import { formatDate, formatUsd, riskColor } from "@/lib/utils";
import type { WhaleEvent } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/states";

export function WhaleTable({
  items,
  onSelect,
  selectedId,
}: {
  items: WhaleEvent[];
  onSelect?: (id: string) => void;
  selectedId?: string;
}) {
  if (!items.length) {
    return (
      <EmptyState
        title="Sin whales detectadas"
        description="El worker escanea cadenas continuamente. Ajusta filtros o espera nuevas detecciones."
      />
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="border-b border-border bg-muted/30 text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2">Hora</th>
            <th className="px-3 py-2">Asset</th>
            <th className="px-3 py-2">Chain</th>
            <th className="px-3 py-2">USD</th>
            <th className="px-3 py-2">Flujo</th>
            <th className="px-3 py-2">Riesgo</th>
            <th className="px-3 py-2">Ruta</th>
          </tr>
        </thead>
        <tbody>
          {items.map((w) => (
            <tr
              key={w.id}
              className={`cursor-pointer border-b border-border/60 hover:bg-muted/20 ${
                selectedId === w.id ? "bg-primary/10" : ""
              }`}
              onClick={() => onSelect?.(w.id)}
            >
              <td className="px-3 py-2 whitespace-nowrap text-muted-foreground">
                {formatDate(w.detected_at)}
              </td>
              <td className="px-3 py-2 font-medium">{w.asset}</td>
              <td className="px-3 py-2 capitalize text-muted-foreground">{w.chain}</td>
              <td className="px-3 py-2 font-mono">{formatUsd(w.amount_usd)}</td>
              <td className="px-3 py-2">
                <Badge className="border-border bg-muted/40">{w.flow_type}</Badge>
              </td>
              <td className="px-3 py-2">
                <Badge className={riskColor(w.risk.level)}>{w.risk.level}</Badge>
              </td>
              <td className="max-w-[220px] truncate px-3 py-2 text-xs text-muted-foreground">
                {w.from.label} → {w.to.label}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
