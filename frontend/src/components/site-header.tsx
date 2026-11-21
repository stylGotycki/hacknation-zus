"use client";

import { Baby, Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import type { Citizen } from "@/lib/api";
import { LOGIN_ITEM, NAV_ITEMS } from "@/lib/nav";
import { isRouteActive } from "@/lib/routes";
import { endSession, loadCitizen } from "@/lib/session";
import { cn } from "@/lib/utils";

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [citizen, setCitizen] = useState<Citizen | null>(null);

  // The simulated mObywatel session is kept in the browser and announced with a custom event.
  useEffect(() => {
    const sync = () => setCitizen(loadCitizen());
    sync();
    window.addEventListener("parent-guide:session", sync);
    return () => window.removeEventListener("parent-guide:session", sync);
  }, []);

  // Close the mobile menu after navigating.
  useEffect(() => setOpen(false), [pathname]);

  return (
    <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-4 px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="grid size-8 place-items-center rounded-lg bg-primary text-primary-foreground">
            <Baby className="size-5" />
          </span>
          <span>Przewodnik rodzica</span>
        </Link>

        {/* Desktop navigation */}
        <nav className="ml-auto hidden items-center gap-1 lg:flex" aria-label="Główna nawigacja">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.route}
              href={item.href}
              className={cn(
                "rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground",
                isRouteActive(pathname, item.route) && "bg-accent font-medium text-accent-foreground",
              )}
            >
              {item.label}
            </Link>
          ))}
          {citizen ? (
            <Button size="sm" variant="outline" className="ml-2" onClick={endSession}>
              {citizen.first_name} · Wyloguj
            </Button>
          ) : (
            <Button asChild size="sm" className="ml-2">
              <Link href={LOGIN_ITEM.href}>{LOGIN_ITEM.label}</Link>
            </Button>
          )}
        </nav>

        {/* Mobile toggle */}
        <Button
          variant="ghost"
          size="icon"
          className="ml-auto lg:hidden"
          aria-label={open ? "Zamknij menu" : "Otwórz menu"}
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <X /> : <Menu />}
        </Button>
      </div>

      {/* Mobile navigation */}
      {open && (
        <nav className="border-t px-4 pb-4 pt-2 lg:hidden" aria-label="Nawigacja mobilna">
          <ul className="flex flex-col gap-1">
            {NAV_ITEMS.map((item) => (
              <li key={item.route}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-3 text-base",
                    isRouteActive(pathname, item.route) ? "bg-accent font-medium" : "hover:bg-accent",
                  )}
                >
                  <item.icon className="size-5 text-primary" />
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
          {citizen ? (
            <Button className="mt-3 w-full" size="lg" variant="outline" onClick={endSession}>
              {citizen.first_name} · Wyloguj
            </Button>
          ) : (
            <Button asChild className="mt-3 w-full" size="lg">
              <Link href={LOGIN_ITEM.href}>{LOGIN_ITEM.label}</Link>
            </Button>
          )}
        </nav>
      )}
    </header>
  );
}
