"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { VerticalTimeline } from "@/components/timeline/vertical-timeline";
import { Button } from "@/components/ui/button";
import type { EvaluationResult } from "@/lib/api";
import { loadLastResult } from "@/lib/last-result";
import { withoutIdleFather } from "@/lib/result-view";
import { PUBLIC_PATHS } from "@/lib/routes";

/** Shows the timeline of the last calculation made in this browser tab. */
export function TimelineView() {
  const [result, setResult] = useState<EvaluationResult | null | undefined>(undefined);

  useEffect(() => {
    const last = loadLastResult();
    setResult(last ? withoutIdleFather(last) : null);
  }, []);

  if (result === undefined) return null;
  if (result === null) {
    return (
      <div className="flex flex-col items-start gap-4 rounded-xl border border-dashed p-6">
        <p>Oś czasu powstaje z wyniku kalkulatora. Policz najpierw zasiłki i urlopy swojej rodziny.</p>
        <Button asChild>
          <Link href={PUBLIC_PATHS.calculator}>Przejdź do kalkulatora</Link>
        </Button>
      </div>
    );
  }
  return <VerticalTimeline result={result} />;
}
