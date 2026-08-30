"use client";

import { useState } from "react";
import { Bookmark, Pause, Play, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/badge";
import {
  deleteFilter,
  loadSavedFilters,
  saveFilter,
  type SavedFilter,
  type WhaleFilters,
} from "@/lib/filters/storage";

interface Props {
  filters: WhaleFilters;
  onApply: (filters: Omit<WhaleFilters, "pauseFeed">) => void;
  onPauseChange: (paused: boolean) => void;
}

export function SavedFiltersBar({ filters, onApply, onPauseChange }: Props) {
  const [saved, setSaved] = useState<SavedFilter[]>(() => loadSavedFilters());
  const [name, setName] = useState("");
  const [showSave, setShowSave] = useState(false);

  function refresh() {
    setSaved(loadSavedFilters());
  }

  function handleSave() {
    if (!name.trim()) return;
    saveFilter(name.trim(), {
      asset: filters.asset,
      chain: filters.chain,
      flowType: filters.flowType,
      minUsd: filters.minUsd,
    });
    setName("");
    setShowSave(false);
    refresh();
  }

  function handleDelete(id: string) {
    deleteFilter(id);
    refresh();
  }

  return (
    <div className="space-y-3 rounded-lg border border-border bg-card/30 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium uppercase text-muted-foreground">Noise gate</span>
        <Button
          variant="outline"
          className="h-7 gap-1 px-2 text-xs"
          onClick={() => onPauseChange(!filters.pauseFeed)}
        >
          {filters.pauseFeed ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
          {filters.pauseFeed ? "Reanudar feed" : "Pausar feed"}
        </Button>
        <Button variant="outline" className="h-7 gap-1 px-2 text-xs" onClick={() => setShowSave(!showSave)}>
          <Bookmark className="h-3 w-3" />
          Guardar filtro
        </Button>
      </div>

      {showSave && (
        <div className="flex gap-2">
          <Input
            placeholder="Nombre del filtro"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="h-8 text-sm"
          />
          <Button className="h-8 px-3 text-xs" disabled={!name.trim()} onClick={handleSave}>
            Guardar
          </Button>
        </div>
      )}

      {saved.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {saved.map((s) => (
            <div
              key={s.id}
              className="flex items-center gap-1 rounded-full border border-border bg-muted/40 px-2 py-0.5 text-xs"
            >
              <button className="hover:text-primary" onClick={() => onApply(s.filters)}>
                {s.name}
              </button>
              <button
                className="text-muted-foreground hover:text-red-400"
                onClick={() => handleDelete(s.id)}
                aria-label={`Eliminar ${s.name}`}
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
