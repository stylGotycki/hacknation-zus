"use client";

import { ChevronLeft, ChevronRight, Loader2, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  type EvaluationResult,
  evaluateFamily,
  type FamilyProfile,
  getGuideState,
  saveGuideState,
} from "@/lib/api";
import {
  loadLastForm,
  loadLastProfile,
  loadLastStep,
  saveLastForm,
  saveLastProfile,
  saveLastResult,
  saveLastStep,
} from "@/lib/last-result";
import { PUBLIC_PATHS } from "@/lib/routes";
import { CalculatorResults } from "./calculator-results";
import {
  FormState,
  INITIAL,
  STEP_TITLE,
  buildProfile,
  formFromProfile,
  problems,
  stepsFor,
} from "@/components/calculator/form-model";
import {
  ChildStep,
  DifficultStep,
  FamilyStep,
  ParentStep,
  PlanStep,
  SituationStep,
  Stepper,
} from "@/components/calculator/form-steps";

export function CalculatorForm() {
  const [form, setForm] = useState<FormState>(INITIAL);
  const [step, setStep] = useState(0);
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tried, setTried] = useState(false);
  const [loading, setLoading] = useState(false);

  const [restored, setRestored] = useState(false);

  // Continue where the user stopped: this tab first, then what their account saved (after a new login,
  // in another tab or on another device).
  useEffect(() => {
    const apply = (saved: Partial<FormState>, savedStep: number) => {
      const next = {
        ...INITIAL,
        ...saved,
        mother: { ...INITIAL.mother, ...saved.mother },
        father: { ...INITIAL.father, ...saved.father },
      };
      setForm(next);
      const all = stepsFor(next);
      const at = Math.min(savedStep, all.length - 1);
      setStep(at);
      if (all[at] === "wynik") void calculateFor(next);
    };
    const local = loadLastForm<FormState>();
    if (local && local.stage !== undefined) {
      apply(local, loadLastStep());
      setRestored(true);
      return;
    }
    getGuideState()
      .then((state) => {
        const saved = state.form as FormState | null;
        if (saved && saved.stage !== undefined) return apply(saved, state.step);
        const profile = state.profile ?? loadLastProfile<FamilyProfile>();
        if (profile) {
          const rebuilt = formFromProfile(profile as FamilyProfile);
          apply(rebuilt, stepsFor(rebuilt).length - 1);
        }
      })
      .catch(() => undefined)
      .finally(() => setRestored(true));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Autosave every answer (tab + account), shortly after the user stops typing.
  useEffect(() => {
    if (!restored) return;
    saveLastForm(form);
    saveLastStep(step);
    const timer = setTimeout(() => {
      let profile: FamilyProfile | null = null;
      try {
        profile = form.stage ? buildProfile(form) : null;
      } catch {
        profile = null;
      }
      void saveGuideState({ form, step, profile }).catch(() => undefined);
    }, 800);
    return () => clearTimeout(timer);
  }, [form, step, restored]);

  const steps = useMemo(() => stepsFor(form), [form]);
  const current = steps[Math.min(step, steps.length - 1)];
  const issues = problems(current, form);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((f) => ({ ...f, [key]: value }));
    setResult(null);
  };

  async function calculateFor(state: FormState) {
    setLoading(true);
    setError(null);
    try {
      const profile = buildProfile(state);
      const evaluated = await evaluateFamily(profile);
      saveLastResult(evaluated);
      saveLastForm(state);
      saveLastProfile(profile);
      setResult(evaluated);
    } catch (err) {
      const message = err instanceof Error ? err.message : "";
      const detail = /"detail":\s*"([^"]+)"/.exec(message)?.[1];
      setError(
        detail
          ? `Ten plan nie jest zgodny z przepisami: ${detail}`
          : "Nie udało się policzyć. Sprawdź dane i spróbuj ponownie.",
      );
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  function next() {
    setTried(true);
    if (issues.length) return;
    setTried(false);
    const target = Math.min(step + 1, steps.length - 1);
    setStep(target);
    saveLastForm(form);
    if (steps[target] === "wynik") void calculateFor(form);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function go(i: number) {
    setStep(i);
    setTried(false);
    if (steps[i] === "wynik") void calculateFor(form);
  }

  return (
    <div className="flex flex-col gap-6">
      <Stepper
        steps={steps}
        current={Math.min(step, steps.length - 1)}
        onGo={go}
      />
      <section aria-label={STEP_TITLE[current]} className="flex flex-col gap-5">
        {current !== "wynik" && (
          <h2 id="step-title" className="text-xl font-bold">
            {STEP_TITLE[current]}
          </h2>
        )}
        {current === "sytuacja" && <SituationStep f={form} set={set} />}
        {current === "dziecko" && <ChildStep f={form} set={set} />}
        {current === "rodzina" && <FamilyStep f={form} set={set} />}
        {current === "mama" && <ParentStep f={form} set={set} who="mother" />}
        {current === "tata" && <ParentStep f={form} set={set} who="father" />}
        {current === "trudne" && <DifficultStep f={form} set={set} />}
        {current === "plan" && <PlanStep f={form} set={set} />}
        {current === "wynik" && (
          <>
            {loading && (
              <Loader2
                className="animate-spin text-muted-foreground"
                aria-label="Liczę"
              />
            )}
            {error && (
              <div
                role="alert"
                className="flex flex-col items-start gap-3 rounded-sm border border-destructive/40 bg-destructive/5 p-4 text-sm"
              >
                {error}
                {steps.includes("plan") && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => go(steps.indexOf("plan"))}
                  >
                    <ChevronLeft /> Popraw plan
                  </Button>
                )}
              </div>
            )}
            {result && (
              <>
                <CalculatorResults result={result} />
                <div className="flex flex-wrap gap-3">
                  <Link
                    href={PUBLIC_PATHS.timeline}
                    className="inline-flex h-11 items-center gap-2 rounded-sm bg-primary px-5 font-bold text-white hover:bg-primary-dark"
                  >
                    Zobacz oś czasu i wnioski{" "}
                    <ChevronRight className="size-4" />
                  </Link>
                </div>
              </>
            )}
          </>
        )}
      </section>
      {tried && issues.length > 0 && (
        <ul
          role="alert"
          className="list-disc rounded-sm bg-destructive/5 p-3 pl-8 text-sm text-destructive"
        >
          {issues.map((i) => (
            <li key={i}>{i}</li>
          ))}
        </ul>
      )}
      <div className="flex flex-wrap justify-between gap-3 border-t border-band-border pt-4">
        <div className="flex gap-3">
          {step > 0 && (
            <Button
              type="button"
              variant="outline"
              onClick={() => go(step - 1)}
            >
              <ChevronLeft /> Wstecz
            </Button>
          )}
          {current !== "wynik" && (
            <Button type="button" onClick={next}>
              {steps[step + 1] === "wynik"
                ? "Policz zasiłki i urlopy"
                : "Dalej"}{" "}
              <ChevronRight />
            </Button>
          )}
        </div>
        <Button
          type="button"
          variant="ghost"
          onClick={() => {
            setForm(INITIAL);
            setStep(0);
            setResult(null);
            saveLastForm(null);
          }}
        >
          <RotateCcw /> Zacznij od nowa
        </Button>
      </div>
    </div>
  );
}
