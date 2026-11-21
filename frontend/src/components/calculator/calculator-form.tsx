"use client";

import { Calculator, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox, Field, Input, Select } from "@/components/ui/form-controls";
import {
  type EmploymentType,
  type EvaluationResult,
  evaluateFamily,
  type FamilyProfile,
  type ParentProfile,
  type Situation,
} from "@/lib/api";
import { toIsoDate } from "@/lib/format";
import { saveLastResult } from "@/lib/last-result";

import { CalculatorResults } from "./calculator-results";

const EMPLOYMENT_LABELS: Record<EmploymentType, string> = {
  employee: "Umowa o pracę",
  contract: "Umowa zlecenie",
  self_employed: "Działalność gospodarcza (JDG)",
  cooperating: "Osoba współpracująca",
  unemployed: "Bez pracy",
  other: "Inna sytuacja",
};

type ParentForm = {
  employment: EmploymentType;
  voluntary: boolean;
  base: string;
  employerCount: string;
  debt: string;
  workPercent: string;
};

type FormState = {
  situation: Situation;
  born: boolean;
  date: string;
  children: string;
  zaZyciem: boolean;
  stillborn: boolean;
  gestation: string;
  hospitalDays: string;
  hospitalFirstDay: string;
  age: string;
  schoolDeferred: boolean;
  mother: ParentForm;
  withFather: boolean;
  father: ParentForm;
  beforeBirthWeeks: string;
  toFatherWeeks: string;
  fatherParentalWeeks: string;
  averagedApplied: boolean;
};

const emptyParent = (base: string): ParentForm => ({
  employment: "employee",
  voluntary: false,
  base,
  employerCount: "50",
  debt: "",
  workPercent: "0",
});

const INITIAL: FormState = {
  situation: "birth",
  born: false,
  date: "",
  children: "1",
  zaZyciem: false,
  stillborn: false,
  gestation: "",
  hospitalDays: "",
  hospitalFirstDay: "",
  age: "3",
  schoolDeferred: false,
  mother: emptyParent("6000"),
  withFather: true,
  father: emptyParent("5000"),
  beforeBirthWeeks: "0",
  toFatherWeeks: "0",
  fatherParentalWeeks: "9",
  averagedApplied: false,
};

const num = (value: string): number | null => {
  const parsed = Number(value.replace(",", "."));
  return value.trim() === "" || Number.isNaN(parsed) ? null : parsed;
};

function parentProfile(form: ParentForm): ParentProfile {
  const isEmployee = form.employment === "employee";
  const hasInsuranceChoice = !isEmployee && form.employment !== "unemployed";
  return {
    employment: form.employment,
    sickness_insurance: isEmployee ? "mandatory" : hasInsuranceChoice && form.voluntary ? "voluntary" : "none",
    average_monthly_base: num(form.base),
    employer_insured_count: isEmployee || form.employment === "contract" ? num(form.employerCount) : null,
    contribution_debt: num(form.debt) ?? 0,
    planned_work_fraction: isEmployee ? (num(form.workPercent) ?? 0) / 100 : 0,
  };
}

export function buildProfile(form: FormState): FamilyProfile {
  const isBirth = form.situation === "birth";
  const child: FamilyProfile["child"] = {
    situation: form.situation,
    children_count: num(form.children) ?? 1,
    za_zyciem: form.zaZyciem,
  };
  if (isBirth) {
    if (form.born) child.birth_date = form.date;
    else child.due_date = form.date;
    child.stillborn = form.stillborn;
    child.gestation_weeks = num(form.gestation);
    child.hospital_days = num(form.hospitalDays) ?? 0;
    child.hospital_first_day = num(form.hospitalFirstDay);
  } else {
    child.placement_date = form.date;
    child.age_years = num(form.age);
    child.school_deferred = form.schoolDeferred;
  }
  return {
    child,
    mother: parentProfile(form.mother),
    father: form.withFather ? parentProfile(form.father) : null,
    averaged_rate_applied_on: form.averagedApplied && isBirth ? form.date : null,
    plan: {
      maternity_before_birth_weeks: isBirth ? (num(form.beforeBirthWeeks) ?? 0) : 0,
      maternity_weeks_to_father: form.withFather ? (num(form.toFatherWeeks) ?? 0) : 0,
      parental_weeks_father: form.withFather ? num(form.fatherParentalWeeks) : null,
    },
  };
}

function ParentFields({
  title,
  value,
  onChange,
  showWork,
}: {
  title: string;
  value: ParentForm;
  onChange: (next: ParentForm) => void;
  showWork: boolean;
}) {
  const set = <K extends keyof ParentForm>(key: K, v: ParentForm[K]) => onChange({ ...value, [key]: v });
  const isEmployee = value.employment === "employee";
  return (
    <div className="flex flex-col gap-4">
      <h3 className="font-medium">{title}</h3>
      <Field label="Forma zatrudnienia">
        <Select
          value={value.employment}
          onChange={(e) => set("employment", e.target.value as EmploymentType)}
        >
          {Object.entries(EMPLOYMENT_LABELS).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </Select>
      </Field>
      {value.employment !== "unemployed" && (
        <Field
          label="Średnia miesięczna podstawa brutto (zł)"
          hint={
            isEmployee
              ? "Średnie wynagrodzenie brutto z ostatnich 12 miesięcy."
              : "Średnia podstawa składki chorobowej z ostatnich 12 miesięcy."
          }
        >
          <Input
            inputMode="decimal"
            value={value.base}
            onChange={(e) => set("base", e.target.value)}
          />
        </Field>
      )}
      {!isEmployee && value.employment !== "unemployed" && (
        <Checkbox
          label="Opłacam dobrowolną składkę chorobową"
          hint="Bez niej zasiłek macierzyński nie przysługuje."
          checked={value.voluntary}
          onChange={(e) => set("voluntary", e.target.checked)}
        />
      )}
      {(isEmployee || value.employment === "contract") && (
        <Field
          label="Ilu ubezpieczonych zgłasza pracodawca?"
          hint="Powyżej 20 osób zasiłek wypłaca pracodawca, w przeciwnym razie ZUS."
        >
          <Input
            inputMode="numeric"
            value={value.employerCount}
            onChange={(e) => set("employerCount", e.target.value)}
          />
        </Field>
      )}
      {(value.employment === "self_employed" || value.employment === "cooperating") && (
        <Field
          label="Zadłużenie z tytułu składek (zł)"
          hint="Zadłużenie powyżej 1% płacy minimalnej wstrzymuje wypłatę zasiłku."
        >
          <Input
            inputMode="decimal"
            value={value.debt}
            onChange={(e) => set("debt", e.target.value)}
          />
        </Field>
      )}
      {isEmployee && showWork && (
        <Field
          label="Praca w trakcie urlopu rodzicielskiego (% etatu)"
          hint="0 – pełny urlop; maksymalnie 50% etatu u tego samego pracodawcy."
        >
          <Input
            inputMode="numeric"
            value={value.workPercent}
            onChange={(e) => set("workPercent", e.target.value)}
          />
        </Field>
      )}
    </div>
  );
}

export function CalculatorForm() {
  const [form, setForm] = useState<FormState>(INITIAL);
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Default date is set after mount so server and client render the same markup.
  useEffect(() => {
    const inTwoMonths = new Date();
    inTwoMonths.setDate(inTwoMonths.getDate() + 60);
    setForm((f) => (f.date ? f : { ...f, date: toIsoDate(inTwoMonths) }));
  }, []);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }));
  const isBirth = form.situation === "birth";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const evaluated = await evaluateFamily(buildProfile(form));
      saveLastResult(evaluated);
      setResult(evaluated);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Nieznany błąd";
      // API errors look like `API 422: {"detail": "..."}`; show the plain reason when possible.
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

  return (
    <div className="flex flex-col gap-8">
      <form onSubmit={submit} className="flex flex-col gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Dziecko</CardTitle>
            <CardDescription>Kiedy i w jakiej sytuacji zostajecie rodzicami.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <Field label="Sytuacja">
              <Select
                value={form.situation}
                onChange={(e) => set("situation", e.target.value as Situation)}
              >
                <option value="birth">Urodzenie dziecka</option>
                <option value="adoption">Przysposobienie</option>
                <option value="foster">Rodzina zastępcza niezawodowa</option>
              </Select>
            </Field>
            <Field
              label={
                isBirth
                  ? form.born
                    ? "Data urodzenia"
                    : "Przewidywana data porodu"
                  : "Data przyjęcia dziecka"
              }
            >
              <Input type="date" value={form.date} onChange={(e) => set("date", e.target.value)} required />
            </Field>
            {isBirth && (
              <Checkbox
                label="Dziecko już się urodziło"
                checked={form.born}
                onChange={(e) => set("born", e.target.checked)}
                className="sm:col-span-2"
              />
            )}
            <Field label="Liczba dzieci urodzonych / przyjętych jednocześnie">
              <Input
                inputMode="numeric"
                value={form.children}
                onChange={(e) => set("children", e.target.value)}
              />
            </Field>
            {!isBirth && (
              <Field label="Wiek dziecka (lata)">
                <Input
                  inputMode="decimal"
                  value={form.age}
                  onChange={(e) => set("age", e.target.value)}
                />
              </Field>
            )}
            <Checkbox
              label="Zaświadczenie „Za życiem”"
              hint="Wydłuża urlop rodzicielski do 65 / 67 tygodni."
              checked={form.zaZyciem}
              onChange={(e) => set("zaZyciem", e.target.checked)}
            />
            {isBirth && (
              <Checkbox
                label="Dziecko urodziło się martwe"
                checked={form.stillborn}
                onChange={(e) => set("stillborn", e.target.checked)}
              />
            )}
            {!isBirth && form.situation === "foster" && (
              <Checkbox
                label="Odroczony obowiązek szkolny"
                checked={form.schoolDeferred}
                onChange={(e) => set("schoolDeferred", e.target.checked)}
              />
            )}
            {isBirth && form.born && (
              <details className="rounded-md border p-3 sm:col-span-2">
                <summary className="cursor-pointer text-sm font-medium">
                  Wcześniak lub dziecko w szpitalu (uzupełniający urlop macierzyński)
                </summary>
                <div className="mt-4 grid gap-4 sm:grid-cols-3">
                  <Field label="Tydzień ciąży przy porodzie">
                    <Input
                      inputMode="numeric"
                      value={form.gestation}
                      onChange={(e) => set("gestation", e.target.value)}
                    />
                  </Field>
                  <Field label="Dni pobytu dziecka w szpitalu" hint="Od 5. dnia po porodzie.">
                    <Input
                      inputMode="numeric"
                      value={form.hospitalDays}
                      onChange={(e) => set("hospitalDays", e.target.value)}
                    />
                  </Field>
                  <Field label="Który dzień po porodzie zaczął się pobyt?">
                    <Input
                      inputMode="numeric"
                      value={form.hospitalFirstDay}
                      onChange={(e) => set("hospitalFirstDay", e.target.value)}
                    />
                  </Field>
                </div>
              </details>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Rodzice</CardTitle>
            <CardDescription>Dane potrzebne do ustalenia prawa do zasiłku i jego wysokości.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6 md:grid-cols-2">
            <ParentFields
              title="Mama"
              value={form.mother}
              onChange={(v) => set("mother", v)}
              showWork
            />
            <div className="flex flex-col gap-4">
              <Checkbox
                label="Uwzględnij tatę (drugiego rodzica)"
                checked={form.withFather}
                onChange={(e) => set("withFather", e.target.checked)}
              />
              {form.withFather && (
                <ParentFields
                  title="Tata"
                  value={form.father}
                  onChange={(v) => set("father", v)}
                  showWork
                />
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Plan urlopów</CardTitle>
            <CardDescription>Domyślny plan jest poprawny – zmień go, jeśli chcecie inaczej.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            {isBirth && (
              <Field label="Urlop macierzyński przed porodem (tygodnie)" hint="Najwyżej 6 tygodni.">
                <Input
                  inputMode="numeric"
                  value={form.beforeBirthWeeks}
                  onChange={(e) => set("beforeBirthWeeks", e.target.value)}
                />
              </Field>
            )}
            {form.withFather && (
              <>
                <Field
                  label="Urlop macierzyński przejęty przez tatę (tygodnie)"
                  hint="Mama musi wykorzystać co najmniej 14 tygodni po porodzie."
                >
                  <Input
                    inputMode="numeric"
                    value={form.toFatherWeeks}
                    onChange={(e) => set("toFatherWeeks", e.target.value)}
                  />
                </Field>
                <Field
                  label="Urlop rodzicielski taty (tygodnie)"
                  hint="Każdy z rodziców ma 9 tygodni wyłącznie dla siebie."
                >
                  <Input
                    inputMode="numeric"
                    value={form.fatherParentalWeeks}
                    onChange={(e) => set("fatherParentalWeeks", e.target.value)}
                  />
                </Field>
              </>
            )}
            {isBirth && (
              <Checkbox
                label="Mama złoży wniosek o stałą stawkę 81,5% w ciągu 21 dni od porodu"
                hint="Zamiast 100% za urlop macierzyński i 70% za rodzicielski."
                checked={form.averagedApplied}
                onChange={(e) => set("averagedApplied", e.target.checked)}
                className="sm:col-span-2"
              />
            )}
          </CardContent>
        </Card>

        <div>
          <Button type="submit" size="lg" disabled={loading || !form.date} className="w-full sm:w-auto">
            {loading ? <Loader2 className="animate-spin" /> : <Calculator />}
            Policz zasiłki i urlopy
          </Button>
        </div>
      </form>

      {error && (
        <div role="alert" className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm">
          {error}
        </div>
      )}
      {result && <CalculatorResults result={result} />}
    </div>
  );
}
