"use client";

import { useEffect, useRef, useState } from "react";

type FeedEvent = {
  event: string;
  data?: unknown;
  channel?: string;
};

export function useFeedSocket(onEvent?: (evt: FeedEvent) => void) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    let cancelled = false;

    async function connect() {
      if (cancelled) return;
      try {
        const res = await fetch("/api/auth/ws-ticket");
        let url = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/v1/ws/feed";
        if (res.ok) {
          const { ticket } = (await res.json()) as { ticket: string };
          url += `${url.includes("?") ? "&" : "?"}ticket=${encodeURIComponent(ticket)}`;
        }
        const ws = new WebSocket(url);
        wsRef.current = ws;
        ws.onopen = () => {
          setConnected(true);
          retriesRef.current = 0;
        };
        ws.onclose = () => {
          setConnected(false);
          wsRef.current = null;
          if (!cancelled) {
            const delay = Math.min(30_000, 1000 * 2 ** retriesRef.current);
            retriesRef.current += 1;
            timerRef.current = setTimeout(connect, delay);
          }
        };
        ws.onmessage = (msg) => {
          try {
            const parsed = JSON.parse(msg.data as string) as FeedEvent;
            onEventRef.current?.(parsed);
          } catch {
            /* ignore */
          }
        };
      } catch {
        timerRef.current = setTimeout(connect, 5000);
      }
    }

    connect();
    return () => {
      cancelled = true;
      if (timerRef.current) clearTimeout(timerRef.current);
      wsRef.current?.close();
    };
  }, []);

  return { connected };
}
