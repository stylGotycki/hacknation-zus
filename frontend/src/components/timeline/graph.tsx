"use client";

import { cn } from "@/lib/utils";
import { Segment, TimelineEvent } from "@/components/timeline/model";
import {
  DEADLINE_STYLE,
  DOT_Y,
  GRAPH_WIDTH,
  LANE_BORDER,
  LANE_COLOR,
  LANE_TEXT,
  LANE_X,
  LINE,
  TODAY,
  iconFor,
} from "@/components/timeline/style";

export function Graph({
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
  const style =
    event.type === "deadline" && event.deadline
      ? DEADLINE_STYLE[event.deadline.status]
      : null;
  const late =
    event.type === "application" &&
    event.application?.status !== "decided" &&
    event.deadline &&
    event.date > event.deadline.due;
  const Icon = iconFor(event);
  const filled = event.type === "start" || event.type === "birth";
  const payment = event.type === "payment";
  const size = event.type === "birth" ? 44 : payment ? 30 : 36;
  const past = event.date <= TODAY;
  return (
    <div
      className="relative shrink-0 self-stretch"
      style={{ width: GRAPH_WIDTH }}
    >
      {segments.map((s) => (
        <span
          key={s.lane}
          aria-hidden
          className={cn(
            "absolute -translate-x-1/2 rounded-full",
            LANE_COLOR[s.lane],
            past && "opacity-40",
          )}
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
          className={cn(
            "absolute rounded-full",
            LANE_COLOR[event.lane],
            past && "opacity-40",
          )}
          style={{
            left: LANE_X.main,
            width: x - LANE_X.main,
            top: DOT_Y - LINE / 2,
            height: LINE,
          }}
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
                ? cn(
                    LANE_BORDER[event.lane],
                    LANE_COLOR[event.lane],
                    "text-white",
                  )
                : cn(
                    LANE_BORDER[event.lane],
                    "bg-background",
                    LANE_TEXT[event.lane],
                  ),
          payment &&
            cn(
              "bg-background",
              event.payment?.person === "father"
                ? "border-info text-info"
                : "border-primary text-primary",
              event.date > TODAY && "border-dashed",
            ),
          event.type === "application" &&
            (late
              ? "border-amber-600 bg-background text-amber-700"
              : "border-navy bg-background text-navy"),
          past && "opacity-45 grayscale",
          open && "ring-4 ring-orange",
        )}
        style={{ left: x, top: DOT_Y, width: size, height: size }}
      >
        <Icon
          className={
            event.type === "birth"
              ? "size-6"
              : payment
                ? "size-4"
                : "size-[18px]"
          }
          strokeWidth={2.25}
        />
      </button>
    </div>
  );
}
