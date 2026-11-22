"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Status = "checking" | "ok" | "down";

/** Small indicator proving the frontend → nginx → backend → database chain works. */
export function ApiStatus({ inverse = false }: { inverse?: boolean }) {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    api<{ status: string }>("/health")
      .then((r) => setStatus(r.status === "ok" ? "ok" : "down"))
      .catch(() => setStatus("down"));
  }, []);

  const label = { checking: "sprawdzam API…", ok: "API działa", down: "API niedostępne" }[status];

  return (
    <span className="inline-flex items-center gap-2">
      <span
        className={cn(
          "size-2 rounded-full",
          status === "ok" && (inverse ? "bg-white" : "bg-primary"),
          status === "down" && "bg-destructive",
          status === "checking" && (inverse ? "bg-white/60" : "bg-muted-foreground") + " animate-pulse",
        )}
      />
      {label}
    </span>
  );
}
