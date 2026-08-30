"use client";

import { useState } from "react";
import { Card, CardTitle, CardValue } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs } from "@/components/ui/tabs";
import { EmptyState } from "@/components/ui/states";
import { useMarketAnalysis, useMarketSignals, useMarketSnapshot, useMe } from "@/lib/api/hooks";
import { formatDate } from "@/lib/utils";

const ASSETS = ["BTC", "ETH", "SOL", "BNB", "XMR"];

export default function MarketPage() {
  const [asset, setAsset] = useState("BTC");
  const [tab, setTab] = useState("analysis");
  const { data: me } = useMe();
  const hasSignals = me?.scopes.includes("market.signals") ?? false;
  const analysis = useMarketAnalysis(asset);
  const snapshot = useMarketSnapshot(asset, analysis.isError);
  const signals = useMarketSignals(hasSignals ? asset : "");

  const showSnapshotFallback = analysis.isError && snapshot.data && snapshot.data.venues_ok > 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Market Signals</h1>
        <p className="text-sm text-muted-foreground">
          Capa auxiliar CEX (trades, book, OHLC). El producto principal son whales on-chain.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {ASSETS.map((a) => (
          <button
            key={a}
            onClick={() => setAsset(a)}
            className={`rounded-md border px-3 py-1 text-sm ${
              asset === a
                ? "border-primary bg-primary/10 text-primary"
                : "border-border text-muted-foreground hover:bg-muted"
            }`}
          >
            {a}
          </button>
        ))}
      </div>

      <Tabs
        tabs={[
          { id: "analysis", label: "Análisis" },
          { id: "history", label: "Historial" },
        ]}
        active={tab}
        onChange={setTab}
      />

      {tab === "analysis" && (
        <>
          {analysis.isLoading && (
            <Card>
              <p className="text-sm text-muted-foreground">
                Consultando exchanges (Kraken, KuCoin, MEXC, Bitfinex, HTX)… puede tardar unos segundos.
              </p>
              <Skeleton className="mt-3 h-32" />
            </Card>
          )}

          {analysis.isError && !showSnapshotFallback && (
            <Card className="space-y-3">
              <p className="text-sm text-amber-400">
                Sin datos CEX para {asset}. Los exchanges no respondieron tras reintentos.
              </p>
              {snapshot.isLoading && (
                <p className="text-xs text-muted-foreground">Comprobando snapshot de respaldo…</p>
              )}
              <Button variant="outline" className="h-8 px-3 text-xs" onClick={() => analysis.refetch()}>
                Reintentar
              </Button>
            </Card>
          )}

          {showSnapshotFallback && snapshot.data && (
            <Card className="space-y-3 border-amber-900/40">
              <p className="text-sm text-amber-200">
                Análisis completo no disponible; mostrando snapshot parcial (
                {snapshot.data.venues_ok}/{snapshot.data.venues_total} venues OK).
              </p>
              <div className="grid gap-4 sm:grid-cols-3">
                <Card>
                  <CardTitle>Mid medio</CardTitle>
                  <CardValue>
                    {typeof snapshot.data.meta.mid_mean === "number"
                      ? `$${Number(snapshot.data.meta.mid_mean).toLocaleString()}`
                      : "—"}
                  </CardValue>
                </Card>
                <Card>
                  <CardTitle>Spread cross-CEX</CardTitle>
                  <CardValue>
                    {typeof snapshot.data.meta.cross_exchange_spread_bps === "number"
                      ? `${Number(snapshot.data.meta.cross_exchange_spread_bps).toFixed(1)} bps`
                      : "—"}
                  </CardValue>
                </Card>
                <Card>
                  <CardTitle>Venues</CardTitle>
                  <CardValue className="text-lg">
                    {snapshot.data.venues_ok}/{snapshot.data.venues_total}
                  </CardValue>
                </Card>
              </div>
              <VenueList venues={snapshot.data.venues} />
              <Button variant="outline" className="h-8 px-3 text-xs" onClick={() => analysis.refetch()}>
                Reintentar análisis
              </Button>
            </Card>
          )}

          {analysis.data && (
            <>
              <div className="grid gap-4 sm:grid-cols-3">
                <Card>
                  <CardTitle>Stress</CardTitle>
                  <CardValue>{(analysis.data.stress_score * 100).toFixed(1)}%</CardValue>
                </Card>
                <Card>
                  <CardTitle>Régimen</CardTitle>
                  <CardValue className="text-lg capitalize">{analysis.data.regime}</CardValue>
                </Card>
                <Card>
                  <CardTitle>Spillover vs BTC</CardTitle>
                  <CardValue>{(analysis.data.spillover_hint * 100).toFixed(1)}%</CardValue>
                </Card>
              </div>
              {analysis.data.signals?.length > 0 && (
                <Card>
                  <CardTitle className="mb-3">Señales activas</CardTitle>
                  <ul className="space-y-2">
                    {analysis.data.signals.map((s, i) => (
                      <li key={i} className="flex items-start justify-between gap-2 text-sm">
                        <span>{s.title}</span>
                        <Badge className="shrink-0 border-border">{s.severity}</Badge>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}
            </>
          )}
        </>
      )}

      {tab === "history" && (
        <>
          {!hasSignals && (
            <Card>
              <p className="text-sm text-muted-foreground">
                Historial de señales requiere plan Pro+ (scope market.signals).
              </p>
            </Card>
          )}
          {hasSignals && signals.isLoading && <Skeleton className="h-40" />}
          {hasSignals && signals.data && signals.data.length > 0 && (
            <Card>
              <ul className="divide-y divide-border">
                {signals.data.map((s, i) => (
                  <li key={i} className="flex justify-between py-2 text-sm">
                    <span>
                      {s.title}{" "}
                      <span className="text-muted-foreground">({s.signal_type})</span>
                    </span>
                    <span className="text-muted-foreground">{formatDate(s.ts)}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}
          {hasSignals && !signals.isLoading && signals.data?.length === 0 && (
            <EmptyState title={`Sin señales para ${asset}`} description="Las señales persistidas aparecerán cuando el análisis detecte eventos." />
          )}
        </>
      )}
    </div>
  );
}

function VenueList({ venues }: { venues: { exchange: string; ok: boolean; error?: string | null; mid?: number | null }[] }) {
  return (
    <ul className="space-y-1 text-xs">
      {venues.map((v) => (
        <li key={v.exchange} className="flex justify-between gap-2">
          <span className="capitalize">{v.exchange}</span>
          <span className={v.ok ? "text-emerald-400" : "text-red-400"}>
            {v.ok ? (v.mid ? `$${v.mid.toLocaleString()}` : "OK") : v.error || "error"}
          </span>
        </li>
      ))}
    </ul>
  );
}
