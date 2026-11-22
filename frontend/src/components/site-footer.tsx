import { ChevronRight, Mail, Phone } from "lucide-react";
import Link from "next/link";

import { ApiStatus } from "@/components/api-status";
import { PUBLIC_PATHS } from "@/lib/routes";
import { cn } from "@/lib/utils";
import { CONTAINER, GUIDE_NAME, ZUS_CONTACT } from "@/lib/zus-site";

const LINKS: { label: string; href: string; external?: boolean }[] = [
  {
    label: "Zasiłek macierzyński na zus.pl",
    href: "https://www.zus.pl/swiadczenia/zasilki/zasilek-macierzynski",
    external: true,
  },
  {
    label: "Wzory formularzy – zasiłek macierzyński",
    href: "https://www.zus.pl/wzory-formularzy/zasilki/zasilek-macierzynski",
    external: true,
  },
  {
    label: "Urlop rodzicielski – gov.pl",
    href: "https://www.gov.pl/web/rodzina/urlop-rodzicielski",
    external: true,
  },
  {
    label: "Świadczenie rodzicielskie – gov.pl",
    href: "https://www.gov.pl/web/rodzina/wiadczenie-rodzicielskie",
    external: true,
  },
  {
    label: "Rodzicielstwo – Państwowa Inspekcja Pracy",
    href: "https://www.pip.gov.pl/dla-pracodawcow/porady-prawne/rodzicielstwo",
    external: true,
  },
  { label: "Wejście do dema aplikacji", href: PUBLIC_PATHS.login },
  { label: "Pomoc i wsparcie", href: PUBLIC_PATHS.help },
  { label: "Panel administratora", href: PUBLIC_PATHS.admin },
];

/** Green zus.pl footer: white links with a chevron, contact channels for parents. */
export function SiteFooter() {
  return (
    <footer className="mt-12 bg-primary text-white">
      <div className={cn(CONTAINER, "grid gap-8 py-10 md:grid-cols-[2fr_1fr]")}>
        <ul className="grid gap-x-8 gap-y-1 sm:grid-cols-2">
          {LINKS.map((link) => (
            <li key={link.label}>
              {link.external ? (
                <a
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 py-1.5 text-[15px] font-bold hover:underline"
                >
                  <ChevronRight className="size-4 shrink-0" /> {link.label}
                </a>
              ) : (
                <Link
                  href={link.href}
                  className="flex items-center gap-2 py-1.5 text-[15px] font-bold hover:underline"
                >
                  <ChevronRight className="size-4 shrink-0" /> {link.label}
                </Link>
              )}
            </li>
          ))}
        </ul>
        <div className="flex flex-col gap-2 text-[15px]">
          <p className="font-bold">Pytania o zasiłki dla rodziców</p>
          <a
            href={`mailto:${ZUS_CONTACT.email}`}
            className="flex items-center gap-2 hover:underline"
          >
            <Mail className="size-4" /> {ZUS_CONTACT.email}
          </a>
          <a
            href={ZUS_CONTACT.phoneHref}
            className="flex items-center gap-2 hover:underline"
          >
            <Phone className="size-4" /> {ZUS_CONTACT.phone}
          </a>
        </div>
      </div>
      <div className="border-t border-white/25">
        <div
          className={cn(
            CONTAINER,
            "flex flex-col gap-2 py-4 text-xs sm:flex-row sm:items-center sm:justify-between",
          )}
        >
          <p>
            {GUIDE_NAME} — wersja demonstracyjna, projekt HackNation 2026. Nie
            jest serwisem ZUS. AI użyto wyłącznie przy tworzeniu kodu.
          </p>
          <ApiStatus inverse />
        </div>
      </div>
    </footer>
  );
}
