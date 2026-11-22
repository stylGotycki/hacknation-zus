import type {
  ApplicationRecord,
  Deadline,
  EvaluationResult,
  LeavePeriod,
} from "@/lib/api";
import {
  formatDate,
  formatPercent,
  formatPln,
  formatWeeks,
} from "@/lib/format";
import { Lane, Segment, TimelineEvent } from "@/components/timeline/model";
import { LANE_ORDER, PERSON_NAME } from "@/components/timeline/style";
import { STATUS_LABEL } from "@/components/timeline/event-details";

export const MONTH_NAME = [
  "styczeń",
  "luty",
  "marzec",
  "kwiecień",
  "maj",
  "czerwiec",
  "lipiec",
  "sierpień",
  "wrzesień",
  "październik",
  "listopad",
  "grudzień",
];

export function addDays(iso: string, days: number): string {
  const [y, m, d] = iso.split("-").map(Number);
  const date = new Date(y, m - 1, d + days);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

export function periodLines(p: LeavePeriod): string[] {
  const lines = [
    `${formatWeeks(p.weeks)} · do ${formatDate(p.end)}` +
      (p.rate !== null ? ` · ${formatPercent(p.rate)} podstawy` : ""),
  ];
  if (p.paid && p.monthly_gross !== null) {
    lines.push(`ok. ${formatPln(p.monthly_gross)} brutto miesięcznie`);
  }
  if (p.raised_to_minimum) {
    lines.push(
      "Zasiłek podwyższony do kwoty świadczenia rodzicielskiego (miesięcznie)",
    );
  }
  if (!p.paid) lines.push("Bez zasiłku z ubezpieczenia chorobowego");
  return lines;
}

/** The filed application that fulfils a deadline (same rule, same parent). */
export function fulfilledBy(
  d: Deadline,
  applications: ApplicationRecord[],
): ApplicationRecord | undefined {
  return applications.find(
    (a) =>
      a.created_at &&
      a.fulfils.includes(d.code) &&
      (a.person === null || d.person === "family" || a.person === d.person) &&
      // The 81,5% rate needs the statement about the full leave (ZAM, załącznik 6 pkt 15).
      (d.code !== "t_usredniona" || Boolean(a.data.full_leave)),
  );
}

/** Turns periods and deadlines into one date-ordered list of points, like a commit log. */
export function buildEvents(
  result: EvaluationResult,
  applications: ApplicationRecord[] = [],
  showPayments = true,
): TimelineEvent[] {
  const events: TimelineEvent[] = [];
  events.push({
    id: "birth",
    date: result.event_date,
    lane: "main",
    type: "birth",
    title:
      result.situation === "birth"
        ? result.event_is_estimate
          ? "Przewidywany termin porodu"
          : "Narodziny dziecka"
        : "Dziecko trafia do rodziny",
    lines: [],
  });

  for (const person of ["mother", "father"] as const) {
    const periods = result.timeline
      .filter((p) => p.person === person)
      .sort((a, b) => a.start.localeCompare(b.start));
    periods.forEach((p, i) => {
      const prev = periods[i - 1];
      const next = periods[i + 1];
      const startsBlock = !prev || p.start > addDays(prev.end, 1);
      const endsBlock = !next || next.start > addDays(p.end, 1);
      events.push({
        id: `${p.id}-start`,
        date: p.start,
        lane: person,
        type: "start",
        branch: startsBlock,
        title: `${PERSON_NAME[person]}: ${p.label_pl}`,
        lines: periodLines(p),
        period: p,
      });
      if (endsBlock) {
        events.push({
          id: `${p.id}-end`,
          date: p.end,
          lane: person,
          type: "end",
          branch: true,
          title: `${PERSON_NAME[person]}: koniec urlopu, powrót do pracy`,
          lines: [`Ostatni dzień: ${p.label_pl.toLowerCase()}`],
          period: p,
        });
      }
    });
  }

  const used = new Set<number>();
  for (const d of result.deadlines) {
    const who = d.person === "family" ? "" : `${PERSON_NAME[d.person]}: `;
    const filed = d.kind === "apply" ? fulfilledBy(d, applications) : undefined;
    if (filed) {
      // The filed application replaces the deadline point on the axis.
      used.add(filed.id);
      const on = filed.created_at!.slice(0, 10);
      events.push({
        id: `application-${filed.id}-${d.code}`,
        date: on,
        lane: "main",
        type: "application",
        title: `${who}złożono: ${filed.title_pl}`,
        lines: [
          // Once the case is decided the deadline no longer matters, so it is not shown.
          filed.status === "decided"
            ? `Status: ${STATUS_LABEL[filed.status]}`
            : `Status: ${STATUS_LABEL[filed.status]} · termin był do ${formatDate(d.due)}` +
              (on > d.due ? " (złożony po terminie)" : ""),
        ],
        application: filed,
        deadline: d,
      });
      continue;
    }
    events.push({
      id: d.code,
      date: d.due,
      lane: "main",
      type: "deadline",
      title: `${who}${d.title_pl}`,
      lines: [d.note_pl],
      deadline: d,
    });
  }

  for (const a of applications) {
    if (!a.created_at || used.has(a.id)) continue;
    events.push({
      id: `application-${a.id}`,
      date: a.created_at.slice(0, 10),
      lane: "main",
      type: "application",
      title: `Złożono: ${a.title_pl}`,
      lines: [`Status: ${STATUS_LABEL[a.status]}`],
      application: a,
    });
  }

  if (showPayments) {
    for (const pay of result.payments ?? []) {
      events.push({
        id: `payment-${pay.id}`,
        date: pay.date,
        lane: "main",
        type: "payment",
        title: `${PERSON_NAME[pay.person]}: przelew zasiłku ${formatPln(pay.amount_gross)} brutto`,
        lines: [
          `Za ${MONTH_NAME[Number(pay.month.slice(5)) - 1]} ${pay.month.slice(0, 4)} · ${pay.days} dni`,
        ],
        payment: pay,
      });
    }
  }

  return events
    .map((event, seq) => ({ event, seq }))
    .sort(
      (a, b) =>
        a.event.date.localeCompare(b.event.date) ||
        LANE_ORDER[a.event.lane] - LANE_ORDER[b.event.lane] ||
        a.seq - b.seq,
    )
    .map(({ event }) => event);
}

/** Which vertical line pieces cross each row, so the lines look continuous. */
export function segmentsPerRow(events: TimelineEvent[]): Segment[][] {
  const rows: Segment[][] = events.map(() => []);
  const addRange = (lane: Lane, first: number, last: number) => {
    for (let i = first; i <= last; i++) {
      rows[i].push({
        lane,
        from: i === first ? "dot" : "top",
        to: i === last ? "dot" : "bottom",
      });
    }
  };
  addRange("main", 0, events.length - 1);
  for (const lane of ["mother", "father"] as const) {
    let open: number | null = null;
    events.forEach((e, i) => {
      if (e.lane !== lane) return;
      if (e.type === "start" && e.branch && open === null) open = i;
      if (e.type === "end" && open !== null) {
        addRange(lane, open, i);
        open = null;
      }
    });
  }
  return rows;
}
