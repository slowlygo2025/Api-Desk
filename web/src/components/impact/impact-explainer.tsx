"use client";

import type { ImpactInfo } from "@/lib/api/types";

const FACTOR_LABELS: Record<string, string> = {
  model: "Modelo",
  direction_bias: "Sesgo direccional",
  size_factor: "Factor de tamaño",
  asset_liquidity_proxy: "Liquidez del asset",
  flow_base: "Impacto base del flujo",
  liq_dampen: "Amortiguación por liquidez",
};

const DIRECTION_LABELS: Record<string, string> = {
  bearish_pressure: "Presión bajista (inflow a exchange)",
  supply_shock_reduction: "Reducción de oferta (outflow)",
  neutral_bias: "Sesgo neutral",
};

export function ImpactExplainer({ impact }: { impact: ImpactInfo }) {
  const details = impact.details ?? {};
  if (!Object.keys(details).length) return null;

  return (
    <div className="mt-2 space-y-1.5 rounded-md bg-muted/30 p-2 text-xs">
      <p className="font-medium text-muted-foreground">Factores del modelo</p>
      {Object.entries(details).map(([key, value]) => (
        <div key={key} className="flex justify-between gap-2">
          <span className="text-muted-foreground">{FACTOR_LABELS[key] ?? key}</span>
          <span className="font-mono">
            {key === "direction_bias"
              ? (DIRECTION_LABELS[String(value)] ?? String(value))
              : typeof value === "number"
                ? value.toFixed(key.includes("factor") || key.includes("proxy") ? 2 : 4)
                : String(value)}
          </span>
        </div>
      ))}
    </div>
  );
}
