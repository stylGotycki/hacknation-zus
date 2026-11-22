"use client";

import { ChevronRight, Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { AccessibilityToggles } from "@/components/zus/accessibility-toggles";
import { SiteSearch } from "@/components/zus/site-search";
import type { Citizen } from "@/lib/api";
import { LOGIN_ITEM, sideNavItems } from "@/lib/nav";
import { isRouteActive, PUBLIC_PATHS } from "@/lib/routes";
import { endSession, loadCitizen } from "@/lib/session";
import { cn } from "@/lib/utils";
import { CONTAINER, GUIDE_NAME } from "@/lib/zus-site";

function DemoBanner() {
  return (
    <div className="bg-navy text-white">
      <p className={cn(CONTAINER, "py-1.5 text-center text-xs sm:text-sm")}>
        Wersja demonstracyjna — projekt HackNation 2026, nie jest serwisem ZUS. Dane i logowanie są symulowane.
      </p>
    </div>
  );
}

function Logo() {
  return (
    <Link href="/" className="flex shrink-0 items-center gap-4" aria-label={`${GUIDE_NAME} – strona główna`}>
      {/* Official file goes to public/brand/logo-zus.svg (a neutral placeholder ships with the repo). */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/brand/logo-zus.svg" alt="ZUS" className="h-[40px] w-auto sm:h-[46px] lg:h-[57px]" />
      <span className="hidden border-l-2 border-primary pl-4 text-[20px] font-bold leading-tight text-primary sm:block xl:text-[24px]">
        {GUIDE_NAME}
      </span>
    </Link>
  );
}

/** Outlined navy button ("Zarejestruj w PUE/eZUS" on zus.pl) and orange one ("Zaloguj do PUE/eZUS"). */
const navyOutline =
  "inline-flex h-11 items-center gap-2 whitespace-nowrap rounded-sm border border-navy bg-white px-3 text-sm font-bold text-navy hover:bg-navy hover:text-white";
const orangeSolid =
  "inline-flex h-11 items-center gap-2 whitespace-nowrap rounded-sm border border-[#e0a243] bg-orange px-3 text-sm font-bold text-navy hover:brightness-95";

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

  useEffect(() => setOpen(false), [pathname]);

  const loginButton = citizen ? (
    <button type="button" className={orangeSolid} onClick={endSession}>
      {citizen.first_name} · Wyloguj <ChevronRight className="size-4" />
    </button>
  ) : (
    <Link href={LOGIN_ITEM.href} className={orangeSolid}>
      Zaloguj przez mObywatel <ChevronRight className="size-4" />
    </Link>
  );

  return (
    <header className="bg-background">
      <a
        href="#tresc"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:bg-white focus:p-2"
      >
        Przejdź do treści
      </a>
      <DemoBanner />

      <div className={cn(CONTAINER, "flex h-[84px] items-center gap-5 lg:h-[100px]")}>
        <Logo />

        {/* Desktop utility row */}
        <div className="ml-auto hidden items-center gap-4 lg:flex">
          <Link href={`${PUBLIC_PATHS.help}#kontakt`} className="hidden text-sm hover:underline xl:inline">
            Kontakt
          </Link>
          <AccessibilityToggles />
          <Link href={PUBLIC_PATHS.zus} className={navyOutline}>
            Dane z ZUS <ChevronRight className="size-4" />
          </Link>
          {loginButton}
          <SiteSearch />
        </div>

        {/* Mobile: search + menu */}
        <div className="ml-auto flex items-center gap-5 lg:hidden">
          <SiteSearch />
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls="mobile-menu"
            className="flex flex-col items-center gap-1 text-sm font-bold text-link"
          >
            {open ? <X className="size-9" strokeWidth={1.75} /> : <Menu className="size-9" strokeWidth={1.75} />}
            Menu
          </button>
        </div>
      </div>

      {/* Grey bar under the header, as on zus.pl */}
      <div className={CONTAINER}>
        <div className="h-1.5 bg-grey-bar" />
      </div>

      {/* Mobile menu */}
      {open && (
        <nav id="mobile-menu" aria-label="Menu" className="border-b border-band-border lg:hidden">
          <div className={cn(CONTAINER, "flex flex-col gap-4 py-4")}>
            <div className="flex flex-col gap-2">
              {loginButton}
              <Link href={PUBLIC_PATHS.zus} className={navyOutline}>
                Dane z ZUS <ChevronRight className="size-4" />
              </Link>
            </div>
            <ul>
              {sideNavItems().map((item) => (
                <li key={item.route} className="border-b border-border">
                  <Link
                    href={item.href}
                    className={cn(
                      "flex items-center justify-between py-3 font-bold",
                      isRouteActive(pathname, item.route) ? "text-foreground" : "text-link",
                    )}
                  >
                    {item.sideLabel ?? item.label} <ChevronRight className="size-4" />
                  </Link>
                </li>
              ))}
            </ul>
            <div className="flex items-center justify-between">
              <Link href={`${PUBLIC_PATHS.help}#kontakt`} className="text-sm">
                Kontakt
              </Link>
              <AccessibilityToggles />
            </div>
          </div>
        </nav>
      )}
    </header>
  );
}
