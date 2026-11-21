"use client";

import { ArrowLeft, ArrowRight, Loader2, Sparkles } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import {
  buildProfile,
  INITIAL,
  ParentFields,
  type FormState,
} from "@/components/calculator/calculator-form";
import { CalculatorResults } from "@/components/calculator/calculator-results";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox, Field, Input } from "@/components/ui/form-controls";
import { evaluateFamily, type EvaluationResult, type Situation } from "@/lib/api";
import { toIsoDate } from "@/lib/format";
import { saveLastForm, saveLastResult } from "@/lib/last-result";
import { PUBLIC_PATHS } from "@/lib/routes";
import { cn } from "@/lib/utils";

type StepId = "situation" | "date" | "details" | "mother" | "father" | "plan" | "result";

const SITUATIONS: { value: Situation; title: string; text: string }[] = [
  { value: "birth", title: "Urodzenie dziecka", text: "Dziecko jest w drodze albo już się urodziło." },
  { value: "adoption", title: "Przysposobienie", text: "Przyjęliście dziecko na wychowanie i wystąpiliście do sądu o adopcję." },
  { value: "foster", title: "Rodzina zastępcza", text: "Przyjęliście dziecko do niezawodowej rodziny zastępczej." },
];

function stepsFor(form: FormState): StepId[] {
  const steps: StepId[] = ["situation", "date", "details", "mother"];
  steps.push("father");
  if (form.withFather || form.situation === "birth") steps.push("plan");
  steps.push("result");
  return steps;
}

const TITLES: Record<StepId, string> = {
  situation: "Co się u Was zmienia?",
  date: "Kiedy?",
  details: "Szczegóły dotyczące dziecka",
  mother: "Mama",
  father: "Tata",
  plan: "Jak chcecie podzielić urlopy?",
  result: "Wynik",
};

export function WizardView() {
  const [form, setForm] = useState<FormState>(INITIAL);
  const [index, setIndex] = useState(0);
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const inTwoMonths = new Date();
    inTwoMonths.setDate(inTwoMonths.getDate() + 60);
    setForm((f) => (f.date ? f : { ...f, date: toIsoDate(inTwoMonths) }));
  }, []);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const steps = stepsFor(form);
  const step = steps[Math.min(index, steps.length - 1)];
  const isBirth = form.situation === "birth";
  const canNext = step !== "date" || Boolean(form.date);

  async function calculate() {
    setLoading(true);
    setError(null);
    try {
      const evaluated = await evaluateFamily(buildProfile(form));
      saveLastResult(evaluated);
      saveLastForm(form);
      setResult(evaluated);
      setIndex(steps.length - 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nie udało się policzyć uprawnień.");
    } finally {
      setLoading(false);
    }
  }

  function next() {
    if (steps[index + 1] === "result") void calculate();
    else setIndex(index + 1);
  }

  function restart() {
    setResult(null);
    setError(null);
    setIndex(0);
  }

  return (
    <div className="flex flex-col gap-6">
      {step !== "result" && (
        <div className="flex flex-col gap-2" aria-label="Postęp">
          <div className="flex gap-1.5">
            {steps.slice(0, -1).map((id, i) => (
              <span key={id} className={cn("h-1.5 flex-1 rounded-full", i <= index ? "bg-primary" : "bg-muted")} />
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            Krok {index + 1} z {steps.length - 1}
          </p>
        </div>
      )}

      {step !== "result" && (
        <Card>
          <CardHeader>
            <CardTitle>{TITLES[step]}</CardTitle>
            {step === "mother" && <CardDescription>Dane potrzebne do ustalenia prawa do zasiłku.</CardDescription>}
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {step === "situation" && (
              <div className="grid gap-3">
                {SITUATIONS.map((s) => (
                  <button
                    key={s.value}
                    type="button"
                    onClick={() => {
                      set("situation", s.value);
                      setIndex(1);
                    }}
                    className={cn(
                      "rounded-lg border p-4 text-left transition-colors hover:border-primary hover:bg-muted",
                      form.situation === s.value && "border-primary bg-muted",
                    )}
                  >
                    <span className="block font-medium">{s.title}</span>
                    <span className="text-sm text-muted-foreground">{s.text}</span>
                  </button>
                ))}
              </div>
            )}
            {step === "date" && (
              <>
                {isBirth && (
                  <Checkbox
                    label="Dziecko już się urodziło"
                    checked={form.born}
                    onChange={(e) => set("born", e.target.checked)}
                  />
                )}
                <Field
                  label={isBirth ? (form.born ? "Data urodzenia" : "Przewidywana data porodu") : "Data przyjęcia dziecka"}
                >
                  <Input type="date" value={form.date} onChange={(e) => set("date", e.target.value)} />
                </Field>
                <Field label="Ile dzieci naraz?" hint="Np. 2 przy bliźniętach.">
                  <Input inputMode="numeric" value={form.children} onChange={(e) => set("children", e.target.value)} />
                </Field>
              </>
            )}
            {step === "details" && (
              <>
                {!isBirth && (
                  <Field label="Wiek dziecka (lata)">
                    <Input inputMode="decimal" value={form.age} onChange={(e) => set("age", e.target.value)} />
                  </Field>
                )}
                <Checkbox
                  label="Mamy zaświadczenie „Za życiem”"
                  hint="Wydłuża urlop rodzicielski do 65 / 67 tygodni."
                  checked={form.zaZyciem}
                  onChange={(e) => set("zaZyciem", e.target.checked)}
                />
                {isBirth && form.born && (
                  <div className="grid gap-4 sm:grid-cols-3">
                    <Field label="Tydzień ciąży przy porodzie" hint="Pomijasz, jeśli dziecko urodziło się o czasie.">
                      <Input inputMode="numeric" value={form.gestation} onChange={(e) => set("gestation", e.target.value)} />
                    </Field>
                    <Field label="Dni pobytu dziecka w szpitalu">
                      <Input inputMode="numeric" value={form.hospitalDays} onChange={(e) => set("hospitalDays", e.target.value)} />
                    </Field>
                    <Field label="Od którego dnia po porodzie?">
                      <Input inputMode="numeric" value={form.hospitalFirstDay} onChange={(e) => set("hospitalFirstDay", e.target.value)} />
                    </Field>
                  </div>
                )}
                {isBirth && (
                  <Checkbox
                    label="Dziecko urodziło się martwe"
                    checked={form.stillborn}
                    onChange={(e) => set("stillborn", e.target.checked)}
                  />
                )}
              </>
            )}
            {step === "mother" && (
              <ParentFields title="Mama" value={form.mother} onChange={(v) => set("mother", v)} showWork />
            )}
            {step === "father" && (
              <>
                <Checkbox
                  label="Uwzględnij tatę (drugiego rodzica)"
                  checked={form.withFather}
                  onChange={(e) => set("withFather", e.target.checked)}
                />
                {form.withFather && (
                  <ParentFields title="Tata" value={form.father} onChange={(v) => set("father", v)} showWork />
                )}
              </>
            )}
            {step === "plan" && (
              <>
                <p className="text-sm text-muted-foreground">
                  Domyślny podział jest poprawny – zmień go tylko, jeśli chcecie inaczej.
                </p>
                {isBirth && (
                  <Field label="Urlop macierzyński przed porodem (tygodnie)" hint="Najwyżej 6 tygodni.">
                    <Input inputMode="numeric" value={form.beforeBirthWeeks} onChange={(e) => set("beforeBirthWeeks", e.target.value)} />
                  </Field>
                )}
                {form.withFather && (
                  <>
                    <Field label="Urlop macierzyński przejęty przez tatę (tygodnie)" hint="Mama musi wykorzystać co najmniej 14 tygodni po porodzie.">
                      <Input inputMode="numeric" value={form.toFatherWeeks} onChange={(e) => set("toFatherWeeks", e.target.value)} />
                    </Field>
                    <Field label="Urlop rodzicielski taty (tygodnie)" hint="Każdy z rodziców ma 9 tygodni wyłącznie dla siebie.">
                      <Input inputMode="numeric" value={form.fatherParentalWeeks} onChange={(e) => set("fatherParentalWeeks", e.target.value)} />
                    </Field>
                  </>
                )}
                {isBirth && (
                  <Checkbox
                    label="Mama złoży wniosek o stałą stawkę 81,5% w ciągu 21 dni od porodu"
                    hint="Zamiast 100% za urlop macierzyński i 70% za rodzicielski."
                    checked={form.averagedApplied}
                    onChange={(e) => set("averagedApplied", e.target.checked)}
                  />
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}

      {error && (
        <div role="alert" className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm">
          {error}
        </div>
      )}

      {step !== "result" && step !== "situation" && (
        <div className="flex justify-between gap-3">
          <Button variant="outline" onClick={() => setIndex(Math.max(0, index - 1))}>
            <ArrowLeft /> Wstecz
          </Button>
          <Button onClick={next} disabled={!canNext || loading}>
            {loading ? <Loader2 className="animate-spin" /> : steps[index + 1] === "result" ? <Sparkles /> : null}
            {steps[index + 1] === "result" ? "Sprawdź uprawnienia" : "Dalej"}
            {steps[index + 1] !== "result" && <ArrowRight />}
          </Button>
        </div>
      )}

      {step === "result" && result && (
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={restart}>
              <ArrowLeft /> Zacznij od nowa
            </Button>
            <Button asChild variant="outline">
              <Link href={PUBLIC_PATHS.timeline}>Zobacz oś czasu</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href={PUBLIC_PATHS.calculator}>Dopracuj w kalkulatorze</Link>
            </Button>
          </div>
          <CalculatorResults result={result} />
        </div>
      )}
    </div>
  );
}
