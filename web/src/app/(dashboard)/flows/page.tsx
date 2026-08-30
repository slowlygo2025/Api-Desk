"use client";

import { SankeyFlowChart } from "@/components/flows/sankey-flow-chart";

export default function FlowsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Flujos on-chain</h1>
        <p className="text-sm text-muted-foreground">
          Mapa Sankey agregado: rutas from → to por volumen USD (ventana 24h).
        </p>
      </div>
      <SankeyFlowChart window="24h" />
    </div>
  );
}
