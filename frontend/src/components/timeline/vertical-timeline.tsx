"use client";

import {
  Baby,
  BriefcaseBusiness,
  ChevronDown,
  ChevronRight,
  FileCheck2,
  FileText,
  Heart,
  Hospital,
  Hourglass,
  type LucideIcon,
  Stethoscope,
  UserRound,
  Users,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import type {
  ApplicationRecord,
  ApplicationStatus,
  BenefitResult,
  Deadline,
  EvaluationResult,
  LeavePeriod,
  Suggestion,
} from "@/lib/api";
import { PUBLIC_PATHS } from "@/lib/routes";
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
  type: "birth" | "start" | "end" | "deadline" | "application";
  /** First start of an uninterrupted block / last end: draws the branch and merge connectors. */
  branch?: boolean;
  title: string;
  lines: string[];
  deadline?: Deadline;
  period?: LeavePeriod;
  application?: ApplicationRecord;
};

/** Extra data for the details panel: forms to file and applications already filed. */
export type TimelineExtras = { suggestions: Suggestion[]; applications: ApplicationRecord[] };

// Lane x positions (px) inside the graph column.
const LANE_X: Record<Lane, number> = { main: 20, mother: 60, father: 100 };
const GRAPH_WIDTH = 122;
const DOT_Y = 30; // px from the top of a row to the centre of its dot
const LINE = 5; // line thickness (px)

const LANE_COLOR: Record<Lane, string> = {
  main: "bg-[#c9c9c9]",
  mother: "bg-primary",
  father: "bg-info",
};
const LANE_TEXT: Record<Lane, string> = {
  main: "text-muted-foreground",
  mother: "text-primary",
  father: "text-info",
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
  soon: { border: "border-amber-600", text: "text-amber-700", chip: "bg-amber-100 text-amber-900" },
  overdue: { border: "border-destructive", text: "text-destructive", chip: "bg-destructive/10 text-destructive" },
} as const;

const KIND_ICON: Record<LeavePeriod["kind"], LucideIcon> = {
  pregnancy_sickness: Stethoscope,
  maternity: Heart,
  maternity_equivalent: BriefcaseBusiness,
  supplementary: Hospital,
  parental: Users,
  paternity: UserRound,
};

/** Every kind of event has its own icon inside the dot. */
function iconFor(event: TimelineEvent): LucideIcon {
  switch (event.type) {
    case "birth":
      return Baby;
    case "end":
      return BriefcaseBusiness; // back to work
    case "application":
      return FileCheck2;
    case "deadline":
      return event.deadline?.kind === "use_by" ? Hourglass : FileText;
    default:
      return event.period?.work_fraction ? BriefcaseBusiness : KIND_ICON[event.period!.kind];
  }
}

const STATUS_LABEL: Record<ApplicationStatus, string> = {
  submitted: "złożony",
  in_progress: "w rozpatrzeniu",
  decided: "rozpatrzony",
};
const RECIPIENT = { employer: "pracodawcy", zus: "ZUS", registry: "urzędu stanu cywilnego" } as const;

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
export function buildEvents(result: EvaluationResult, applications: ApplicationRecord[] = []): TimelineEvent[] {
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
          title: `${PERSON_NAME[person]}: koniec urlopu, powrót do pracy`,
          lines: [`Ostatni dzień: ${p.label_pl.toLowerCase()}`],
          period: p,
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

  for (const a of applications) {
    if (!a.created_at) continue;
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

function Graph({
  event,
  segments,
  open,
  onToggle,
}: {
  event: TimelineEvent;
  segments: Segment[];
  open: boolean;
  onToggle: () => void;
}) {
  const x = LANE_X[event.lane];
  const style = event.type === "deadline" && event.deadline ? DEADLINE_STYLE[event.deadline.status] : null;
  const Icon = iconFor(event);
  const filled = event.type === "start" || event.type === "birth";
  const size = event.type === "birth" ? 44 : 36;
  return (
    <div className="relative shrink-0 self-stretch" style={{ width: GRAPH_WIDTH }}>
      {segments.map((s) => (
        <span
          key={s.lane}
          aria-hidden
          className={cn("absolute -translate-x-1/2 rounded-full", LANE_COLOR[s.lane])}
          style={{
            width: LINE,
            left: LANE_X[s.lane],
            top: s.from === "top" ? 0 : DOT_Y,
            bottom: s.to === "bottom" ? 0 : `calc(100% - ${DOT_Y}px)`,
          }}
        />
      ))}
      {event.branch && event.lane !== "main" && (
        <span
          aria-hidden
          className={cn("absolute rounded-full", LANE_COLOR[event.lane])}
          style={{ left: LANE_X.main, width: x - LANE_X.main, top: DOT_Y - LINE / 2, height: LINE }}
        />
      )}
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        aria-label={`${open ? "Ukryj" : "Pokaż"} szczegóły: ${event.title}`}
        title="Szczegóły"
        className={cn(
          "absolute z-10 grid -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border-[3px] transition-transform hover:scale-110",
          event.type === "birth"
            ? "border-primary-dark bg-primary-dark text-white ring-4 ring-secondary"
            : style
              ? cn("bg-background", style.border, style.text)
              : filled
                ? cn(LANE_BORDER[event.lane], LANE_COLOR[event.lane], "text-white")
                : cn(LANE_BORDER[event.lane], "bg-background", LANE_TEXT[event.lane]),
          event.type === "application" && "border-navy bg-background text-navy",
          open && "ring-4 ring-orange",
        )}
        style={{ left: x, top: DOT_Y, width: size, height: size }}
      >
        <Icon className={event.type === "birth" ? "size-6" : "size-[18px]"} strokeWidth={2.25} />
      </button>
    </div>
  );
}

const PAYER_LABEL = { employer: "Wypłaca pracodawca", zus: "Wypłaca ZUS" } as const;

function benefitFor(result: EvaluationResult, event: TimelineEvent): BenefitResult | undefined {
  if (event.deadline?.benefit_code) return result.benefits.find((b) => b.code === event.deadline!.benefit_code);
  const p = event.period;
  if (!p) return undefined;
  return result.benefits.find((b) => p.rule !== null && b.periods.includes(p.rule));
}

function DetailList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">{title}</p>
      <ul className="ml-4 list-disc text-sm">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

/** Leave kind behind an event (from its period or from the benefit of its deadline). */
function kindOf(event: TimelineEvent): string | null {
  if (event.period) return event.period.kind;
  const code = event.deadline?.benefit_code ?? "";
  const prefixes: [string, string][] = [
    ["macierzynski", "maternity"],
    ["uzupelniajacy", "supplementary"],
    ["rodzicielski", "parental"],
    ["ojcowski", "paternity"],
  ];
  return prefixes.find(([prefix]) => code.startsWith(prefix))?.[1] ?? null;
}

/** The form a parent files for this event: a leave request to the employer or ZAM to ZUS. */
function suggestionFor(event: TimelineEvent, extras: TimelineExtras): Suggestion | undefined {
  const kind = kindOf(event);
  const person = event.period?.person ?? event.deadline?.person;
  if (!kind || (person !== "mother" && person !== "father")) return undefined;
  const mine = extras.suggestions.filter((s) => s.person === person);
  return mine.find((s) => s.form_code === `leave_${kind}`) ?? mine.find((s) => !s.form_code.startsWith("leave_"));
}

function ApplicationHistory({ application }: { application: ApplicationRecord }) {
  return (
    <ol className="ml-1 flex flex-col gap-1 border-l-[3px] border-navy pl-3 text-sm">
      {application.history.map((h) => (
        <li key={h.at + h.status}>
          <span className="text-xs text-muted-foreground">{formatDate(h.at.slice(0, 10))}</span> · {h.note}
        </li>
      ))}
    </ol>
  );
}

function ApplicationBox({ event, extras }: { event: TimelineEvent; extras: TimelineExtras }) {
  if (event.application) {
    const a = event.application;
    return (
      <section className="flex flex-col gap-2 border-l-[5px] border-navy bg-background p-3">
        <p className="font-bold">{a.title_pl}</p>
        <p className="text-sm">
          Złożony do {RECIPIENT[a.submitted_to ?? "employer"]} · status: <b>{STATUS_LABEL[a.status]}</b>
        </p>
        <ApplicationHistory application={a} />
        <Link href={PUBLIC_PATHS.applications} className="inline-flex items-center gap-1 text-sm font-bold text-link hover:underline">
          Przejdź do wniosków <ChevronRight className="size-4" />
        </Link>
      </section>
    );
  }
  const suggestion = suggestionFor(event, extras);
  if (!suggestion) return null;
  const filed = extras.applications.find((a) => a.form_code === suggestion.form_code);
  return (
    <section className="flex flex-col gap-2 border-l-[5px] border-navy bg-background p-3">
      <p className="text-xs font-bold uppercase tracking-wide text-navy">Wniosek</p>
      <p className="font-bold">{suggestion.title_pl}</p>
      <p className="text-sm">
        Składasz do {RECIPIENT[suggestion.submitted_to]}
        {suggestion.deadline && (
          <>
            {" "}
            · termin: <b>{formatDate(suggestion.deadline)}</b>
            {suggestion.days_left !== null && ` (${formatDaysLeft(suggestion.days_left)})`}
          </>
        )}
      </p>
      {filed ? (
        <>
          <p className="text-sm">
            Złożony {filed.created_at ? formatDate(filed.created_at.slice(0, 10)) : ""} · status:{" "}
            <b>{STATUS_LABEL[filed.status]}</b>
          </p>
          <ApplicationHistory application={filed} />
        </>
      ) : (
        <Link
          href={`${PUBLIC_PATHS.applications}?form=${suggestion.form_code}`}
          className="inline-flex h-10 w-fit items-center gap-2 rounded-sm bg-primary px-4 text-sm font-bold text-white hover:bg-primary-dark"
        >
          Wypełnij wniosek <ChevronRight className="size-4" />
        </Link>
      )}
    </section>
  );
}

function EventDetails({
  result,
  event,
  extras,
}: {
  result: EvaluationResult;
  event: TimelineEvent;
  extras: TimelineExtras;
}) {
  const benefit = benefitFor(result, event);
  const p = event.period;
  const d = event.deadline;
  return (
    <div className="mt-2 flex flex-col gap-3 border border-border bg-muted p-3">
      <ApplicationBox event={event} extras={extras} />
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
      {!benefit && !p && !d && !event.application && (
        <p className="text-sm text-muted-foreground">Brak dodatkowych szczegółów.</p>
      )}
    </div>
  );
}

export function VerticalTimeline({
  result,
  extras = { suggestions: [], applications: [] },
}: {
  result: EvaluationResult;
  extras?: TimelineExtras;
}) {
  const [openId, setOpenId] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "mother" | "father">("all");
  const hasFather = result.timeline.some((p) => p.person === "father");
  const events = buildEvents(result, extras.applications).filter(
    (e) =>
      filter === "all" ||
      e.type === "birth" ||
      e.type === "application" ||
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
                "rounded-sm border px-4 py-1.5 text-sm font-bold transition-colors",
                filter === value ? "border-primary bg-primary text-primary-foreground" : "border-navy text-navy hover:bg-muted",
              )}
            >
              {value === "all" ? "Oboje" : value === "mother" ? "Mama" : "Tata"}
            </button>
          ))}
        </div>
      )}
      <ul className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted-foreground" aria-label="Legenda osi czasu">
        <li className="flex items-center gap-2">
          <span className="h-1.5 w-6 rounded-full bg-primary" /> Mama
        </li>
        {hasFather && (
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-6 rounded-full bg-info" /> Tata
          </li>
        )}
        {(
          [
            [Heart, "Macierzyński"],
            [Hospital, "Uzupełniający"],
            [Users, "Rodzicielski"],
            [UserRound, "Ojcowski"],
            [BriefcaseBusiness, "Praca / powrót"],
            [FileText, "Termin wniosku"],
            [Hourglass, "Wykorzystaj do"],
            [FileCheck2, "Złożony wniosek"],
          ] as const
        ).map(([Icon, label]) => (
          <li key={label} className="flex items-center gap-1.5">
            <Icon className="size-4 text-icon" /> {label}
          </li>
        ))}
      </ul>
      <p className="text-sm text-muted-foreground">Kliknij kropkę, aby zobaczyć szczegóły urlopu i wniosku.</p>

      <ol>
        {events.map((event, i) => {
          const deadline = event.deadline;
          const style = deadline ? DEADLINE_STYLE[deadline.status] : null;
          return (
            <li key={event.id} className="flex gap-2">
              <Graph
                event={event}
                segments={rows[i]}
                open={openId === event.id}
                onToggle={() => setOpenId(openId === event.id ? null : event.id)}
              />
              <div className="min-w-0 flex-1 pb-6 pt-3">
                <p className="text-xs text-muted-foreground">{formatDate(event.date)}</p>
                <p className={cn("font-bold leading-snug", event.type === "birth" && "text-primary-dark")}>
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
                {(event.period || event.deadline || event.application) && (
                  <button
                    type="button"
                    onClick={() => setOpenId(openId === event.id ? null : event.id)}
                    aria-expanded={openId === event.id}
                    className="mt-1 inline-flex items-center gap-1 text-xs font-bold text-link underline-offset-4 hover:underline"
                  >
                    {openId === event.id ? "Ukryj szczegóły" : "Szczegóły"}
                    <ChevronDown className={cn("size-3.5 transition-transform", openId === event.id && "rotate-180")} />
                  </button>
                )}
                {openId === event.id && <EventDetails result={result} event={event} extras={extras} />}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
