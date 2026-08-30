"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Card, CardTitle, CardValue } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/badge";
import { ImpactExplainer } from "@/components/impact/impact-explainer";
import { ErrorState } from "@/components/ui/states";
import { useWhale } from "@/lib/api/hooks";
import { explorerTxUrl, formatDate, formatUsd, riskColor } from "@/lib/utils";

export default function WhaleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, isError } = useWhale(id);

  if (isLoading) return <Skeleton className="h-96" />;
  if (isError || !data) {
    return (
      <div className="space-y-4">
        <Link href="/whales" className="text-sm text-primary hover:underline">
          ← Volver
        </Link>
        <ErrorState title="Whale no encontrada" message="El ID no existe o fue eliminado." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link href="/whales" className="text-sm text-primary hover:underline">
        ← Volver al feed
      </Link>

      <div>
        <h1 className="text-3xl font-bold">{formatUsd(data.amount_usd)}</h1>
        <p className="text-muted-foreground">
          {data.amount.toLocaleString()} {data.asset} · {data.chain}
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardTitle>Clasificación</CardTitle>
          <CardValue className="text-lg capitalize">{data.flow_type.replace(/_/g, " ")}</CardValue>
          <div className="mt-3 space-y-2 text-sm">
            <p>
              <span className="text-muted-foreground">From:</span> {data.from.label}{" "}
              <Badge className="ml-1 border-border">{data.from.entity_type}</Badge>
            </p>
            <p>
              <span className="text-muted-foreground">To:</span> {data.to.label}{" "}
              <Badge className="ml-1 border-border">{data.to.entity_type}</Badge>
            </p>
          </div>
        </Card>

        <Card>
          <CardTitle>Riesgo</CardTitle>
          <CardValue>
            <Badge className={riskColor(data.risk.level)}>
              {data.risk.level} · {(data.risk.score * 100).toFixed(0)}%
            </Badge>
          </CardValue>
          <ul className="mt-3 list-disc space-y-1 pl-4 text-xs text-muted-foreground">
            {data.risk.factors.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </Card>

        <Card>
          <CardTitle>Impacto estimado</CardTitle>
          {data.impact.score != null ? (
            <>
              <CardValue>{(data.impact.score * 100).toFixed(0)}%</CardValue>
              <p className="mt-2 text-sm text-muted-foreground">
                Horizonte: {data.impact.horizon ?? "—"} · Confianza:{" "}
                {data.impact.confidence != null ? `${(data.impact.confidence * 100).toFixed(0)}%` : "—"}
              </p>
              <ImpactExplainer impact={data.impact} />
            </>
          ) : (
            <p className="mt-2 text-sm text-muted-foreground">Sin predicción disponible</p>
          )}
        </Card>
      </div>

      <Card>
        <CardTitle>Transacción</CardTitle>
        <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">TX Hash</dt>
            <dd className="break-all font-mono text-xs">
              <a
                href={explorerTxUrl(data.chain, data.tx_hash)}
                target="_blank"
                rel="noreferrer"
                className="text-primary hover:underline"
              >
                {data.tx_hash}
              </a>
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Provider</dt>
            <dd>{data.provider}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Detectado</dt>
            <dd>{formatDate(data.detected_at)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Block time</dt>
            <dd>{data.block_time ? formatDate(data.block_time) : "—"}</dd>
          </div>
        </dl>
      </Card>
    </div>
  );
}
