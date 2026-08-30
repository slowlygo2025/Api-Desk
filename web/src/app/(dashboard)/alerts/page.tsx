"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/badge";
import { Card, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DeliveryLog } from "@/components/alerts/delivery-log";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/ui/states";
import { useAlertRules, useMe } from "@/lib/api/hooks";
import { proxyFetch } from "@/lib/api/client";
import { useQueryClient } from "@tanstack/react-query";

export default function AlertsPage() {
  const { data: me } = useMe();
  const rules = useAlertRules();
  const qc = useQueryClient();
  const canManage = me?.scopes.includes("alerts.manage") ?? false;

  const [name, setName] = useState("");
  const [minUsd, setMinUsd] = useState("10000000");
  const [kind, setKind] = useState("whale");
  const [error, setError] = useState("");

  async function createRule() {
    setError("");
    try {
      const res = await proxyFetch("/alerts/rules", {
        method: "POST",
        body: JSON.stringify({
          name,
          min_usd: Number(minUsd),
          alert_kinds: [kind],
          channels: ["webhook"],
          is_active: true,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      setName("");
      qc.invalidateQueries({ queryKey: ["alerts"] });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function deleteRule(id: string) {
    await proxyFetch(`/alerts/rules/${id}`, { method: "DELETE" });
    qc.invalidateQueries({ queryKey: ["alerts"] });
  }

  if (!canManage) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Alertas</h1>
        <EmptyState
          title="Alertas no incluidas en tu plan"
          description={`Tu plan (${me?.plan}) no incluye gestión de alertas. Actualiza a Pro o Institutional.`}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Alertas</h1>
        <p className="text-sm text-muted-foreground">Reglas whale / market / both · log de entregas con respuesta.</p>
      </div>

      <Card className="space-y-3">
        <CardTitle>Nueva regla</CardTitle>
        <div className="grid gap-3 sm:grid-cols-3">
          <Input placeholder="Nombre" value={name} onChange={(e) => setName(e.target.value)} />
          <Input
            placeholder="Min USD"
            type="number"
            value={minUsd}
            onChange={(e) => setMinUsd(e.target.value)}
          />
          <select
            className="h-10 rounded-md border border-border bg-background px-3 text-sm"
            value={kind}
            onChange={(e) => setKind(e.target.value)}
          >
            <option value="whale">whale</option>
            <option value="market">market</option>
            <option value="both">both</option>
          </select>
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <Button disabled={!name} onClick={createRule}>
          Crear regla
        </Button>
      </Card>

      {rules.isLoading && <LoadingSkeleton rows={3} />}
      {rules.isError && (
        <ErrorState message="Error cargando reglas." onRetry={() => rules.refetch()} />
      )}
      {rules.data && (
        <Card>
          <CardTitle className="mb-3">Reglas activas</CardTitle>
          {rules.data.length === 0 ? (
            <EmptyState title="Sin reglas" description="Crea una regla para recibir alertas por webhook." />
          ) : (
            <ul className="divide-y divide-border">
              {rules.data.map((r) => (
                <li key={r.id} className="flex items-center justify-between py-3 text-sm">
                  <div>
                    <p className="font-medium">{r.name}</p>
                    <p className="text-xs text-muted-foreground">
                      ≥ ${r.min_usd.toLocaleString()} · {r.alert_kinds.join(", ")}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={r.is_active ? "border-emerald-900 text-emerald-400" : ""}>
                      {r.is_active ? "activa" : "off"}
                    </Badge>
                    <Button variant="destructive" className="h-8 px-2 text-xs" onClick={() => deleteRule(r.id)}>
                      Borrar
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      <Card>
        <CardTitle className="mb-4">Log de entregas</CardTitle>
        <DeliveryLog />
      </Card>
    </div>
  );
}
