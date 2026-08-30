"use client";

import { useState } from "react";
import { Input } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Drawer } from "@/components/ui/drawer";
import { ErrorState, TableSkeleton } from "@/components/ui/states";
import { SavedFiltersBar } from "@/components/whales/saved-filters-bar";
import { WhaleDrawerContent } from "@/components/whales/whale-drawer";
import { WhaleTable } from "@/components/whales/whale-table";
import { DEFAULT_FILTERS, type WhaleFilters } from "@/lib/filters/storage";
import { useWhales } from "@/lib/api/hooks";

export default function WhalesPage() {
  const [filters, setFilters] = useState<WhaleFilters>(DEFAULT_FILTERS);
  const [cursor, setCursor] = useState<string | undefined>();
  const [cursors, setCursors] = useState<string[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const whales = useWhales(
    {
      asset: filters.asset || undefined,
      chain: filters.chain || undefined,
      flow_type: filters.flowType || undefined,
      min_usd: filters.minUsd ? Number(filters.minUsd) : undefined,
      cursor,
      limit: 50,
    },
    { pauseFeed: filters.pauseFeed },
  );

  function nextPage() {
    if (whales.data?.next_cursor) {
      setCursors((c) => [...c, cursor ?? ""]);
      setCursor(whales.data!.next_cursor!);
    }
  }

  function prevPage() {
    const prev = [...cursors];
    const last = prev.pop();
    setCursors(prev);
    setCursor(last || undefined);
  }

  function applySaved(f: Omit<WhaleFilters, "pauseFeed">) {
    setFilters((prev) => ({ ...prev, ...f }));
    setCursor(undefined);
    setCursors([]);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Whales</h1>
        <p className="text-sm text-muted-foreground">
          Feed on-chain en tiempo real. Clic en fila abre drawer · filtros guardados abajo.
        </p>
      </div>

      <SavedFiltersBar
        filters={filters}
        onApply={applySaved}
        onPauseChange={(paused) => setFilters((f) => ({ ...f, pauseFeed: paused }))}
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Input
          placeholder="Asset (BTC, USDT…)"
          value={filters.asset}
          onChange={(e) => setFilters((f) => ({ ...f, asset: e.target.value }))}
        />
        <Input
          placeholder="Chain (ethereum…)"
          value={filters.chain}
          onChange={(e) => setFilters((f) => ({ ...f, chain: e.target.value }))}
        />
        <Input
          placeholder="Flow type"
          value={filters.flowType}
          onChange={(e) => setFilters((f) => ({ ...f, flowType: e.target.value }))}
        />
        <Input
          placeholder="Min USD"
          type="number"
          value={filters.minUsd}
          onChange={(e) => setFilters((f) => ({ ...f, minUsd: e.target.value }))}
        />
      </div>

      {filters.pauseFeed && (
        <p className="rounded-md border border-amber-900/40 bg-amber-950/20 px-3 py-2 text-sm text-amber-200">
          Feed pausado — no se actualiza vía WS ni polling.
        </p>
      )}

      {whales.isLoading && <TableSkeleton />}
      {whales.isError && (
        <ErrorState message={String(whales.error)} onRetry={() => whales.refetch()} />
      )}
      {whales.data && (
        <WhaleTable items={whales.data.items} onSelect={setSelectedId} selectedId={selectedId ?? undefined} />
      )}

      <div className="flex gap-2">
        <Button variant="outline" disabled={!cursors.length} onClick={prevPage}>
          Anterior
        </Button>
        <Button variant="outline" disabled={!whales.data?.next_cursor} onClick={nextPage}>
          Siguiente
        </Button>
        <span className="self-center text-sm text-muted-foreground">
          {whales.data?.count ?? 0} en página
        </span>
      </div>

      <Drawer open={!!selectedId} onClose={() => setSelectedId(null)} title="Detalle whale">
        {selectedId && <WhaleDrawerContent whaleId={selectedId} />}
      </Drawer>
    </div>
  );
}
