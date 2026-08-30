import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatUsd(value: number): string {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${value.toFixed(0)}`;
}

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "short",
    timeStyle: "medium",
  }).format(new Date(iso));
}

export function riskColor(level: string): string {
  switch (level) {
    case "high":
      return "text-red-400 bg-red-950/50 border-red-900";
    case "medium":
      return "text-amber-400 bg-amber-950/50 border-amber-900";
    default:
      return "text-emerald-400 bg-emerald-950/50 border-emerald-900";
  }
}

export function explorerTxUrl(chain: string, txHash: string): string {
  const c = chain.toLowerCase();
  const map: Record<string, string> = {
    bitcoin: `https://mempool.space/tx/${txHash}`,
    ethereum: `https://etherscan.io/tx/${txHash}`,
    bsc: `https://bscscan.com/tx/${txHash}`,
    polygon: `https://polygonscan.com/tx/${txHash}`,
    arbitrum: `https://arbiscan.io/tx/${txHash}`,
    optimism: `https://optimistic.etherscan.io/tx/${txHash}`,
    base: `https://basescan.org/tx/${txHash}`,
    avalanche: `https://snowtrace.io/tx/${txHash}`,
    tron: `https://tronscan.org/#/transaction/${txHash}`,
    solana: `https://solscan.io/tx/${txHash}`,
  };
  return map[c] ?? `#${txHash}`;
}
