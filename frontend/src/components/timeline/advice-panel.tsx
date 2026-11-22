"use client";

import { Lightbulb } from "lucide-react";
import type { EvaluationResult } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { TimelineExtras } from "@/components/timeline/model";
import { PERSON_NAME } from "@/components/timeline/style";
import { fulfilledBy } from "@/components/timeline/events";

/** Advice for every deadline that has passed without a filed application. */
export function AdvicePanel({
  result,
  extras,
}: {
  result: EvaluationResult;
  extras: TimelineExtras;
}) {
  const missed = result.deadlines.filter(
    (d) =>
      d.status === "overdue" &&
      d.late_pl &&
      !(d.kind === "apply" && fulfilledBy(d, extras.applications)),
  );
  if (!missed.length) return null;
  return (
    <section
      aria-labelledby="porady"
      className="flex flex-col gap-2 border border-amber-300 bg-amber-50/60 p-4"
    >
      <h2 id="porady" className="flex items-center gap-2 font-bold">
        <Lightbulb className="size-5 text-amber-700" aria-hidden /> Porady:
        terminy, które minęły
      </h2>
      <ul className="flex flex-col gap-2 text-sm">
        {missed.map((d) => (
          <li key={d.code}>
            <span className="font-bold">
              {d.person === "family" ? "" : `${PERSON_NAME[d.person]}: `}
              {d.title_pl}
            </span>{" "}
            <span className="text-muted-foreground">
              (do {formatDate(d.due)})
            </span>{" "}
            – {d.late_pl}
          </li>
        ))}
      </ul>
    </section>
  );
}
