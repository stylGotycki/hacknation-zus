"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Status = "checking" | "ok" | "down";

/** Small indicator proving the frontend → nginx → backend → database chain works. */
export function ApiStatus() {
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
          status === "ok" && "bg-primary",
          status === "down" && "bg-destructive",
          status === "checking" && "bg-muted-foreground animate-pulse",
        )}
      />
      {label}
    </span>
  );
}
