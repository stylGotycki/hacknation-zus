import {
  Calculator,
  FileText,
  GitBranch,
  type LucideIcon,
  Settings,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

import { PUBLIC_PATHS, type RouteName } from "@/lib/routes";

export type NavItem = {
  /** English route name (folder in `src/app`); see `lib/routes.ts`. */
  route: RouteName;
  /** Public URL (Polish) – what <Link> uses. */
  href: string;
  label: string;
  description: string;
  icon: LucideIcon;
  /** Backlog epic that fills this page – shown on placeholders. */
  epic: string;
};

/** Single source of truth for navigation: header, mobile menu and home page tiles. */
export const NAV_ITEMS: NavItem[] = [
  {
    route: "wizard",
    href: PUBLIC_PATHS.wizard,
    label: "Sprawdź uprawnienia",
    description: "Odpowiedz na kilka pytań i zobacz, jakie świadczenia Ci przysługują.",
    icon: Sparkles,
    epic: "E4",
  },
  {
    route: "calculator",
    href: PUBLIC_PATHS.calculator,
    label: "Kalkulator",
    description: "Policz wysokość zasiłku macierzyńskiego i długość urlopów.",
    icon: Calculator,
    epic: "E2",
  },
  {
    route: "timeline",
    href: PUBLIC_PATHS.timeline,
    label: "Oś czasu",
    description: "Zobacz plan urlopów mamy i taty na jednej osi.",
    icon: GitBranch,
    epic: "E5",
  },
  {
    route: "applications",
    href: PUBLIC_PATHS.applications,
    label: "Wnioski",
    description: "Wypełnij wnioski krok po kroku i wróć do zapisanych wersji roboczych.",
    icon: FileText,
    epic: "E6",
  },
  {
    route: "examples",
    href: PUBLIC_PATHS.examples,
    label: "Przykłady",
    description: "Prawdziwe sytuacje rodzin na podstawie spraw ZUS.",
    icon: Users,
    epic: "E3",
  },
  {
    route: "zus",
    href: PUBLIC_PATHS.zus,
    label: "Dane z ZUS",
    description: "Ubezpieczenie, zadłużenie, e-ZLA i pytanie do PUE (symulacja po zalogowaniu).",
    icon: ShieldCheck,
    epic: "E7",
  },
  {
    route: "admin",
    href: PUBLIC_PATHS.admin,
    label: "Admin",
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
