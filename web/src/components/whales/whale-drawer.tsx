"use client";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/badge";
import { ErrorState } from "@/components/ui/states";
import { useWhale } from "@/lib/api/hooks";
import { explorerTxUrl, formatDate, formatUsd, riskColor } from "@/lib/utils";
import Link from "next/link";
import { ImpactExplainer } from "@/components/impact/impact-explainer";

export function WhaleDrawerContent({ whaleId }: { whaleId: string }) {
  const { data, isLoading, isError, refetch } = useWhale(whaleId);

  if (isLoading) return <Skeleton className="h-64" />;
  if (isError || !data) {
    return <ErrorState message="No se pudo cargar la whale." onRetry={() => refetch()} />;
  }

  return (
    <div className="space-y-5">
      <div>
        <p className="text-2xl font-bold">{formatUsd(data.amount_usd)}</p>
        <p className="text-sm text-muted-foreground">
          {data.amount.toLocaleString()} {data.asset} · {data.chain}
        </p>
      </div>

      <section className="space-y-2 rounded-lg border border-border p-3">
        <p className="text-xs font-medium uppercase text-muted-foreground">Clasificación</p>
        <p className="capitalize">{data.flow_type.replace(/_/g, " ")}</p>
        <p className="text-sm">
          <span className="text-muted-foreground">From:</span> {data.from.label}{" "}
          <Badge className="ml-1 border-border">{data.from.entity_type}</Badge>
        </p>
        <p className="text-sm">
          <span className="text-muted-foreground">To:</span> {data.to.label}{" "}
          <Badge className="ml-1 border-border">{data.to.entity_type}</Badge>
        </p>
      </section>

      <section className="space-y-2 rounded-lg border border-border p-3">
        <p className="text-xs font-medium uppercase text-muted-foreground">Riesgo</p>
        <Badge className={riskColor(data.risk.level)}>
          {data.risk.level} · {(data.risk.score * 100).toFixed(0)}%
        </Badge>
        <ul className="list-disc space-y-1 pl-4 text-xs text-muted-foreground">
          {data.risk.factors.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      </section>

      <section className="space-y-2 rounded-lg border border-border p-3">
        <p className="text-xs font-medium uppercase text-muted-foreground">Impacto estimado</p>
        {data.impact.score != null ? (
          <>
            <p className="text-lg font-semibold">{(data.impact.score * 100).toFixed(0)}%</p>
            <p className="text-xs text-muted-foreground">
              Horizonte: {data.impact.horizon ?? "—"} · Confianza:{" "}
              {data.impact.confidence != null ? `${(data.impact.confidence * 100).toFixed(0)}%` : "—"}
            </p>
            <ImpactExplainer impact={data.impact} />
          </>
        ) : (
          <p className="text-sm text-muted-foreground">Sin predicción disponible</p>
        )}
      </section>

      <section className="space-y-2 rounded-lg border border-border p-3 text-sm">
        <p className="text-xs font-medium uppercase text-muted-foreground">Transacción</p>
        <p className="break-all font-mono text-xs">
          <a
            href={explorerTxUrl(data.chain, data.tx_hash)}
            target="_blank"
            rel="noreferrer"
            className="text-primary hover:underline"
          >
            {data.tx_hash}
          </a>
        </p>
        <p>
          <span className="text-muted-foreground">Detectado:</span> {formatDate(data.detected_at)}
        </p>
      </section>

      <Link href={`/whales/${data.id}`} className="text-sm text-primary hover:underline">
        Abrir página completa →
      </Link>
    </div>
  );
}
