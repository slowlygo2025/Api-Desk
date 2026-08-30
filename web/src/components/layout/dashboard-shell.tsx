"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  Bell,
  GitBranch,
  LayoutDashboard,
  LogOut,
  Server,
  Settings,
  Shield,
  TrendingUp,
  Waves,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useMe } from "@/lib/api/hooks";
import { useFeedSocket } from "@/lib/ws/useFeedSocket";
import { useInvalidateWhales } from "@/lib/api/hooks";

const NAV_BASE = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/whales", label: "Whales", icon: Waves },
  { href: "/market", label: "Market", icon: TrendingUp },
  { href: "/alerts", label: "Alertas", icon: Bell },
  { href: "/settings", label: "Ajustes", icon: Settings },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { data: me } = useMe();
  const invalidate = useInvalidateWhales();
  const { connected } = useFeedSocket((evt) => {
    if (evt.event === "whale.detected" || evt.event === "market.analysis") {
      invalidate();
    }
  });

  const nav = [...NAV_BASE];
  if (me?.scopes.includes("stats.flows")) {
    nav.splice(3, 0, { href: "/flows", label: "Flujos", icon: GitBranch });
  }
  if (me?.scopes.includes("admin.ops")) {
    nav.push({ href: "/ops", label: "Ops", icon: Server });
    nav.push({ href: "/admin", label: "Admin", icon: Shield });
  }

  async function logout() {
    await fetch("/api/auth/session", { method: "DELETE" });
    router.push("/login");
    router.refresh();
  }

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-56 shrink-0 flex-col border-r border-border bg-card/50 p-4 md:flex">
        <div className="mb-8">
          <p className="text-lg font-bold tracking-tight text-primary">Api-Desk</p>
          <p className="text-xs text-muted-foreground">Whales on-chain · Panel</p>
        </div>
        <nav className="flex flex-1 flex-col gap-1">
          {nav.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                pathname === href || (href !== "/" && pathname.startsWith(href))
                  ? "bg-muted text-foreground"
                  : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="mt-auto space-y-2 border-t border-border pt-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Activity className={cn("h-3 w-3", connected ? "text-emerald-400" : "text-amber-400")} />
            {connected ? "Feed en vivo" : "Reconectando…"}
          </div>
          {me && (
            <p className="text-xs text-muted-foreground">
              {me.name} · <span className="uppercase">{me.plan}</span>
            </p>
          )}
          <Button variant="ghost" className="w-full justify-start gap-2 px-2" onClick={logout}>
            <LogOut className="h-4 w-4" />
            Salir
          </Button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-4 md:p-6">{children}</main>
    </div>
  );
}
