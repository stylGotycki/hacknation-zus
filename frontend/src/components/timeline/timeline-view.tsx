"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { type TimelineExtras, VerticalTimeline } from "@/components/timeline/vertical-timeline";
import { type EvaluationResult, type FamilyProfile, getSuggestions, listApplications } from "@/lib/api";
import { loadLastProfile, loadLastResult } from "@/lib/last-result";
import { PUBLIC_PATHS } from "@/lib/routes";

/** Shows the timeline of the last calculation, with the forms to file and applications already filed. */
export function TimelineView() {
  const [result, setResult] = useState<EvaluationResult | null | undefined>(undefined);
  const [extras, setExtras] = useState<TimelineExtras>({ suggestions: [], applications: [] });

  useEffect(() => {
    const last = loadLastResult();
    setResult(last);
    if (!last) return;
    const profile = loadLastProfile<FamilyProfile>();
    // Both calls are optional: without them the timeline still shows leaves and deadlines.
    Promise.allSettled([profile ? getSuggestions(profile) : Promise.resolve([]), listApplications()]).then(
      ([s, a]) =>
        setExtras({
          suggestions: s.status === "fulfilled" ? s.value : [],
          applications: a.status === "fulfilled" ? a.value : [],
        }),
    );
  }, []);

  if (result === undefined) return null;
  if (result === null) {
    return (
      <div className="flex flex-col items-start gap-3 border-l-[5px] border-primary bg-muted p-5">
        <p>Oś czasu powstaje z wyliczenia. Najpierw sprawdź uprawnienia albo policz zasiłki w kalkulatorze.</p>
        <Link href={PUBLIC_PATHS.calculator} className="inline-flex items-center gap-1 font-bold text-link hover:underline">
          Przejdź do kalkulatora <ChevronRight className="size-4" />
        </Link>
      </div>
    );
  }
  return <VerticalTimeline result={result} extras={extras} />;
}
