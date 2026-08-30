"use client";

import { AlertCircle, Inbox, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function EmptyState({
  title,
  description,
  action,
  className,
}: {
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-dashed border-border px-6 py-12 text-center",
        className,
      )}
    >
      <Inbox className="mb-3 h-10 w-10 text-muted-foreground/60" />
      <p className="font-medium">{title}</p>
      {description && <p className="mt-1 max-w-sm text-sm text-muted-foreground">{description}</p>}
      {action && (
        <Button variant="outline" className="mt-4 h-8 text-xs" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}

export function ErrorState({
  title = "Error al cargar",
  message,
  onRetry,
  className,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-red-900/40 bg-red-950/20 px-6 py-10 text-center",
        className,
      )}
    >
      <AlertCircle className="mb-3 h-10 w-10 text-red-400/80" />
      <p className="font-medium text-red-200">{title}</p>
      {message && <p className="mt-1 max-w-md text-sm text-red-300/80">{message}</p>}
      {onRetry && (
        <Button variant="outline" className="mt-4 h-8 gap-1 text-xs" onClick={onRetry}>
          <RefreshCw className="h-3 w-3" />
          Reintentar
        </Button>
      )}
    </div>
  );
}

export function LoadingSkeleton({ rows = 5, className }: { rows?: number; className?: string }) {
  return (
    <div className={cn("space-y-2", className)}>
      {[...Array(rows)].map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  );
}

export function TableSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("overflow-hidden rounded-lg border border-border", className)}>
      <Skeleton className="h-10 rounded-none" />
      <LoadingSkeleton rows={6} className="p-2" />
    </div>
  );
}
