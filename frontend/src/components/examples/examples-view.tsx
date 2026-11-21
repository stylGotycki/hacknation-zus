"use client";

import { Loader2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { CalculatorResults } from "@/components/calculator/calculator-results";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { evaluateFamily, listScenarios, type EvaluationResult, type Scenario } from "@/lib/api";
import { saveLastForm, saveLastProfile, saveLastResult } from "@/lib/last-result";
import { PUBLIC_PATHS } from "@/lib/routes";

export function ExamplesView() {
  const [scenarios, setScenarios] = useState<Scenario[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  useEffect(() => {
    listScenarios()
      .then(setScenarios)
      .catch((e: Error) => setError(e.message));
  }, []);

  async function open(scenario: Scenario) {
    setLoadingId(scenario.id);
    setError(null);
    try {
      const evaluated = await evaluateFamily(scenario.profile);
      saveLastResult(evaluated);
      saveLastForm(null); // an example has no form answers to hand over
      saveLastProfile(scenario.profile);
      setResult(evaluated);
      setActiveId(scenario.id);
      requestAnimationFrame(() =>
        document.getElementById("example-result")?.scrollIntoView({ behavior: "smooth" }),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nie udało się policzyć przykładu.");
    } finally {
      setLoadingId(null);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      {error && (
        <div role="alert" className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm">
          {error}
        </div>
      )}
      {!scenarios && !error && <Loader2 className="animate-spin text-muted-foreground" />}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {scenarios?.map((scenario) => (
          <Card key={scenario.id} className={scenario.id === activeId ? "border-primary" : undefined}>
            <CardHeader>
              <CardTitle className="text-base">
                <span className="mr-2 text-muted-foreground">{scenario.id}</span>
                {scenario.title_pl}
              </CardTitle>
              <CardDescription>{scenario.description_pl}</CardDescription>
            </CardHeader>
            <CardContent className="mt-auto flex flex-col gap-3">
              <div className="flex flex-wrap gap-1.5">
                {scenario.tags.map((tag) => (
                  <Badge key={tag} variant="secondary">
                    {tag}
                  </Badge>
                ))}
              </div>
              <Button onClick={() => open(scenario)} disabled={loadingId !== null} className="w-full">
                {loadingId === scenario.id && <Loader2 className="animate-spin" />}
                Zobacz wyliczenie
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
      {result && (
        <div id="example-result" className="flex flex-col gap-4 scroll-mt-20">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-xl font-semibold">
              Wyliczenie dla przykładu {activeId}
            </h2>
            <Button asChild variant="outline">
              <Link href={PUBLIC_PATHS.timeline}>Otwórz na osi czasu</Link>
            </Button>
          </div>
          <CalculatorResults result={result} />
        </div>
      )}
    </div>
  );
}
