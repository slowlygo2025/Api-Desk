"use client";

import { Card, CardTitle } from "@/components/ui/card";
import { useFlowSankey } from "@/lib/api/hooks";
import { formatUsd } from "@/lib/utils";
import { ErrorState, LoadingSkeleton } from "@/components/ui/states";

export function SankeyFlowChart({ window = "24h" }: { window?: string }) {
  const flows = useFlowSankey(window);

  if (flows.isLoading) return <LoadingSkeleton rows={6} />;
  if (flows.isError) {
    return (
      <ErrorState
        title="Mapa de flujos no disponible"
        message="Requiere plan Institutional (scope stats.flows)."
        onRetry={() => flows.refetch()}
      />
    );
  }

  const { nodes, links } = flows.data ?? { nodes: [], links: [] };
  if (!links.length) {
    return null;
  }

  const nodePos: Record<string, { x: number; y: number }> = {};
  const sources = new Set(links.map((l) => l.source));
  const targets = new Set(links.map((l) => l.target));
  const leftNodes = nodes.filter((n) => sources.has(n.id) && !targets.has(n.id));
  const rightNodes = nodes.filter((n) => targets.has(n.id) && !sources.has(n.id));
  const midNodes = nodes.filter((n) => !leftNodes.find((l) => l.id === n.id) && !rightNodes.find((r) => r.id === n.id));

  [...leftNodes, ...midNodes, ...rightNodes].forEach((n) => {
    const col = leftNodes.includes(n) ? 0 : rightNodes.includes(n) ? 2 : 1;
    const colNodes = col === 0 ? leftNodes : col === 2 ? rightNodes : midNodes;
    const idx = colNodes.indexOf(n);
    nodePos[n.id] = { x: 80 + col * 200, y: 40 + idx * 36 };
  });

  const maxVal = Math.max(...links.map((l) => l.value), 1);

  return (
    <Card>
      <CardTitle className="mb-4">Flujos agregados ({window})</CardTitle>
      <div className="overflow-x-auto">
        <svg viewBox="0 0 560 320" className="w-full min-w-[480px]" role="img" aria-label="Diagrama Sankey de flujos">
          {links.map((link, i) => {
            const s = nodePos[link.source];
            const t = nodePos[link.target];
            if (!s || !t) return null;
            const w = Math.max(2, (link.value / maxVal) * 12);
            const path = `M ${s.x + 80} ${s.y + 12} C ${(s.x + t.x) / 2} ${s.y + 12}, ${(s.x + t.x) / 2} ${t.y + 12}, ${t.x} ${t.y + 12}`;
            return (
              <path
                key={i}
                d={path}
                fill="none"
                stroke="#22c55e"
                strokeWidth={w}
                strokeOpacity={0.35}
              />
            );
          })}
          {nodes.map((n) => {
            const p = nodePos[n.id];
            if (!p) return null;
            return (
              <g key={n.id}>
                <rect x={p.x} y={p.y} width={120} height={24} rx={4} fill="#27272a" stroke="#3f3f46" />
                <text x={p.x + 6} y={p.y + 16} fill="#e4e4e7" fontSize={10}>
                  {n.label.length > 14 ? `${n.label.slice(0, 14)}…` : n.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
      <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
        {links.slice(0, 8).map((l, i) => {
          const src = nodes.find((n) => n.id === l.source);
          const tgt = nodes.find((n) => n.id === l.target);
          return (
            <li key={i}>
              {src?.label} → {tgt?.label}: {formatUsd(l.value)} ({l.count} tx)
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
