import { NextResponse } from "next/server";
import { getApiBaseUrl } from "@/lib/auth/session";

export async function POST() {
  try {
    const res = await fetch(`${getApiBaseUrl()}/v1/clients`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "demo-panel", plan: "pro" }),
      cache: "no-store",
    });
    if (!res.ok) {
      const detail = await res.text();
      return NextResponse.json({ error: detail || "No se pudo crear cuenta demo" }, { status: 502 });
    }
    const data = (await res.json()) as { api_key: string; id: string; plan: string };
    return NextResponse.json({ api_key: data.api_key, id: data.id, plan: data.plan });
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 502 });
  }
}
