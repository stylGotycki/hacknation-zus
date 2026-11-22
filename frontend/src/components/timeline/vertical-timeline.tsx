"use client";

import {
  ArrowRight,
  Banknote,
  BriefcaseBusiness,
  ChevronDown,
  FileCheck2,
  FileText,
  Heart,
  Hospital,
  Hourglass,
  UserRound,
  Users,
} from "lucide-react";
import { Fragment, useState } from "react";
import type { EvaluationResult } from "@/lib/api";
import { formatDate, formatDaysLeft } from "@/lib/format";
import { cn } from "@/lib/utils";
import { Lane, TimelineExtras } from "@/components/timeline/model";
import {
  DEADLINE_STYLE,
  GRAPH_WIDTH,
  LANE_COLOR,
  LANE_X,
  LINE,
  TODAY,
} from "@/components/timeline/style";
import { buildEvents, segmentsPerRow } from "@/components/timeline/events";
import { Graph } from "@/components/timeline/graph";
import { EventDetails } from "@/components/timeline/event-details";
import { AdvicePanel } from "@/components/timeline/advice-panel";

/** Horizontal "today" line across the timeline; lane lines keep running through it. */
export function TodayMarker({ lanes }: { lanes: Lane[] }) {
  return (
    <li aria-label={`Dziś, ${formatDate(TODAY)}`} className="flex h-9 gap-2">
      <div
        className="relative shrink-0 self-stretch"
        style={{ width: GRAPH_WIDTH }}
      >
        {lanes.map((lane) => (
          <span
            key={lane}
            aria-hidden
            className={cn(
              "absolute inset-y-0 -translate-x-1/2 rounded-full",
              LANE_COLOR[lane],
            )}
            style={{ width: LINE, left: LANE_X[lane] }}
          />
        ))}
        <ArrowRight
          aria-hidden
          className="absolute top-1/2 z-10 size-6 -translate-y-1/2 text-[#d9780f]"
          strokeWidth={3}
          style={{ left: GRAPH_WIDTH - 26 }}
        />
      </div>
      <div className="relative flex min-w-0 flex-1 items-center">
        <span aria-hidden className="h-[3px] w-full bg-[#d9780f]" />
        <span
          className="absolute left-0 -translate-y-1/2 rounded-sm bg-[#d9780f] px-2 py-0.5 text-xs font-bold text-white"
          style={{ top: "50%" }}
        >
          Dziś · {formatDate(TODAY)}
        </span>
      </div>
    </li>
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
  const [showPayments, setShowPayments] = useState(true);
  const hasFather = result.timeline.some((p) => p.person === "father");
  const events = buildEvents(result, extras.applications, showPayments).filter(
    (e) =>
      filter === "all" ||
      (e.payment && e.payment.person === filter) ||
      e.type === "birth" ||
      e.type === "application" ||
      (e.type !== "payment" && e.lane === filter) ||
      (e.deadline &&
        (e.deadline.person === filter || e.deadline.person === "family")),
  );
  const rows = segmentsPerRow(events);
  // First event after today: the "today" line is drawn right above it.
  const firstFuture = events.findIndex((e) => e.date > TODAY);
  const todayAt = firstFuture === -1 ? events.length : firstFuture;
  const todayLanes: Lane[] =
    todayAt > 0 && todayAt < events.length
      ? rows[todayAt].filter((seg) => seg.from === "top").map((seg) => seg.lane)
      : [];

  return (
    <div className="flex flex-col gap-4">
      <AdvicePanel result={result} extras={extras} />
      {hasFather && (
        <div
          role="group"
          aria-label="Pokaż oś czasu dla"
          className="flex gap-2"
        >
          {(["all", "mother", "father"] as const).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setFilter(value)}
              aria-pressed={filter === value}
              className={cn(
                "rounded-sm border px-4 py-1.5 text-sm font-bold transition-colors",
                filter === value
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-navy text-navy hover:bg-muted",
              )}
            >
              {value === "all" ? "Oboje" : value === "mother" ? "Mama" : "Tata"}
            </button>
          ))}
        </div>
      )}
      <ul
        className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted-foreground"
        aria-label="Legenda osi czasu"
      >
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
            [Banknote, "Przelew zasiłku"],
          ] as const
        ).map(([Icon, label]) => (
          <li key={label} className="flex items-center gap-1.5">
            <Icon className="size-4 text-icon" /> {label}
          </li>
        ))}
      </ul>
      <label className="flex w-fit cursor-pointer items-center gap-2 text-sm">
        <input
          type="checkbox"
          className="size-4 accent-primary"
          checked={showPayments}
          onChange={(e) => setShowPayments(e.target.checked)}
        />
        Pokaż miesięczne przelewy zasiłku
      </label>
      <p className="text-sm text-muted-foreground">
        Kliknij kropkę, aby zobaczyć szczegóły urlopu, wniosku albo przelewu.
      </p>

      <ol>
        {events.map((event, i) => {
          const deadline = event.deadline;
          const style =
            deadline && event.type === "deadline"
              ? DEADLINE_STYLE[deadline.status]
              : null;
          const past = event.date <= TODAY;
          return (
            <Fragment key={event.id}>
              {i === todayAt && <TodayMarker lanes={todayLanes} />}
              <li className="flex gap-2">
                <Graph
                  event={event}
                  segments={rows[i]}
                  open={openId === event.id}
                  onToggle={() =>
                    setOpenId(openId === event.id ? null : event.id)
                  }
                />
                <div
                  className={cn(
                    "min-w-0 flex-1 pb-6 pt-3",
                    past && "opacity-60",
                  )}
                >
                  <p className="text-xs text-muted-foreground">
                    {formatDate(event.date)}
                  </p>
                  <p
                    className={cn(
                      "font-bold leading-snug",
                      event.type === "birth" && "text-primary-dark",
                    )}
                  >
                    {event.title}
                  </p>
                  {event.lines.map((line) => (
                    <p key={line} className="text-sm text-muted-foreground">
                      {line}
                    </p>
                  ))}
                  {deadline && style && (
                    <p
                      className={cn(
                        "mt-1 mr-2 inline-block rounded-md px-2 py-0.5 text-xs font-medium",
                        style.chip,
                      )}
                    >
                      {formatDaysLeft(deadline.days_left)}
                    </p>
                  )}
                  {(event.period ||
                    event.deadline ||
                    event.application ||
                    event.payment) && (
                    <button
                      type="button"
                      onClick={() =>
                        setOpenId(openId === event.id ? null : event.id)
                      }
                      aria-expanded={openId === event.id}
                      className="mt-1 inline-flex items-center gap-1 text-xs font-bold text-link underline-offset-4 hover:underline"
                    >
                      {openId === event.id ? "Ukryj szczegóły" : "Szczegóły"}
                      <ChevronDown
                        className={cn(
                          "size-3.5 transition-transform",
                          openId === event.id && "rotate-180",
                        )}
                      />
                    </button>
                  )}
                  {openId === event.id && (
                    <EventDetails
                      result={result}
                      event={event}
                      extras={extras}
                    />
                  )}
                </div>
              </li>
            </Fragment>
          );
        })}
        {todayAt === events.length && <TodayMarker lanes={todayLanes} />}
      </ol>
    </div>
  );
}
