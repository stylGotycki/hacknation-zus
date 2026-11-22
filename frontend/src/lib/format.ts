/** Formatting helpers for Polish UI text. */

const pln = new Intl.NumberFormat("pl-PL", {
  style: "currency",
  currency: "PLN",
});
const dateFmt = new Intl.DateTimeFormat("pl-PL", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

export const formatPln = (value: number | null | undefined) =>
  value === null || value === undefined ? "–" : pln.format(value);

/** ISO date (YYYY-MM-DD) -> "10 lis 2026". Parsed as local date to avoid timezone shifts. */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "–";
  const [y, m, d] = iso.split("-").map(Number);
  return dateFmt.format(new Date(y, m - 1, d));
}

export const formatPercent = (rate: number | null | undefined) =>
  rate === null || rate === undefined
    ? "–"
    : `${(rate * 100).toLocaleString("pl-PL", { maximumFractionDigits: 1 })}%`;

export function formatWeeks(weeks: number | null | undefined): string {
  if (weeks === null || weeks === undefined) return "–";
  const rounded = Math.round(weeks * 10) / 10;
  return `${rounded.toLocaleString("pl-PL")} tyg.`;
}

export const toIsoDate = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

/** "Zostało 12 dni", "Zostanie 1 dzień", "Dziś ostatni dzień", "Termin minął 3 dni temu". */
export function formatDaysLeft(days: number): string {
  const plural = (n: number, one: string, few: string, many: string) => {
    if (n === 1) return one;
    const lastTwo = n % 100;
    const last = n % 10;
    return last >= 2 && last <= 4 && !(lastTwo >= 12 && lastTwo <= 14)
      ? few
      : many;
  };
  if (days === 0) return "Dziś ostatni dzień";
  if (days < 0) {
    const n = -days;
    return `Termin minął ${n} ${plural(n, "dzień", "dni", "dni")} temu`;
  }
  if (days > 730) return `Zostało ok. ${Math.round(days / 365)} lat`;
  if (days > 90) {
    const months = Math.round(days / 30);
    return `Zostało ok. ${months} ${plural(months, "miesiąc", "miesiące", "miesięcy")}`;
  }
  const verb =
    days === 1 ? "Został" : plural(days, "Został", "Zostały", "Zostało");
  return `${verb} ${days} ${plural(days, "dzień", "dni", "dni")}`;
}
