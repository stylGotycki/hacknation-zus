"use client";

import { ChevronDown, Home } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { NAV_ITEMS, type NavItem, sideNavItems } from "@/lib/nav";
import { isRouteActive } from "@/lib/routes";
import { cn } from "@/lib/utils";
import { CONTAINER, GUIDE_NAME } from "@/lib/zus-site";

const labelOf = (item: NavItem) => item.sideLabel ?? item.label;

function useCurrentItem(): { pathname: string; current: NavItem | undefined } {
  const pathname = usePathname();
  const current = NAV_ITEMS.find((item) => isRouteActive(pathname, item.route));
  return { pathname, current };
}

/** zus.pl side menu: level 1 = the guide, level 2 = its pages; active item has a green background. */
function SideMenu({ className }: { className?: string }) {
  const { pathname, current } = useCurrentItem();
  const atHome = pathname === "/";
  const item = "block border-b border-border py-[18px] pr-4 text-[15px] leading-snug";

  return (
    <nav aria-label={GUIDE_NAME} className={className}>
      <ul>
        <li>
          <Link
            href="/"
            aria-current={atHome ? "page" : undefined}
            className={cn(item, "pl-5", atHome ? "bg-primary font-bold text-white" : "text-foreground hover:underline")}
          >
            {GUIDE_NAME}
          </Link>
        </li>
        {sideNavItems().map((nav) => {
          const active = current?.route === nav.route;
          return (
            <li key={nav.route}>
              <Link
                href={nav.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  item,
                  "pl-[50px] font-bold",
                  active ? "bg-primary text-white" : "text-link hover:underline",
                )}
              >
                {labelOf(nav)}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

function Breadcrumbs() {
  const { pathname, current } = useCurrentItem();
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [pathname]);

  const sep = <span aria-hidden className="px-2.5 text-foreground">&gt;</span>;
  const last = current ? labelOf(current) : null;

  return (
    <div className="border-y border-band-border bg-muted">
      {/* Desktop: full trail */}
      <nav aria-label="Ścieżka nawigacji" className={cn(CONTAINER, "hidden h-[52px] items-center lg:flex")}>
        <Link href="/" className="flex h-full items-center pr-5 text-link" aria-label={`${GUIDE_NAME} – start`}>
          <Home className="size-6" strokeWidth={1.75} />
        </Link>
        <ol className="flex h-full items-center border-l border-band-border pl-3 text-xs">
          <li className="flex items-center">
            {last ? (
              <>
                <Link href="/" className="hover:underline">
                  {GUIDE_NAME}
                </Link>
                {sep}
                <span className="font-bold" aria-current="page">
                  {last}
                </span>
              </>
            ) : (
              <span className="font-bold" aria-current="page">
                {GUIDE_NAME}
              </span>
            )}
          </li>
        </ol>
      </nav>

      {/* Mobile: collapsed trail that opens the side menu */}
      <div className="lg:hidden">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          className={cn(CONTAINER, "flex h-[58px] items-center justify-between text-left text-xs")}
        >
          <span>
            {GUIDE_NAME} {sep}
            {last ? <span className="font-bold">{last}</span> : "…"}
          </span>
          <ChevronDown className={cn("size-5 text-link transition-transform", open && "rotate-180")} />
        </button>
        {open && <SideMenu className="border-t border-band-border bg-background" />}
      </div>
    </div>
  );
}

/** Breadcrumbs + zus.pl two-column body (side menu with a green rule, content on the right). */
export function GuideFrame({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Breadcrumbs />
      <div className={cn(CONTAINER, "flex flex-1 items-stretch")}>
        <SideMenu className="hidden w-[300px] shrink-0 border-r-[7px] border-primary lg:block" />
        <main id="tresc" className="min-w-0 flex-1 py-8 lg:py-10 lg:pl-[50px]">
          {children}
        </main>
      </div>
    </>
  );
}
