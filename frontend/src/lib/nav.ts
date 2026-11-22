import {
  Calculator,
  FileText,
  GitBranch,
  HeartHandshake,
  type LucideIcon,
  Settings,
  ShieldCheck,
  Users,
  WalletCards,
} from "lucide-react";

import { PUBLIC_PATHS, type RouteName } from "@/lib/routes";

export type NavItem = {
  /** English route name (folder in `src/app`); see `lib/routes.ts`. */
  route: RouteName;
  /** Public URL (Polish) – what <Link> uses. */
  href: string;
  label: string;
  /** Label in the zus.pl side menu and breadcrumb (falls back to `label`). */
  sideLabel?: string;
  description: string;
  icon: LucideIcon;
  /** Backlog epic that fills this page – shown on placeholders. */
  epic: string;
};

/** Items shown in the citizen side menu (admin lives in the footer). */
export const sideNavItems = () =>
  NAV_ITEMS.filter((item) => item.route !== "admin");

/** Single source of truth for navigation: header, mobile menu and home page tiles. */
export const NAV_ITEMS: NavItem[] = [
  {
    route: "calculator",
    href: PUBLIC_PATHS.calculator,
    label: "Sprawdź uprawnienia",
    sideLabel: "Sprawdź uprawnienia i policz zasiłek",
    description:
      "Odpowiedz krok po kroku na pytania o dziecko, rodzinę i pracę – zobacz świadczenia, kwoty, urlopy i terminy.",
    icon: Calculator,
    epic: "E2",
  },
  {
    route: "timeline",
    href: PUBLIC_PATHS.timeline,
    label: "Oś czasu",
    sideLabel: "Plan urlopów – oś czasu",
    description: "Zobacz plan urlopów mamy i taty na jednej osi.",
    icon: GitBranch,
    epic: "E5",
  },
  {
    route: "account",
    href: PUBLIC_PATHS.account,
    label: "Moje urlopy i zasiłki",
    description:
      "Co wykorzystano, ile zostało i do kiedy – oraz co zrobić teraz.",
    icon: WalletCards,
    epic: "E10",
  },
  {
    route: "applications",
    href: PUBLIC_PATHS.applications,
    label: "Wnioski",
    description:
      "Wypełnij wnioski krok po kroku i wróć do zapisanych wersji roboczych.",
    icon: FileText,
    epic: "E6",
  },
  {
    route: "zus",
    href: PUBLIC_PATHS.zus,
    label: "Dane z ZUS",
    description:
      "Ubezpieczenie, zadłużenie, e-ZLA i pytanie do PUE (symulacja po zalogowaniu).",
    icon: ShieldCheck,
    epic: "E7",
  },
  {
    route: "help",
    href: PUBLIC_PATHS.help,
    label: "Pomoc i wsparcie",
    description:
      "Oficjalne informacje, organizacje wspierające rodziców i odpis aktu urodzenia.",
    icon: HeartHandshake,
    epic: "E9",
  },
  {
    route: "admin",
    href: PUBLIC_PATHS.admin,
    label: "Admin",
    sideLabel: "Panel administratora",
    description: "Parametry prawne i obieg wniosków.",
    icon: Settings,
    epic: "E8",
  },
];

export const LOGIN_ITEM = {
  route: "login",
  href: PUBLIC_PATHS.login,
  label: "Zaloguj przez mObywatel",
  epic: "E7",
} as const;
