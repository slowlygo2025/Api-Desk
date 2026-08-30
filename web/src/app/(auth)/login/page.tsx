"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/badge";
import { Card, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  const [apiKey, setApiKey] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [demoKey, setDemoKey] = useState<string | null>(null);

  async function login() {
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/api/auth/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ apiKey }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || "Login fallido");
      }
      window.location.href = "/";
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error de autenticación");
    } finally {
      setLoading(false);
    }
  }

  async function createDemo() {
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/api/auth/demo", { method: "POST" });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || "No se pudo crear cuenta demo");
      }
      const data = (await res.json()) as { api_key: string };
      setDemoKey(data.api_key);
      setApiKey(data.api_key);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error creando demo");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-primary">Api-Desk</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Panel de whales on-chain. Tu API key se guarda en sesión segura del servidor — nunca en el navegador.
          </p>
        </div>
        <div>
          <CardTitle className="mb-2">API Key</CardTitle>
          <Input
            type="password"
            placeholder="adsk_..."
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && login()}
          />
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        {demoKey && (
          <p className="rounded-md border border-amber-900/50 bg-amber-950/30 p-2 text-xs text-amber-200">
            Key demo creada (cópiala ahora): <code className="break-all">{demoKey}</code>
          </p>
        )}
        <Button className="w-full" disabled={loading || !apiKey} onClick={login}>
          {loading ? "Entrando…" : "Entrar al panel"}
        </Button>
        {process.env.NODE_ENV === "development" && (
          <Button variant="outline" className="w-full" disabled={loading} onClick={createDemo}>
            Crear cuenta demo (dev)
          </Button>
        )}
      </Card>
    </div>
  );
}
