import { getApiBaseUrl } from "@/lib/auth/session";

export async function apiFetch<T>(
  path: string,
  apiKey: string,
  init: RequestInit = {},
): Promise<T> {
  const base = getApiBaseUrl();
  const url = `${base}/v1${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey,
      ...(init.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function proxyFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const proxyPath = `/api/proxy${path.startsWith("/") ? path : `/${path}`}`;
  return fetch(proxyPath, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
    credentials: "include",
  });
}

export async function proxyJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await proxyFetch(path, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}
