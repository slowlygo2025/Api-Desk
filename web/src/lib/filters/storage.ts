export interface WhaleFilters {
  asset: string;
  chain: string;
  flowType: string;
  minUsd: string;
  pauseFeed: boolean;
}

export interface SavedFilter {
  id: string;
  name: string;
  filters: Omit<WhaleFilters, "pauseFeed">;
  createdAt: string;
}

const STORAGE_KEY = "apidesk_saved_filters";

export function loadSavedFilters(): SavedFilter[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as SavedFilter[]) : [];
  } catch {
    return [];
  }
}

export function persistSavedFilters(filters: SavedFilter[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(filters));
}

export function saveFilter(name: string, filters: Omit<WhaleFilters, "pauseFeed">): SavedFilter {
  const entry: SavedFilter = {
    id: crypto.randomUUID(),
    name,
    filters,
    createdAt: new Date().toISOString(),
  };
  const all = [...loadSavedFilters(), entry];
  persistSavedFilters(all);
  return entry;
}

export function deleteFilter(id: string) {
  persistSavedFilters(loadSavedFilters().filter((f) => f.id !== id));
}

export const DEFAULT_FILTERS: WhaleFilters = {
  asset: "",
  chain: "",
  flowType: "",
  minUsd: "",
  pauseFeed: false,
};
