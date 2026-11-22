"use client";

import { Search, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { sideNavItems } from "@/lib/nav";
import { cn } from "@/lib/utils";

const normalize = (s: string) =>
  s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ł/g, "l");

/** "Szukaj" from the zus.pl header: searches the pages of the guide. */
export function SiteSearch({ className }: { className?: string }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const pathname = usePathname();

  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    if (open) input.current?.focus();
  }, [open]);

  const results = useMemo(() => {
    const q = normalize(query.trim());
    const items = sideNavItems();
    if (!q) return items;
    return items.filter((item) =>
      normalize(
        `${item.label} ${item.sideLabel ?? ""} ${item.description}`,
      ).includes(q),
    );
  }, [query]);

  return (
    <div className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex flex-col items-center gap-1 text-sm text-link"
      >
        <span className="grid size-10 place-items-center rounded-full border-2 border-link">
          <Search className="size-5" strokeWidth={2.5} />
        </span>
        Szukaj
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-[min(22rem,calc(100vw-2rem))] border border-band-border bg-background p-3 shadow-lg">
          <div className="flex items-center gap-2 border-b border-border pb-2">
            <Search className="size-4 text-icon" />
            <input
              ref={input}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Czego szukasz? np. urlop ojcowski"
              aria-label="Szukaj w przewodniku"
              className="min-w-0 flex-1 bg-transparent py-1 text-sm outline-none"
            />
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Zamknij wyszukiwanie"
            >
              <X className="size-4" />
            </button>
          </div>
          <ul className="mt-1 max-h-80 overflow-auto">
            {results.map((item) => (
              <li
                key={item.route}
                className="border-b border-border last:border-0"
              >
                <Link
                  href={item.href}
                  className="block py-2.5 text-sm hover:bg-muted"
                >
                  <span className="font-bold text-link">
                    {item.sideLabel ?? item.label}
                  </span>
                  <span className="block text-xs text-muted-foreground">
                    {item.description}
                  </span>
                </Link>
              </li>
            ))}
            {results.length === 0 && (
              <li className="py-3 text-sm text-muted-foreground">
                Brak wyników.
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
