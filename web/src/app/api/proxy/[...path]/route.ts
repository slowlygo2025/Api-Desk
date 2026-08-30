import { getIronSession } from "iron-session";
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";
import { getApiBaseUrl, getSessionOptions, SessionData } from "@/lib/auth/session";

async function handler(request: NextRequest, pathSegments: string[]) {
  const session = await getIronSession<SessionData>(await cookies(), getSessionOptions());
  if (!session.isLoggedIn || !session.apiKey) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  const subPath = pathSegments.join("/").replace(/^v1\//, "");
  const url = new URL(request.url);
  const target = `${getApiBaseUrl()}/v1/${subPath}${url.search}`;

  const headers = new Headers();
  headers.set("X-API-Key", session.apiKey);
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);

  const body =
    request.method !== "GET" && request.method !== "HEAD" ? await request.text() : undefined;

  const upstream = await fetch(target, {
    method: request.method,
    headers,
    body: body || undefined,
    cache: "no-store",
  });

  const responseHeaders = new Headers();
  const rlLimit = upstream.headers.get("X-RateLimit-Limit");
  const rlRemain = upstream.headers.get("X-RateLimit-Remaining");
  const rlPlan = upstream.headers.get("X-RateLimit-Plan");
  if (rlLimit) responseHeaders.set("X-RateLimit-Limit", rlLimit);
  if (rlRemain) responseHeaders.set("X-RateLimit-Remaining", rlRemain);
  if (rlPlan) responseHeaders.set("X-RateLimit-Plan", rlPlan);

  const data = await upstream.arrayBuffer();
  responseHeaders.set("Content-Type", upstream.headers.get("Content-Type") || "application/json");
  return new NextResponse(data, { status: upstream.status, headers: responseHeaders });
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return handler(request, path);
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return handler(request, path);
}

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return handler(request, path);
}

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return handler(request, path);
}

export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return handler(request, path);
}
