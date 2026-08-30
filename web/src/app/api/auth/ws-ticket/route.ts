import { getIronSession } from "iron-session";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { getSessionOptions, SessionData } from "@/lib/auth/session";
import { apiFetch } from "@/lib/api/client";

export async function GET() {
  const session = await getIronSession<SessionData>(await cookies(), getSessionOptions());
  if (!session.isLoggedIn || !session.apiKey) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  try {
    const ticket = await apiFetch<{ ticket: string; expires_in: number }>(
      "/auth/ws-ticket",
      session.apiKey,
      { method: "POST" },
    );
    return NextResponse.json(ticket);
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 502 });
  }
}
