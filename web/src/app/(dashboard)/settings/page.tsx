"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/badge";
import { Card, CardTitle, CardValue } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/badge";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { useEntityCatalogStats, useMe, useWorkspaces } from "@/lib/api/hooks";
import { proxyFetch } from "@/lib/api/client";
import { useQueryClient } from "@tanstack/react-query";

export default function SettingsPage() {
  const { data: me, isLoading } = useMe();
  const catalog = useEntityCatalogStats();
  const workspaces = useWorkspaces();
  const qc = useQueryClient();
  const canWorkspaces = me?.scopes.includes("workspaces.manage") ?? false;

  const [wsName, setWsName] = useState("");

  async function createWorkspace() {
    if (!wsName.trim()) return;
    await proxyFetch("/workspaces", {
      method: "POST",
      body: JSON.stringify({
        name: wsName.trim(),
        config: { defaultView: "whales" },
        is_default: false,
      }),
    });
    setWsName("");
    qc.invalidateQueries({ queryKey: ["workspaces"] });
  }

  async function deleteWorkspace(id: string) {
    await proxyFetch(`/workspaces/${id}`, { method: "DELETE" });
    qc.invalidateQueries({ queryKey: ["workspaces"] });
  }

  if (isLoading) return <Skeleton className="h-64" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Ajustes</h1>
        <p className="text-sm text-muted-foreground">Perfil, plan, workspaces Pro y catálogo de entities.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardTitle>Cuenta</CardTitle>
          <CardValue className="text-lg">{me?.name}</CardValue>
          <p className="mt-2 text-sm text-muted-foreground">ID: {me?.id}</p>
          <p className="text-sm text-muted-foreground">Key prefix: {me?.api_key_prefix}…</p>
        </Card>
        <Card>
          <CardTitle>Plan</CardTitle>
          <CardValue className="uppercase">{me?.plan}</CardValue>
          <p className="mt-2 text-sm text-muted-foreground">
            Rate limit: {me?.rate_limit_per_min}/min
          </p>
          <p className="text-sm text-muted-foreground">
            Cuota diaria: {me?.daily_usage}/{me?.daily_quota}
          </p>
        </Card>
      </div>

      {catalog.data && (
        <Card>
          <CardTitle className="mb-2">Entity catalog</CardTitle>
          <p className="text-sm text-muted-foreground">
            {catalog.data.total} direcciones etiquetadas ·{" "}
            {Object.keys(catalog.data.by_chain).length} chains
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {Object.entries(catalog.data.by_label)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 12)
              .map(([label, count]) => (
                <span key={label} className="rounded-md border border-border px-2 py-0.5 text-xs">
                  {label} ({count})
                </span>
              ))}
          </div>
        </Card>
      )}

      {canWorkspaces && (
        <Card className="space-y-3">
          <CardTitle>Workspaces Pro</CardTitle>
          <p className="text-sm text-muted-foreground">
            Guarda layouts y configuraciones por workspace (sincronizado en servidor).
          </p>
          <div className="flex gap-2">
            <Input
              placeholder="Nombre workspace"
              value={wsName}
              onChange={(e) => setWsName(e.target.value)}
              className="h-9 max-w-xs"
            />
            <Button className="h-9" disabled={!wsName.trim()} onClick={createWorkspace}>
              Crear
            </Button>
          </div>
          {workspaces.isError && (
            <ErrorState message="Error cargando workspaces." onRetry={() => workspaces.refetch()} />
          )}
          {workspaces.data?.length === 0 && (
            <EmptyState title="Sin workspaces" description="Crea uno para guardar tu configuración." />
          )}
          {workspaces.data && workspaces.data.length > 0 && (
            <ul className="divide-y divide-border text-sm">
              {workspaces.data.map((w) => (
                <li key={w.id} className="flex items-center justify-between py-2">
                  <span>
                    {w.name}
                    {w.is_default && (
                      <span className="ml-2 text-xs text-primary">(default)</span>
                    )}
                  </span>
                  <Button variant="destructive" className="h-7 px-2 text-xs" onClick={() => deleteWorkspace(w.id)}>
                    Borrar
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      <Card>
        <CardTitle className="mb-3">Scopes incluidos</CardTitle>
        <div className="flex flex-wrap gap-2">
          {(me?.scopes ?? []).map((s) => (
            <span key={s} className="rounded-md border border-border bg-muted/40 px-2 py-1 text-xs">
              {s}
            </span>
          ))}
        </div>
      </Card>

      <Card>
        <CardTitle className="mb-2">Documentación API</CardTitle>
        <a
          href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/docs`}
          target="_blank"
          rel="noreferrer"
          className="text-sm text-primary hover:underline"
        >
          OpenAPI / Swagger →
        </a>
      </Card>
    </div>
  );
}
