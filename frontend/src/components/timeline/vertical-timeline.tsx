"use client";

import { ChevronDown } from "lucide-react";
import { useState } from "react";

import type { BenefitResult, Deadline, EvaluationResult, LeavePeriod } from "@/lib/api";
import {
  formatDate,
  formatDaysLeft,
  formatPercent,
  formatPln,
  formatWeeks,
} from "@/lib/format";
import { cn } from "@/lib/utils";

type Lane = "main" | "mother" | "father";

type TimelineEvent = {
  id: string;
  date: string;
  lane: Lane;
  type: "birth" | "start" | "end" | "deadline";
  /** First start of an uninterrupted block / last end: draws the branch and merge connectors. */
  branch?: boolean;
  title: string;
  lines: string[];
  deadline?: Deadline;
  period?: LeavePeriod;
};

// Lane x positions (px) inside the graph column.
const LANE_X: Record<Lane, number> = { main: 14, mother: 42, father: 70 };
const GRAPH_WIDTH = 92;
const DOT_Y = 22; // px from the top of a row to the centre of its dot

const LANE_COLOR: Record<Lane, string> = {
  main: "bg-muted-foreground",
  mother: "bg-primary",
  father: "bg-info",
};
const LANE_BORDER: Record<Lane, string> = {
  main: "border-muted-foreground",
  mother: "border-primary",
  father: "border-info",
};
const LANE_ORDER: Record<Lane, number> = { main: 0, mother: 1, father: 2 };
const PERSON_NAME = { mother: "Mama", father: "Tata", family: "Rodzina" } as const;

const DEADLINE_STYLE = {
  open: { border: "border-navy", text: "text-navy", chip: "bg-muted text-navy" },
  soon: { border: "border-amber-500", text: "text-amber-800", chip: "bg-amber-100 text-amber-900" },
  overdue: { border: "border-destructive", text: "text-destructive", chip: "bg-destructive/10 text-destructive" },
} as const;

function addDays(iso: string, days: number): string {
  const [y, m, d] = iso.split("-").map(Number);
  const date = new Date(y, m - 1, d + days);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function periodLines(p: LeavePeriod): string[] {
  const lines = [
    `${formatWeeks(p.weeks)} · do ${formatDate(p.end)}` + (p.rate !== null ? ` · ${formatPercent(p.rate)} podstawy` : ""),
  ];
  if (p.paid && p.monthly_gross !== null) {
    lines.push(`ok. ${formatPln(p.monthly_gross)} brutto miesięcznie`);
  }
  if (!p.paid) lines.push("Bez zasiłku z ubezpieczenia chorobowego");
  return lines;
}

/** Turns periods and deadlines into one date-ordered list of points, like a commit log. */
export function buildEvents(result: EvaluationResult): TimelineEvent[] {
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
    const periods = result.timeline.filter((p) => p.person === person).sort((a, b) => a.start.localeCompare(b.start));
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
          title: `${PERSON_NAME[person]}: koniec urlopu`,
          lines: [`Ostatni dzień: ${p.label_pl.toLowerCase()}`],
        });
      }
    });
  }

  for (const d of result.deadlines) {
    events.push({
      id: d.code,
      date: d.due,
      lane: "main",
      type: "deadline",
      title: `${d.person === "family" ? "" : `${PERSON_NAME[d.person]}: `}${d.title_pl}`,
      lines: [d.note_pl],
      deadline: d,
    });
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

type Segment = { lane: Lane; from: "top" | "dot"; to: "dot" | "bottom" };

/** Which vertical line pieces cross each row, so the lines look continuous. */
function segmentsPerRow(events: TimelineEvent[]): Segment[][] {
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

function Graph({ event, segments }: { event: TimelineEvent; segments: Segment[] }) {
  const x = LANE_X[event.lane];
  const isDeadline = event.type === "deadline" && event.deadline;
  const style = isDeadline ? DEADLINE_STYLE[event.deadline!.status] : null;
  return (
    <div className="relative shrink-0 self-stretch" style={{ width: GRAPH_WIDTH }} aria-hidden>
      {segments.map((s) => (
        <span
          key={s.lane}
          className={cn("absolute w-0.5 -translate-x-1/2", LANE_COLOR[s.lane], s.lane === "main" && "opacity-40")}
          style={{
            left: LANE_X[s.lane],
            top: s.from === "top" ? 0 : DOT_Y,
            bottom: s.to === "bottom" ? 0 : `calc(100% - ${DOT_Y}px)`,
          }}
        />
      ))}
      {event.branch && event.lane !== "main" && (
        <span
          className={cn("absolute h-0.5", LANE_COLOR[event.lane])}
          style={{ left: LANE_X.main, width: x - LANE_X.main, top: DOT_Y - 1 }}
        />
      )}
      <span
        className={cn(
          "absolute -translate-x-1/2 -translate-y-1/2 rounded-full border-2 bg-background",
          event.type === "birth" ? "size-5 border-primary-dark bg-primary-dark ring-4 ring-secondary" : "size-3.5",
          event.type === "deadline"
            ? style?.border
            : event.type === "birth"
              ? ""
              : cn(LANE_BORDER[event.lane], event.type === "start" && LANE_COLOR[event.lane]),
        )}
        style={{ left: x, top: DOT_Y }}
      />
    </div>
  );
}

const PAYER_LABEL = { employer: "Wypłaca pracodawca", zus: "Wypłaca ZUS", municipality: "Wypłaca gmina" } as const;

function benefitFor(result: EvaluationResult, event: TimelineEvent): BenefitResult | undefined {
  if (event.deadline?.benefit_code) return result.benefits.find((b) => b.code === event.deadline!.benefit_code);
  const p = event.period;
  if (!p) return undefined;
  return result.benefits.find(
    (b) =>
      b.person === p.person &&
      (p.kind === "pregnancy_sickness" ? b.code === "sickness_pregnancy" : b.code.startsWith(p.kind)),
  );
}

function DetailList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{title}</p>
      <ul className="ml-4 list-disc text-sm">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function EventDetails({ result, event }: { result: EvaluationResult; event: TimelineEvent }) {
  const benefit = benefitFor(result, event);
  const p = event.period;
  const d = event.deadline;
  return (
    <div className="mt-2 flex flex-col gap-3 rounded-lg border bg-muted/40 p-3">
      {p && (
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-xs text-muted-foreground">Okres</dt>
            <dd>
              {formatDate(p.start)} – {formatDate(p.end)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Długość</dt>
            <dd>
              {formatWeeks(p.weeks)} ({p.days} dni)
            </dd>
          </div>
          {p.rate !== null && (
            <div>
              <dt className="text-xs text-muted-foreground">Stawka</dt>
              <dd>{formatPercent(p.rate)} podstawy</dd>
            </div>
          )}
          {p.monthly_gross !== null && (
            <div>
              <dt className="text-xs text-muted-foreground">Miesięcznie brutto</dt>
              <dd>{formatPln(p.monthly_gross)}</dd>
            </div>
          )}
          {p.total_gross !== null && (
            <div>
              <dt className="text-xs text-muted-foreground">Za cały okres brutto</dt>
              <dd>{formatPln(p.total_gross)}</dd>
            </div>
          )}
          {p.total_net_estimate !== null && (
            <div>
              <dt className="text-xs text-muted-foreground">Za cały okres netto (szac.)</dt>
              <dd>{formatPln(p.total_net_estimate)}</dd>
            </div>
          )}
          {p.work_fraction > 0 && (
            <div>
              <dt className="text-xs text-muted-foreground">Praca w trakcie urlopu</dt>
              <dd>{formatPercent(p.work_fraction)} etatu</dd>
            </div>
          )}
        </dl>
      )}
      {d && (
        <p className="text-sm">
          <span className="font-medium">Termin: {formatDate(d.due)}.</span> {d.note_pl}
        </p>
      )}
      {benefit && (
        <>
          <p className="text-sm">
            <span className="font-medium">{benefit.title_pl}.</span> {benefit.summary_pl}
          </p>
          {benefit.payer && <p className="text-sm text-muted-foreground">{PAYER_LABEL[benefit.payer]}</p>}
          {benefit.apply_to_pl && (
            <p className="text-sm">
              <span className="font-medium">Gdzie złożyć: </span>
              {benefit.apply_to_pl}
            </p>
          )}
          {benefit.deadline && (
            <p className="text-sm">
              <span className="font-medium">Wniosek do: </span>
              {formatDate(benefit.deadline)}
              {benefit.days_left !== null && ` (${formatDaysLeft(benefit.days_left)})`}
              {benefit.deadline_note_pl && ` – ${benefit.deadline_note_pl}`}
            </p>
          )}
          <DetailList title="Dokumenty" items={benefit.documents_pl} />
          <DetailList title="Dlaczego" items={benefit.reasons_pl} />
          {benefit.legal_basis.length > 0 && (
            <p className="text-xs text-muted-foreground">Podstawa prawna: {benefit.legal_basis.join("; ")}</p>
          )}
        </>
      )}
      {!benefit && !p && !d && <p className="text-sm text-muted-foreground">Brak dodatkowych szczegółów.</p>}
    </div>
  );
}

export function VerticalTimeline({ result }: { result: EvaluationResult }) {
  const [openId, setOpenId] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "mother" | "father">("all");
  const hasFather = result.timeline.some((p) => p.person === "father");
  const events = buildEvents(result).filter(
    (e) =>
      filter === "all" ||
      e.type === "birth" ||
      e.lane === filter ||
      (e.deadline && (e.deadline.person === filter || e.deadline.person === "family")),
  );
  const rows = segmentsPerRow(events);

  return (
    <div className="flex flex-col gap-4">
      {hasFather && (
        <div role="group" aria-label="Pokaż oś czasu dla" className="flex gap-2">
          {(["all", "mother", "father"] as const).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setFilter(value)}
              aria-pressed={filter === value}
              className={cn(
                "rounded-full border px-3 py-1 text-sm transition-colors",
                filter === value ? "border-primary bg-primary text-primary-foreground" : "hover:bg-muted",
              )}
            >
              {value === "all" ? "Oboje" : value === "mother" ? "Mama" : "Tata"}
            </button>
          ))}
        </div>
      )}
      <ul className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted-foreground" aria-label="Legenda osi czasu">
        <li className="flex items-center gap-2">
          <span className="size-3 rounded-full bg-primary" /> Mama
        </li>
        {hasFather && (
          <li className="flex items-center gap-2">
            <span className="size-3 rounded-full bg-info" /> Tata
          </li>
        )}
        <li className="flex items-center gap-2">
          <span className="size-3 rounded-full border-2 border-navy bg-background" /> Termin
        </li>
        <li className="flex items-center gap-2">
          <span className="size-3 rounded-full border-2 border-primary bg-background" /> Koniec urlopu
        </li>
      </ul>

      <ol>
        {events.map((event, i) => {
          const deadline = event.deadline;
          const style = deadline ? DEADLINE_STYLE[deadline.status] : null;
          return (
            <li key={event.id} className="flex gap-3">
              <Graph event={event} segments={rows[i]} />
              <div className="min-w-0 flex-1 pb-5 pt-3">
                <p className="text-xs text-muted-foreground">{formatDate(event.date)}</p>
                <p className={cn("font-medium leading-snug", event.type === "birth" && "text-primary-dark")}>
                  {event.title}
                </p>
                {event.lines.map((line) => (
                  <p key={line} className="text-sm text-muted-foreground">
                    {line}
                  </p>
                ))}
                {deadline && style && (
                  <p className={cn("mt-1 mr-2 inline-block rounded-md px-2 py-0.5 text-xs font-medium", style.chip)}>
                    {formatDaysLeft(deadline.days_left)}
                  </p>
                )}
                {(event.period || event.deadline) && (
                  <button
                    type="button"
                    onClick={() => setOpenId(openId === event.id ? null : event.id)}
                    aria-expanded={openId === event.id}
                    className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-primary underline-offset-4 hover:underline"
                  >
                    {openId === event.id ? "Ukryj szczegóły" : "Szczegóły"}
                    <ChevronDown className={cn("size-3.5 transition-transform", openId === event.id && "rotate-180")} />
                  </button>
                )}
                {openId === event.id && <EventDetails result={result} event={event} />}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
