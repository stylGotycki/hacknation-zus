import { fulfilledBy } from "@/components/timeline/events";
import type {
  ApplicationRecord,
  Deadline,
  EvaluationResult,
  LeavePeriod,
  Payment,
} from "@/lib/api";
import { formatDate, formatDaysLeft, formatPln, toIsoDate } from "@/lib/format";
import { PUBLIC_PATHS } from "@/lib/routes";

export type PeriodState = "done" | "now" | "planned" | "unpaid";

export type PeriodRow = {
  period: LeavePeriod;
  state: PeriodState;
  /** Days of the period that have already passed (today included). */
  used: number;
  left: number;
  /** Last day to use this kind of leave, when the rules give one. */
  useBy: Deadline | null;
};

export type Todo = {
  tone: "late" | "soon" | "info";
  title: string;
  text: string;
  href?: string;
};

export const WHO = {
  mother: "Mama",
  father: "Tata",
  family: "Rodzina",
} as const;

const MS_DAY = 86_400_000;
const toUtc = (iso: string) => {
  const [y, m, d] = iso.split("-").map(Number);
  return Date.UTC(y, m - 1, d);
};
export const dayDiff = (from: string, to: string) =>
  Math.round((toUtc(to) - toUtc(from)) / MS_DAY);

export const todayIso = () => toIsoDate(new Date());

/** Which use-by deadline caps which kind of leave. */
const USE_BY: Partial<Record<LeavePeriod["kind"], string>> = {
  parental: "t_rodzicielski_do",
  paternity: "t_ojcowski_do",
};

export function periodRows(
  result: EvaluationResult,
  today: string,
): PeriodRow[] {
  return result.timeline.map((period) => {
    const total = period.days;
    const used =
      today < period.start
        ? 0
        : today > period.end
          ? total
          : dayDiff(period.start, today) + 1;
    const state: PeriodState = !period.paid
      ? "unpaid"
      : today > period.end
        ? "done"
        : today >= period.start
          ? "now"
          : "planned";
    const code = USE_BY[period.kind];
    return {
      period,
      state,
      used,
      left: Math.max(0, total - used),
      useBy: code
        ? (result.deadlines.find((d) => d.code === code) ?? null)
        : null,
    };
  });
}

export type PaymentSummary = {
  received: number;
  expected: number;
  next: Payment | null;
  receivedCount: number;
};

export function paymentSummary(
  result: EvaluationResult,
  today: string,
): PaymentSummary {
  const payments = [...(result.payments ?? [])].sort((a, b) =>
    a.date.localeCompare(b.date),
  );
  const past = payments.filter((p) => p.date <= today);
  const future = payments.filter((p) => p.date > today);
  const sum = (list: Payment[]) =>
    list.reduce((acc, p) => acc + p.amount_gross, 0);
  return {
    received: sum(past),
    expected: sum(future),
    next: future[0] ?? null,
    receivedCount: past.length,
  };
}

const STATUS_PL = {
  submitted: "złożony",
  in_progress: "w rozpatrzeniu",
  decided: "rozpatrzony",
} as const;

/** What to do next: missed deadlines first, then the nearest open ones, then what is pending. */
export function whatNow(
  result: EvaluationResult,
  applications: ApplicationRecord[],
  today: string,
  loggedIn: boolean,
): Todo[] {
  const apply = result.deadlines.filter(
    (d) => d.kind === "apply" && !fulfilledBy(d, applications),
  );
  const who = (d: Deadline) =>
    d.person === "family" ? "" : `${WHO[d.person]}: `;
  const late: Todo[] = apply
    .filter((d) => d.status === "overdue")
    .map((d) => ({
      tone: "late" as const,
      title: `${who(d)}${d.title_pl} – termin minął ${formatDate(d.due)}`,
      text: d.late_pl || d.note_pl,
      href: loggedIn ? PUBLIC_PATHS.applications : undefined,
    }));
  const open: Todo[] = apply
    .filter((d) => d.status !== "overdue")
    .sort((a, b) => a.due.localeCompare(b.due))
    .slice(0, 3)
    .map((d) => ({
      tone: d.status === "soon" ? ("soon" as const) : ("info" as const),
      title: `${who(d)}${d.title_pl} – do ${formatDate(d.due)}`,
      text: `${formatDaysLeft(d.days_left)}. ${d.note_pl}`,
      href: loggedIn ? PUBLIC_PATHS.applications : undefined,
    }));
  const pending: Todo[] = applications
    .filter((a) => a.status !== "decided")
    .map((a) => ({
      tone: "info" as const,
      title: `${a.title_pl} – ${STATUS_PL[a.status]}`,
      text:
        a.status === "submitted"
          ? "Poczekaj na przyjęcie wniosku do rozpatrzenia."
          : "Wniosek jest rozpatrywany – nic więcej nie musisz robić.",
      href: PUBLIC_PATHS.applications,
    }));
  const rows = periodRows(result, today);
  const running = rows.filter((r) => r.state === "now");
  const going: Todo[] = running.map((r) => ({
    tone: "info" as const,
    title: `Trwa: ${WHO[r.period.person]} – ${r.period.label_pl}`,
    text: `Do ${formatDate(r.period.end)}, zostało ${r.left} dni.`,
  }));
  const next = rows
    .filter((r) => r.state === "planned")
    .sort((a, b) => a.period.start.localeCompare(b.period.start))[0];
  const upcoming: Todo[] = next
    ? [
        {
          tone: "info",
          title: `Najbliższy urlop: ${WHO[next.period.person]} – ${next.period.label_pl}`,
          text: `Od ${formatDate(next.period.start)} (za ${dayDiff(today, next.period.start)} dni).`,
        },
      ]
    : [];
  const pay = paymentSummary(result, today).next;
  const payment: Todo[] = pay
    ? [
        {
          tone: "info",
          title: `Najbliższy przelew: ${formatPln(pay.amount_gross)} brutto`,
          text: `${WHO[pay.person]}, ${formatDate(pay.date)} (założenie planera – termin wypłaty zależy od płatnika).`,
        },
      ]
    : [];
  return [
    ...late,
    ...open,
    ...pending,
    ...going,
    ...upcoming,
    ...payment,
  ].slice(0, 8);
}
