"use client";

import { Card, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ErrorState, LoadingSkeleton } from "@/components/ui/states";
import { useAdminClients } from "@/lib/api/hooks";
import { formatDate } from "@/lib/utils";

export default function AdminPage() {
  const clients = useAdminClients();

  if (clients.isLoading) return <LoadingSkeleton rows={5} />;
  if (clients.isError) {
    return (
      <ErrorState
        title="Admin no disponible"
        message="Requiere plan Institutional (scope admin.ops)."
        onRetry={() => clients.refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Admin</h1>
        <p className="text-sm text-muted-foreground">Gestión de clientes API registrados.</p>
      </div>

      <Card>
        <CardTitle className="mb-4">Clientes ({clients.data?.length ?? 0})</CardTitle>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-border text-xs uppercase text-muted-foreground">
              <tr>
                <th className="py-2">Nombre</th>
                <th className="py-2">Plan</th>
                <th className="py-2">API Key</th>
                <th className="py-2">Estado</th>
                <th className="py-2">Webhook</th>
                <th className="py-2">Creado</th>
              </tr>
            </thead>
            <tbody>
              {(clients.data ?? []).map((c) => (
                <tr key={c.id} className="border-b border-border/50">
                  <td className="py-2 font-medium">{c.name}</td>
                  <td className="py-2 uppercase">{c.plan}</td>
                  <td className="py-2 font-mono text-xs">{c.api_key_prefix}…</td>
                  <td className="py-2">
                    <Badge className={c.is_active ? "border-emerald-900 text-emerald-400" : "border-red-900 text-red-400"}>
                      {c.is_active ? "activo" : "off"}
                    </Badge>
                  </td>
                  <td className="py-2">{c.webhook_configured ? "✓" : "—"}</td>
                  <td className="py-2 text-xs text-muted-foreground">{formatDate(c.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
