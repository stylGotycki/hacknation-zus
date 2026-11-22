import type * as React from "react";

import { cn } from "@/lib/utils";

const controlClass =
  "h-11 w-full rounded-sm border border-input bg-background px-3 text-[15px] outline-none transition-colors focus-visible:border-navy focus-visible:ring-2 focus-visible:ring-navy/30 disabled:opacity-50";

/** Label + control + optional hint, stacked. */
export function Field({
  label,
  hint,
  children,
  className,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <label className={cn("flex flex-col gap-1.5 text-sm", className)}>
      <span className="font-bold">{label}</span>
      {children}
      {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
    </label>
  );
}

export function Input({ className, ...props }: React.ComponentProps<"input">) {
  return <input className={cn(controlClass, className)} {...props} />;
}

export function Select({ className, ...props }: React.ComponentProps<"select">) {
  return <select className={cn(controlClass, className)} {...props} />;
}

export function Checkbox({
  label,
  hint,
  className,
  ...props
}: Omit<React.ComponentProps<"input">, "type"> & { label: string; hint?: string }) {
  return (
    <label className={cn("flex items-start gap-3 rounded-sm border p-3 text-sm", className)}>
      <input type="checkbox" className="mt-0.5 size-4 accent-primary" {...props} />
      <span className="flex flex-col gap-0.5">
        <span className="font-bold">{label}</span>
        {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
      </span>
    </label>
  );
}
