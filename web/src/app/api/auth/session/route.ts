import { getIronSession } from "iron-session";
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";
import { getSessionOptions, SessionData } from "@/lib/auth/session";
import { apiFetch } from "@/lib/api/client";
import type { ClientMe } from "@/lib/api/types";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const apiKey = body.apiKey as string | undefined;
  if (!apiKey?.startsWith("adsk_")) {
    return NextResponse.json({ error: "API key inválida" }, { status: 400 });
  }

  try {
    const me = await apiFetch<ClientMe>("/clients/me", apiKey);
    const session = await getIronSession<SessionData>(await cookies(), getSessionOptions());
    session.apiKey = apiKey;
    session.clientId = me.id;
    session.clientName = me.name;
    session.plan = me.plan;
    session.isLoggedIn = true;
    await session.save();
    return NextResponse.json({
      ok: true,
      client: { id: me.id, name: me.name, plan: me.plan, prefix: me.api_key_prefix },
    });
  } catch {
    return NextResponse.json({ error: "API key rechazada por el servidor" }, { status: 401 });
  }
}

export async function DELETE() {
  const session = await getIronSession<SessionData>(await cookies(), getSessionOptions());
  session.destroy();
  return NextResponse.json({ ok: true });
}
