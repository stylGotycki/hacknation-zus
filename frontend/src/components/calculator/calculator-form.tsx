"use client";

import { ChevronLeft, ChevronRight, Loader2, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox, Field, Input, Select } from "@/components/ui/form-controls";
import {
  type EmploymentType,
  type EvaluationResult,
  evaluateFamily,
  type FamilyProfile,
  type MotherCannotCare,
  type ParentProfile,
} from "@/lib/api";
import { formatDate, toIsoDate } from "@/lib/format";
import { loadLastForm, loadLastProfile, saveLastForm, saveLastProfile, saveLastResult } from "@/lib/last-result";
import { PUBLIC_PATHS } from "@/lib/routes";
import { cn } from "@/lib/utils";

import { CalculatorResults } from "./calculator-results";

/*
 * The calculator is a small state machine (docs/maszyna-stanow.md):
 *   sytuacja -> dziecko -> rodzina -> praca mamy / praca taty -> trudne sytuacje -> plan -> wynik
 * Steps that do not apply are skipped (no father -> no split; stillbirth -> no plan; a stillbirth
 * or a child's death can only be entered after the birth).
 */

export type Stage = "pregnancy" | "born" | "adoption" | "foster";
type Outcome = "alive" | "stillborn" | "died";
type Family = "both" | "mother" | "father";

export type ParentForm = {
  employment: EmploymentType;
  voluntary: boolean; // non-employee: pays voluntary sickness contribution
  otherInsured: boolean; // "other" title: has sickness insurance
  startRelief: boolean;
  base: string;
  history: string;
  partTime: boolean;
  fraction: string; // % of full time
  payer: "over20" | "upTo20";
  debt: string;
  debtPaidOn: string;
  childcareLeave: boolean;
  workPercent: string;
  // mother only
  ended: boolean;
  endedOn: string;
  endReason: "employer_bankruptcy" | "unlawful_dismissal" | "other";
  fixedTerm: boolean;
  sick: boolean;
  sickStart: string;
  sickEnd: string;
  sickUsed: string;
  over50: boolean;
};

export type FormState = {
  stage: Stage | null;
  date: string;
  children: string;
  zaZyciem: boolean;
  outcome: Outcome;
  diedOn: string;
  surviving: string;
  premature: boolean;
  gestation: string;
  weight: string;
  hospitalDays: string;
  hospitalFirstDay: string;
  age: string;
  schoolDeferred: boolean;
  family: Family;
  mother: ParentForm;
  father: ParentForm;
  difficult: "none" | MotherCannotCare;
  difficultFrom: string;
  difficultTo: string;
  beforeBirthWeeks: string;
  toFatherWeeks: string;
  fatherParentalWeeks: string;
  fatherParentalStart: string;
  motherParentalStart: string;
  partsMother: string;
  partsFather: string;
  paternityStart: string;
  paternityParts: "1" | "2";
  supplementary: boolean;
  supplementaryBy: "mother" | "father";
  averaged: boolean;
  averagedAppliedOn: string;
};

const EMPLOYMENT: [EmploymentType, string][] = [
  ["employee", "Umowa o pracę"],
  ["contract", "Umowa zlecenie"],
  ["self_employed", "Działalność gospodarcza"],
  ["cooperating", "Osoba współpracująca przy działalności"],
  ["unemployed", "Nie pracuję / bezrobocie / studia"],
  ["other", "Inny tytuł (np. umowa o dzieło)"],
];

const parent = (base: string): ParentForm => ({
  employment: "employee",
  voluntary: true,
  otherInsured: false,
  startRelief: false,
  base,
  history: "",
  partTime: false,
  fraction: "50",
  payer: "over20",
  debt: "",
  debtPaidOn: "",
  childcareLeave: false,
  workPercent: "0",
  ended: false,
  endedOn: "",
  endReason: "employer_bankruptcy",
  fixedTerm: false,
  sick: false,
  sickStart: "",
  sickEnd: "",
  sickUsed: "0",
  over50: false,
});

export const INITIAL: FormState = {
  stage: null,
  date: "",
  children: "1",
  zaZyciem: false,
  outcome: "alive",
  diedOn: "",
  surviving: "",
  premature: false,
  gestation: "",
  weight: "",
  hospitalDays: "",
  hospitalFirstDay: "",
  age: "3",
  schoolDeferred: false,
  family: "both",
  mother: parent("6000"),
  father: parent("6000"),
  difficult: "none",
  difficultFrom: "",
  difficultTo: "",
  beforeBirthWeeks: "0",
  toFatherWeeks: "0",
  fatherParentalWeeks: "9",
  fatherParentalStart: "",
  motherParentalStart: "",
  partsMother: "1",
  partsFather: "1",
  paternityStart: "",
  paternityParts: "1",
  supplementary: true,
  supplementaryBy: "mother",
  averaged: false,
  averagedAppliedOn: "",
};

const num = (value: string): number | null => {
  const parsed = Number(value.replace(",", ".").replace(/\s/g, ""));
  return value.trim() === "" || Number.isNaN(parsed) ? null : parsed;
};
const todayIso = () => toIsoDate(new Date());
const addDays = (iso: string, days: number) => {
  const d = new Date(`${iso}T12:00:00`);
  d.setDate(d.getDate() + days);
  return toIsoDate(d);
};

// --- What the answers mean (client-side only to decide which questions to ask) -----------

const isBirth = (f: FormState) => f.stage === "pregnancy" || f.stage === "born";
const hasMother = (f: FormState) => isBirth(f) || f.family !== "father";
const hasFather = (f: FormState) => (isBirth(f) ? f.family === "both" : f.family !== "mother");
const alive = (f: FormState) => f.stage !== "born" || f.outcome !== "stillborn";

/** Can the parent be insured in sickness insurance on the day of the event? (the engine decides finally) */
export function insured(p: ParentForm): boolean {
  if (p.startRelief) return false;
  switch (p.employment) {
    case "employee":
      return true;
    case "contract":
    case "self_employed":
    case "cooperating":
      return p.voluntary;
    case "other":
      return p.otherInsured;
    default:
      return p.childcareLeave;
  }
}

const motherInsured = (f: FormState) => hasMother(f) && (insured(f.mother) || (f.mother.ended && isBirth(f)));
const fatherInsured = (f: FormState) => hasFather(f) && insured(f.father);

type StepId = "sytuacja" | "dziecko" | "rodzina" | "mama" | "tata" | "trudne" | "plan" | "wynik";
const STEP_TITLE: Record<StepId, string> = {
  sytuacja: "Sytuacja",
  dziecko: "Dziecko",
  rodzina: "Rodzina",
  mama: "Praca mamy",
  tata: "Praca taty",
  trudne: "Szczególne sytuacje",
  plan: "Plan urlopów",
  wynik: "Wynik",
};

export function stepsFor(f: FormState): StepId[] {
  const steps: StepId[] = ["sytuacja"];
  if (!f.stage) return steps;
  steps.push("dziecko", "rodzina");
  if (hasMother(f)) steps.push("mama");
  if (hasFather(f)) steps.push("tata");
  // Mother in hospital / unable / died / abandoned / took up work: only after the birth, with a father.
  if (f.stage === "born" && alive(f) && hasFather(f)) steps.push("trudne");
  if (alive(f) && (motherInsured(f) || fatherInsured(f))) steps.push("plan");
  steps.push("wynik");
  return steps;
}

/** Problems that block going to the next step (Polish, shown under the buttons). */
function problems(step: StepId, f: FormState): string[] {
  const out: string[] = [];
  const today = todayIso();
  if (step === "sytuacja" && !f.stage) out.push("Wybierz sytuację.");
  if (step === "dziecko") {
    if (!f.date) out.push("Podaj datę.");
    if (f.stage === "pregnancy" && f.date && f.date < today)
      out.push("Przewidywana data porodu minęła – jeśli dziecko już się urodziło, wybierz „Dziecko się urodziło”.");
    if (f.stage === "born" && f.date > today) out.push("Data porodu nie może być w przyszłości – wybierz „Jestem w ciąży”.");
    if (f.stage === "born" && f.outcome === "died") {
      if (!f.diedOn) out.push("Podaj datę zgonu dziecka.");
      else if (f.diedOn < f.date || f.diedOn > today) out.push("Data zgonu musi przypadać między porodem a dzisiejszym dniem.");
    }
    const count = num(f.children) ?? 0;
    if (count < 1 || count > 10) out.push("Liczba dzieci: od 1 do 10.");
    if ((f.stage === "adoption" || f.stage === "foster") && ((num(f.age) ?? -1) < 0 || (num(f.age) ?? 99) >= 18))
      out.push("Podaj wiek dziecka (0–17 lat).");
  }
  if (step === "mama" || step === "tata") {
    const p = step === "mama" ? f.mother : f.father;
    if (insured(p) && num(p.base) === null && !p.history.trim()) out.push("Podaj przeciętne wynagrodzenie (przychód) brutto.");
    if (step === "mama" && p.ended && !p.endedOn) out.push("Podaj dzień ustania ubezpieczenia.");
    if (step === "mama" && p.sick && (!p.sickStart || !p.sickEnd || p.sickEnd < p.sickStart)) out.push("Podaj okres zwolnienia lekarskiego.");
  }
  if (step === "trudne" && f.difficult !== "none" && !f.difficultFrom) out.push("Podaj datę zdarzenia.");
  return out;
}

// --- Profile for the API --------------------------------------------------------------------

function parentProfile(p: ParentForm, withWork: boolean): ParentProfile {
  const employee = p.employment === "employee";
  const history = p.history
    .split(/[\s;]+/)
    .map(num)
    .filter((v): v is number => v !== null)
    .slice(0, 12);
  return {
    employment: p.employment,
    sickness_insurance: employee ? "mandatory" : insured(p) && !p.childcareLeave ? "voluntary" : "none",
    start_relief: p.employment === "self_employed" && p.startRelief,
    average_monthly_base: num(p.base),
    monthly_bases: history.length ? history : null,
    working_time_fraction: employee && p.partTime ? Math.min(1, Math.max(0.01, (num(p.fraction) ?? 100) / 100)) : 1,
    employer_insured_count: employee || p.employment === "contract" ? (p.payer === "over20" ? 50 : 10) : null,
    contribution_debt: ["self_employed", "cooperating"].includes(p.employment) ? (num(p.debt) ?? 0) : 0,
    debt_paid_on: p.debtPaidOn || null,
    on_childcare_leave: p.childcareLeave,
    planned_work_fraction: withWork && employee ? (num(p.workPercent) ?? 0) / 100 : 0,
  };
}

export function buildProfile(f: FormState): FamilyProfile {
  const birth = isBirth(f);
  const child: FamilyProfile["child"] = {
    situation: birth ? "birth" : (f.stage as "adoption" | "foster"),
    children_count: num(f.children) ?? 1,
    za_zyciem: f.zaZyciem,
  };
  if (f.stage === "pregnancy") child.due_date = f.date;
  if (f.stage === "born") {
    child.birth_date = f.date;
    child.stillborn = f.outcome === "stillborn";
    child.died_on = f.outcome === "died" ? f.diedOn : null;
    child.children_surviving = (num(f.children) ?? 1) > 1 && f.outcome !== "alive" ? num(f.surviving) : null;
    if (f.premature && f.outcome !== "stillborn") {
      child.gestation_weeks = num(f.gestation);
      child.birth_weight_g = num(f.weight);
      child.hospital_days = num(f.hospitalDays) ?? 0;
      child.hospital_first_day = num(f.hospitalFirstDay);
    }
  }
  if (!birth) {
    child.placement_date = f.date;
    child.age_years = num(f.age);
    child.school_deferred = f.stage === "foster" && f.schoolDeferred;
  }
  const mother = hasMother(f)
    ? {
        ...parentProfile(f.mother, true),
        ...(birth && f.mother.ended
          ? {
              insurance_ended_on: f.mother.endedOn || null,
              job_loss_reason: f.mother.endReason,
              fixed_term_contract: f.mother.fixedTerm,
            }
          : {}),
        ...(birth && f.mother.sick
          ? {
              sick_leave_start: f.mother.sickStart,
              sick_leave_end: f.mother.sickEnd,
              sick_days_used_this_year: num(f.mother.sickUsed) ?? 0,
              age_over_50: f.mother.over50,
            }
          : {}),
      }
    : null;
  const father = hasFather(f) ? parentProfile(f.father, true) : null;
  const both = motherInsured(f) && fatherInsured(f);
  const difficult = f.stage === "born" && hasFather(f) && f.difficult !== "none";
  return {
    child,
    mother,
    father,
    mother_cannot_care: difficult ? (f.difficult as MotherCannotCare) : null,
    mother_situation_from: difficult ? f.difficultFrom || null : null,
    mother_situation_to: difficult ? f.difficultTo || null : null,
    plan: {
      maternity_before_birth_weeks: f.stage === "pregnancy" ? (num(f.beforeBirthWeeks) ?? 0) : 0,
      maternity_weeks_to_father: birth && both && !difficult ? (num(f.toFatherWeeks) ?? 0) : 0,
      parental_weeks_father: both ? num(f.fatherParentalWeeks) : null,
      parental_father_start: both && f.fatherParentalStart ? f.fatherParentalStart : null,
      parental_mother_start: f.motherParentalStart || null,
      parental_parts_mother: num(f.partsMother) ?? 1,
      parental_parts_father: num(f.partsFather) ?? 1,
      paternity_start: hasFather(f) && f.paternityStart ? f.paternityStart : null,
      paternity_parts: Number(f.paternityParts),
      use_supplementary_leave: f.supplementary,
      supplementary_taken_by: both ? f.supplementaryBy : fatherInsured(f) && !motherInsured(f) ? "father" : "mother",
      averaged_rate: f.averaged,
      averaged_rate_applied_on: f.averaged && f.averagedAppliedOn ? f.averagedAppliedOn : null,
    },
  };
}

/** Back from a profile (e.g. data "downloaded from ZUS") to the answers of the form. */
export function formFromProfile(p: FamilyProfile): FormState {
  const toParent = (src: ParentProfile | null | undefined): ParentForm => {
    const base = parent("");
    if (!src) return base;
    return {
      ...base,
      employment: src.employment,
      voluntary: src.sickness_insurance !== "none",
      startRelief: Boolean(src.start_relief),
      base: src.average_monthly_base != null ? String(src.average_monthly_base) : "",
      history: (src.monthly_bases ?? []).join(" "),
      partTime: (src.working_time_fraction ?? 1) < 1,
      fraction: String(Math.round((src.working_time_fraction ?? 1) * 100)),
      payer: (src.employer_insured_count ?? 50) > 20 ? "over20" : "upTo20",
      debt: src.contribution_debt ? String(src.contribution_debt) : "",
      debtPaidOn: src.debt_paid_on ?? "",
      childcareLeave: Boolean(src.on_childcare_leave),
      workPercent: String(Math.round((src.planned_work_fraction ?? 0) * 100)),
      ended: Boolean(src.insurance_ended_on),
      endedOn: src.insurance_ended_on ?? "",
      endReason: src.job_loss_reason ?? "employer_bankruptcy",
      fixedTerm: Boolean(src.fixed_term_contract),
      sick: Boolean(src.sick_leave_start),
      sickStart: src.sick_leave_start ?? "",
      sickEnd: src.sick_leave_end ?? "",
      sickUsed: String(src.sick_days_used_this_year ?? 0),
      over50: Boolean(src.age_over_50),
    };
  };
  const c = p.child;
  const stage: Stage = c.situation === "adoption" ? "adoption" : c.situation === "foster" ? "foster" : c.birth_date ? "born" : "pregnancy";
  const plan = p.plan ?? {};
  return {
    ...INITIAL,
    stage,
    date: (stage === "born" ? c.birth_date : stage === "pregnancy" ? c.due_date : c.placement_date) ?? "",
    children: String(c.children_count ?? 1),
    zaZyciem: Boolean(c.za_zyciem),
    outcome: c.stillborn ? "stillborn" : c.died_on ? "died" : "alive",
    diedOn: c.died_on ?? "",
    surviving: c.children_surviving != null ? String(c.children_surviving) : "",
    premature: Boolean(c.gestation_weeks || c.hospital_days),
    gestation: c.gestation_weeks ? String(c.gestation_weeks) : "",
    weight: c.birth_weight_g ? String(c.birth_weight_g) : "",
    hospitalDays: c.hospital_days ? String(c.hospital_days) : "",
    hospitalFirstDay: c.hospital_first_day ? String(c.hospital_first_day) : "",
    age: c.age_years != null ? String(c.age_years) : "3",
    schoolDeferred: Boolean(c.school_deferred),
    family: p.mother && p.father ? "both" : p.father && !p.mother ? "father" : "mother",
    mother: toParent(p.mother),
    father: toParent(p.father),
    difficult: p.mother_cannot_care ?? "none",
    difficultFrom: p.mother_situation_from ?? "",
    difficultTo: p.mother_situation_to ?? "",
    beforeBirthWeeks: String(plan.maternity_before_birth_weeks ?? 0),
    toFatherWeeks: String(plan.maternity_weeks_to_father ?? 0),
    fatherParentalWeeks: plan.parental_weeks_father != null ? String(plan.parental_weeks_father) : "9",
    fatherParentalStart: plan.parental_father_start ?? "",
    motherParentalStart: plan.parental_mother_start ?? "",
    paternityStart: plan.paternity_start ?? "",
    paternityParts: plan.paternity_parts === 2 ? "2" : "1",
    averaged: Boolean(plan.averaged_rate),
    averagedAppliedOn: plan.averaged_rate_applied_on ?? "",
  };
}

// --- Small building blocks ----------------------------------------------------------------

function Choice<T extends string>({
  legend,
  value,
  options,
  onChange,
  hint,
}: {
  legend: string;
  value: T | null;
  options: [T, string, string?][];
  onChange: (v: T) => void;
  hint?: string;
}) {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-1 text-sm font-bold">{legend}</legend>
      {hint && <p className="-mt-1 text-xs text-muted-foreground">{hint}</p>}
      <div className="grid gap-2 sm:grid-cols-2">
        {options.map(([id, label, desc]) => (
          <label
            key={id}
            className={cn(
              "flex cursor-pointer items-start gap-3 rounded-sm border p-3 text-sm",
              value === id ? "border-primary bg-primary/5" : "border-border hover:border-navy",
            )}
          >
            <input
              type="radio"
              className="mt-0.5 size-4 accent-primary"
              checked={value === id}
              onChange={() => onChange(id)}
            />
            <span className="flex flex-col gap-0.5">
              <span className="font-bold">{label}</span>
              {desc && <span className="text-xs text-muted-foreground">{desc}</span>}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function Stepper({ steps, current, onGo }: { steps: StepId[]; current: number; onGo: (i: number) => void }) {
  return (
    <ol className="flex flex-wrap gap-x-1 gap-y-2 border-b border-band-border pb-3 text-sm" aria-label="Kroki kalkulatora">
      {steps.map((s, i) => (
        <li key={s} className="flex items-center gap-1">
          <button
            type="button"
            disabled={i > current}
            onClick={() => onGo(i)}
            aria-current={i === current ? "step" : undefined}
            className={cn(
              "flex items-center gap-1.5 rounded-sm px-2 py-1",
              i === current ? "bg-primary font-bold text-white" : i < current ? "text-link hover:underline" : "text-muted-foreground",
            )}
          >
            <span
              className={cn(
                "flex size-5 items-center justify-center rounded-full text-[11px] font-bold",
                i === current ? "bg-white text-primary" : "border border-current",
              )}
            >
              {i + 1}
            </span>
            {STEP_TITLE[s]}
          </button>
          {i < steps.length - 1 && <ChevronRight className="size-3 text-muted-foreground" />}
        </li>
      ))}
    </ol>
  );
}

// --- Steps ---------------------------------------------------------------------------------

type StepProps = { f: FormState; set: <K extends keyof FormState>(k: K, v: FormState[K]) => void };

function SituationStep({ f, set }: StepProps) {
  return (
    <Choice<Stage>
      legend="Na jakim etapie jesteście?"
      value={f.stage}
      onChange={(v) => {
        set("stage", v);
        if (v !== "born") set("outcome", "alive");
      }}
      options={[
        ["pregnancy", "Jestem w ciąży", "Planujemy urlopy przed porodem – liczymy od przewidywanej daty porodu."],
        ["born", "Dziecko się urodziło", "Poród już nastąpił."],
        ["adoption", "Przysposobienie", "Przyjęliśmy dziecko (do 14 lat) i wystąpiliśmy do sądu o przysposobienie."],
        ["foster", "Rodzina zastępcza", "Niezawodowa rodzina zastępcza – dziecko do 7 lat (10 przy odroczeniu obowiązku szkolnego)."],
      ]}
    />
  );
}

function ChildStep({ f, set }: StepProps) {
  const many = (num(f.children) ?? 1) > 1;
  const today = todayIso();
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Field
        label={f.stage === "pregnancy" ? "Przewidywana data porodu" : f.stage === "born" ? "Data porodu" : "Data przyjęcia dziecka na wychowanie"}
        hint={f.stage === "pregnancy" ? "Z zaświadczenia lekarskiego." : undefined}
      >
        <Input
          type="date"
          value={f.date}
          min={f.stage === "pregnancy" ? today : undefined}
          max={f.stage === "born" ? today : undefined}
          onChange={(e) => set("date", e.target.value)}
        />
      </Field>
      <Field label={f.stage === "pregnancy" ? "Ile dzieci się urodzi?" : f.stage === "born" ? "Ile dzieci urodziło się przy porodzie?" : "Ile dzieci przyjęto jednocześnie?"}>
        <Input inputMode="numeric" value={f.children} onChange={(e) => set("children", e.target.value)} />
      </Field>
      {(f.stage === "adoption" || f.stage === "foster") && (
        <>
          <Field label="Wiek dziecka w dniu przyjęcia (lata)" hint="Np. 2,5">
            <Input inputMode="decimal" value={f.age} onChange={(e) => set("age", e.target.value)} />
          </Field>
          {f.stage === "foster" && (
            <Checkbox
              label="Podjęto decyzję o odroczeniu obowiązku szkolnego"
              checked={f.schoolDeferred}
              onChange={(e) => set("schoolDeferred", e.target.checked)}
            />
          )}
        </>
      )}
      {f.stage === "born" && (
        <div className="sm:col-span-2">
          <Choice<Outcome>
            legend="Co się stało po porodzie?"
            value={f.outcome}
            onChange={(v) => set("outcome", v)}
            hint="Wiemy, że to trudne pytanie. Od odpowiedzi zależy długość urlopu i dokumenty."
            options={[
              ["alive", many ? "Dzieci żyją" : "Dziecko żyje"],
              ["stillborn", "Dziecko urodziło się martwe", "Urlop macierzyński 8 tygodni i zasiłek pogrzebowy."],
              ["died", "Dziecko zmarło po porodzie"],
            ]}
          />
        </div>
      )}
      {f.stage === "born" && f.outcome === "died" && (
        <Field label="Data zgonu dziecka">
          <Input type="date" value={f.diedOn} min={f.date} max={today} onChange={(e) => set("diedOn", e.target.value)} />
        </Field>
      )}
      {f.stage === "born" && f.outcome !== "alive" && many && (
        <Field label="Ile dzieci żyje?">
          <Input inputMode="numeric" value={f.surviving} onChange={(e) => set("surviving", e.target.value)} />
        </Field>
      )}
      {f.outcome !== "stillborn" && (
        <Checkbox
          label="Zaświadczenie „Za życiem”"
          hint="Ciężkie i nieodwracalne upośledzenie albo nieuleczalna choroba – dłuższy urlop rodzicielski (65 / 67 tygodni)."
          checked={f.zaZyciem}
          onChange={(e) => set("zaZyciem", e.target.checked)}
          className="sm:col-span-2"
        />
      )}
      {f.stage === "born" && f.outcome !== "stillborn" && (
        <>
          <Checkbox
            label="Wcześniak albo dziecko w szpitalu po porodzie"
            hint="Uzupełniający urlop macierzyński: do 8 albo 15 tygodni."
            checked={f.premature}
            onChange={(e) => set("premature", e.target.checked)}
            className="sm:col-span-2"
          />
          {f.premature && (
            <div className="grid gap-4 sm:col-span-2 sm:grid-cols-4">
              <Field label="Tydzień ciąży przy porodzie">
                <Input inputMode="numeric" value={f.gestation} onChange={(e) => set("gestation", e.target.value)} />
              </Field>
              <Field label="Masa urodzeniowa (g)">
                <Input inputMode="numeric" value={f.weight} onChange={(e) => set("weight", e.target.value)} />
              </Field>
              <Field label="Dni pobytu w szpitalu">
                <Input inputMode="numeric" value={f.hospitalDays} onChange={(e) => set("hospitalDays", e.target.value)} />
              </Field>
              <Field label="Od którego dnia po porodzie?" hint="Ważne przy porodzie w terminie (od 5. do 28. dnia).">
                <Input inputMode="numeric" value={f.hospitalFirstDay} onChange={(e) => set("hospitalFirstDay", e.target.value)} />
              </Field>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function FamilyStep({ f, set }: StepProps) {
  if (isBirth(f))
    return (
      <Choice<Family>
        legend="Czy w rodzinie jest tata, który może korzystać z urlopów i zasiłków?"
        value={f.family === "father" ? "both" : f.family}
        onChange={(v) => set("family", v)}
        options={[
          ["both", "Tak – mama i tata", "Pokażemy podział urlopów i uprawnienia taty."],
          ["mother", "Nie – tylko mama", "Nie będziemy pytać o tatę ani o podział urlopów."],
        ]}
      />
    );
  return (
    <Choice<Family>
      legend="Kto przyjmuje dziecko na wychowanie?"
      value={f.family}
      onChange={(v) => set("family", v)}
      options={[
        ["both", "Mama i tata"],
        ["mother", "Tylko mama"],
        ["father", "Tylko tata"],
      ]}
    />
  );
}

function ParentStep({ f, set, who }: StepProps & { who: "mother" | "father" }) {
  const p = f[who];
  const upd = (patch: Partial<ParentForm>) => set(who, { ...p, ...patch });
  const employee = p.employment === "employee";
  const business = p.employment === "self_employed" || p.employment === "cooperating";
  const mother = who === "mother";
  const event = f.stage === "pregnancy" ? "porodu" : f.stage === "born" ? "porodu" : "przyjęcia dziecka";
  return (
    <div className="flex flex-col gap-4">
      <Field label={`Podstawa ubezpieczenia ${mother ? "mamy" : "taty"} w dniu ${event}`}>
        <Select value={p.employment} onChange={(e) => upd({ employment: e.target.value as EmploymentType })}>
          {EMPLOYMENT.map(([id, label]) => (
            <option key={id} value={id}>
              {label}
            </option>
          ))}
        </Select>
      </Field>
      {(p.employment === "contract" || business) && (
        <Checkbox
          label="Opłacam dobrowolne ubezpieczenie chorobowe"
          hint="Bez ubezpieczenia chorobowego w dniu porodu zasiłek macierzyński nie przysługuje. Zgłoszenia nie można złożyć wstecz."
          checked={p.voluntary}
          onChange={(e) => upd({ voluntary: e.target.checked })}
        />
      )}
      {p.employment === "self_employed" && (
        <Checkbox
          label="Korzystam z ulgi na start"
          hint="W uldze na start nie ma ubezpieczeń społecznych – także chorobowego."
          checked={p.startRelief}
          onChange={(e) => upd({ startRelief: e.target.checked })}
        />
      )}
      {p.employment === "other" && (
        <Checkbox
          label="Podlegam ubezpieczeniu chorobowemu"
          checked={p.otherInsured}
          onChange={(e) => upd({ otherInsured: e.target.checked })}
        />
      )}
      {(employee || p.employment === "unemployed") && (
        <Checkbox
          label={`${mother ? "Jestem" : "Tata jest"} na urlopie wychowawczym (z poprzednim dzieckiem)`}
          hint="Poród w czasie urlopu wychowawczego daje prawo do zasiłku macierzyńskiego."
          checked={p.childcareLeave}
          onChange={(e) => upd({ childcareLeave: e.target.checked })}
        />
      )}
      {insured(p) && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field
            label={employee ? "Przeciętne miesięczne wynagrodzenie brutto (zł)" : "Przeciętna podstawa składki chorobowej (zł)"}
            hint="Z 12 miesięcy przed miesiącem porodu (albo z pełnych miesięcy ubezpieczenia)."
          >
            <Input inputMode="decimal" value={p.base} onChange={(e) => upd({ base: e.target.value })} />
          </Field>
          <Field label="Albo kwoty z kolejnych miesięcy (opcjonalnie)" hint="Oddziel spacją, do 12 wartości – policzymy średnią.">
            <Input value={p.history} onChange={(e) => upd({ history: e.target.value })} placeholder="np. 6000 6200 5800" />
          </Field>
          {(employee || p.employment === "contract") && (
            <Field label="Ilu ubezpieczonych zgłasza płatnik składek?" hint="Powyżej 20 osób zasiłek wypłaca pracodawca, w pozostałych przypadkach ZUS.">
              <Select value={p.payer} onChange={(e) => upd({ payer: e.target.value as ParentForm["payer"] })}>
                <option value="over20">Więcej niż 20</option>
                <option value="upTo20">20 lub mniej</option>
              </Select>
            </Field>
          )}
          {employee && (
            <div className="flex flex-col gap-2">
              <Checkbox label="Pracuję w niepełnym wymiarze" checked={p.partTime} onChange={(e) => upd({ partTime: e.target.checked })} />
              {p.partTime && (
                <Field label="Wymiar etatu (%)">
                  <Input inputMode="numeric" value={p.fraction} onChange={(e) => upd({ fraction: e.target.value })} />
                </Field>
              )}
            </div>
          )}
          {business && (
            <>
              <Field label="Zadłużenie z tytułu składek (zł)" hint="Powyżej 1% płacy minimalnej zasiłek jest wstrzymany do spłaty.">
                <Input inputMode="decimal" value={p.debt} onChange={(e) => upd({ debt: e.target.value })} />
              </Field>
              {(num(p.debt) ?? 0) > 0 && (
                <Field label="Dzień spłaty zadłużenia (jeśli spłacone)">
                  <Input type="date" value={p.debtPaidOn} onChange={(e) => upd({ debtPaidOn: e.target.value })} />
                </Field>
              )}
            </>
          )}
        </div>
      )}
      {mother && isBirth(f) && employee && (
        <Checkbox
          label="Umowa o pracę ustała w czasie ciąży"
          hint="Np. upadłość lub likwidacja pracodawcy, rozwiązanie z naruszeniem prawa, koniec umowy na czas określony."
          checked={p.ended}
          onChange={(e) => upd({ ended: e.target.checked })}
        />
      )}
      {mother && isBirth(f) && employee && p.ended && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Ostatni dzień ubezpieczenia">
            <Input type="date" value={p.endedOn} onChange={(e) => upd({ endedOn: e.target.value })} />
          </Field>
          <Field label="Przyczyna">
            <Select value={p.endReason} onChange={(e) => upd({ endReason: e.target.value as ParentForm["endReason"] })}>
              <option value="employer_bankruptcy">Upadłość, likwidacja albo śmierć pracodawcy</option>
              <option value="unlawful_dismissal">Rozwiązanie z naruszeniem prawa (wyrok sądu)</option>
              <option value="other">Inna przyczyna</option>
            </Select>
          </Field>
          <Checkbox
            label="Umowa na czas określony przedłużona do dnia porodu"
            hint="Umowa, która skończyłaby się po 3. miesiącu ciąży, przedłuża się do porodu (art. 177 § 3 KP)."
            checked={p.fixedTerm}
            onChange={(e) => upd({ fixedTerm: e.target.checked })}
            className="sm:col-span-2"
          />
        </div>
      )}
      {mother && isBirth(f) && insured(p) && (
        <>
          <Checkbox
            label="Zwolnienie lekarskie w ciąży (kod B)"
            checked={p.sick}
            onChange={(e) => upd({ sick: e.target.checked })}
          />
          {p.sick && (
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Zwolnienie od">
                <Input type="date" value={p.sickStart} onChange={(e) => upd({ sickStart: e.target.value })} />
              </Field>
              <Field label="Zwolnienie do">
                <Input type="date" value={p.sickEnd} onChange={(e) => upd({ sickEnd: e.target.value })} />
              </Field>
              {employee && (
                <>
                  <Field label="Dni chorobowego już opłaconych przez pracodawcę w tym roku">
                    <Input inputMode="numeric" value={p.sickUsed} onChange={(e) => upd({ sickUsed: e.target.value })} />
                  </Field>
                  <Checkbox
                    label="Ukończyłam 50 lat (w poprzednim roku)"
                    hint="Pracodawca płaci wtedy 14 dni zamiast 33."
                    checked={p.over50}
                    onChange={(e) => upd({ over50: e.target.checked })}
                  />
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function DifficultStep({ f, set }: StepProps) {
  const mInsured = motherInsured(f);
  const options: [FormState["difficult"], string, string?][] = [
    ["none", "Nie dotyczy", "Najczęstsza sytuacja."],
    ["hospital", "Mama przebywa w szpitalu", mInsured ? "Po co najmniej 8 tygodniach urlopu – na ten czas urlop wykorzystuje tata." : undefined],
    ["disabled", "Mama ma orzeczenie o niezdolności do samodzielnej egzystencji"],
    ["death", "Mama zmarła"],
    ["abandoned", "Mama porzuciła dziecko"],
  ];
  if (!mInsured) options.push(["employed", "Mama (bez ubezpieczenia) podjęła pracę", "Co najmniej na pół etatu – zasiłek dla taty na czas jej pracy."]);
  return (
    <div className="flex flex-col gap-4">
      <Choice
        legend="Czy wydarzyło się coś, przez co mama nie może opiekować się dzieckiem?"
        value={f.difficult}
        onChange={(v) => set("difficult", v)}
        options={options}
      />
      {f.difficult !== "none" && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={f.difficult === "hospital" ? "Przyjęcie do szpitala" : f.difficult === "employed" ? "Początek pracy" : "Data zdarzenia"}>
            <Input type="date" value={f.difficultFrom} min={f.date} onChange={(e) => set("difficultFrom", e.target.value)} />
          </Field>
          {(f.difficult === "hospital" || f.difficult === "employed") && (
            <Field label={f.difficult === "hospital" ? "Wypis (jeśli znany)" : "Koniec pracy (jeśli znany)"}>
              <Input type="date" value={f.difficultTo} min={f.difficultFrom} onChange={(e) => set("difficultTo", e.target.value)} />
            </Field>
          )}
        </div>
      )}
    </div>
  );
}

function PlanStep({ f, set }: StepProps) {
  const m = motherInsured(f);
  const t = fatherInsured(f);
  const both = m && t;
  const takenIn = f.stage === "adoption" || f.stage === "foster";
  const deadline21 = f.date ? addDays(f.date, 21) : "";
  const averagedOpen = f.stage === "pregnancy" || (f.date !== "" && todayIso() <= deadline21);
  const supplementaryPossible = f.stage === "born" && f.premature && (num(f.hospitalDays) ?? 0) > 0;
  const noDifficulty = f.difficult === "none";
  return (
    <div className="flex flex-col gap-6">
      {f.stage === "pregnancy" && m && (
        <Field label="Ile tygodni urlopu macierzyńskiego mama weźmie przed porodem?" hint="Od 0 do 6 tygodni – wliczają się do 20 tygodni urlopu.">
          <Select value={f.beforeBirthWeeks} onChange={(e) => set("beforeBirthWeeks", e.target.value)}>
            {[0, 1, 2, 3, 4, 5, 6].map((w) => (
              <option key={w} value={w}>
                {w}
              </option>
            ))}
          </Select>
        </Field>
      )}
      {both && !takenIn && noDifficulty && f.outcome === "alive" && (
        <Field
          label="Ile tygodni urlopu macierzyńskiego przejmie tata?"
          hint="Mama musi wykorzystać po porodzie co najmniej 14 tygodni; tata bierze resztę."
        >
          <Input inputMode="numeric" value={f.toFatherWeeks} onChange={(e) => set("toFatherWeeks", e.target.value)} />
        </Field>
      )}
      {both && f.outcome !== "died" && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Ile tygodni urlopu rodzicielskiego weźmie tata?" hint="9 tygodni jest tylko dla taty – nie można ich przekazać mamie.">
            <Input inputMode="numeric" value={f.fatherParentalWeeks} onChange={(e) => set("fatherParentalWeeks", e.target.value)} />
          </Field>
          <Field label="Od kiedy urlop rodzicielski taty?" hint="Puste = zaraz po urlopie mamy. Można też równolegle z mamą.">
            <Input type="date" value={f.fatherParentalStart} onChange={(e) => set("fatherParentalStart", e.target.value)} />
          </Field>
        </div>
      )}
      {t && !m && (
        <p className="rounded-sm bg-muted p-3 text-sm">
          Mama nie ma tytułu do zasiłku – tata może wykorzystać cały urlop rodzicielski i (osobno) urlop ojcowski.
        </p>
      )}
      {t && (f.stage === "pregnancy" || f.stage === "born" || f.stage === "adoption") && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Początek urlopu ojcowskiego" hint="2 tygodnie do ukończenia przez dziecko 12 miesięcy. Puste = od dnia porodu.">
            <Input type="date" value={f.paternityStart} onChange={(e) => set("paternityStart", e.target.value)} />
          </Field>
          <Field label="Urlop ojcowski w częściach">
            <Select value={f.paternityParts} onChange={(e) => set("paternityParts", e.target.value as "1" | "2")}>
              <option value="1">Jednorazowo</option>
              <option value="2">W 2 częściach (po tygodniu)</option>
            </Select>
          </Field>
        </div>
      )}
      {(["mother", "father"] as const).map((who) => {
        const p = f[who];
        if (!(who === "mother" ? m : t) || p.employment !== "employee" || f.outcome === "died") return null;
        return (
          <Field
            key={who}
            label={`Czy ${who === "mother" ? "mama" : "tata"} będzie pracować w czasie urlopu rodzicielskiego? (% etatu)`}
            hint="0 = pełny urlop. Najwyżej 50% etatu – urlop wydłuża się proporcjonalnie, zasiłek jest niższy."
          >
            <Select value={p.workPercent} onChange={(e) => set(who, { ...p, workPercent: e.target.value })}>
              {[0, 10, 20, 25, 30, 40, 50].map((v) => (
                <option key={v} value={v}>
                  {v}%
                </option>
              ))}
            </Select>
          </Field>
        );
      })}
      {supplementaryPossible && (
        <div className="flex flex-col gap-3">
          <Checkbox
            label="Skorzystamy z uzupełniającego urlopu macierzyńskiego"
            hint="Bezpośrednio po urlopie macierzyńskim, jednorazowo, przez jedno z rodziców."
            checked={f.supplementary}
            onChange={(e) => set("supplementary", e.target.checked)}
          />
          {f.supplementary && both && (
            <Field label="Kto weźmie urlop uzupełniający?">
              <Select value={f.supplementaryBy} onChange={(e) => set("supplementaryBy", e.target.value as "mother" | "father")}>
                <option value="mother">Mama</option>
                <option value="father">Tata</option>
              </Select>
            </Field>
          )}
        </div>
      )}
      {f.outcome !== "died" && (m || (takenIn && t)) && (
        <div className="flex flex-col gap-3">
          {averagedOpen ? (
            <Checkbox
              label="Złożę wniosek o zasiłek w stałej stawce 81,5%"
              hint={`Za cały urlop macierzyński i rodzicielski zamiast 100% + 70%. Wniosek najpóźniej 21 dni po ${takenIn ? "przyjęciu dziecka" : "porodzie"}${deadline21 ? ` (do ${formatDate(deadline21)})` : ""}.`}
              checked={f.averaged}
              onChange={(e) => set("averaged", e.target.checked)}
            />
          ) : (
            <>
              <Checkbox
                label="Wniosek o stawkę 81,5% został złożony w ciągu 21 dni"
                hint="Termin minął – jeśli wniosku nie było, zasiłek wynosi 100% za macierzyński i 70% za rodzicielski."
                checked={f.averaged}
                onChange={(e) => set("averaged", e.target.checked)}
              />
              {f.averaged && (
                <Field label="Data złożenia wniosku">
                  <Input type="date" value={f.averagedAppliedOn} onChange={(e) => set("averagedAppliedOn", e.target.value)} />
                </Field>
              )}
            </>
          )}
        </div>
      )}
      <details className="text-sm">
        <summary className="cursor-pointer font-bold text-link">Więcej opcji</summary>
        <div className="mt-3 grid gap-4 sm:grid-cols-3">
          {m && (
            <Field label="Początek urlopu rodzicielskiego mamy" hint="Puste = zaraz po macierzyńskim.">
              <Input type="date" value={f.motherParentalStart} onChange={(e) => set("motherParentalStart", e.target.value)} />
            </Field>
          )}
          {m && (
            <Field label="Na ile części mama dzieli urlop rodzicielski?" hint="Najwyżej 5.">
              <Input inputMode="numeric" value={f.partsMother} onChange={(e) => set("partsMother", e.target.value)} />
            </Field>
          )}
          {t && (
            <Field label="Na ile części tata dzieli urlop rodzicielski?" hint="Najwyżej 5.">
              <Input inputMode="numeric" value={f.partsFather} onChange={(e) => set("partsFather", e.target.value)} />
            </Field>
          )}
        </div>
      </details>
    </div>
  );
}

// --- The calculator -------------------------------------------------------------------------

export function CalculatorForm() {
  const [form, setForm] = useState<FormState>(INITIAL);
  const [step, setStep] = useState(0);
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tried, setTried] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const saved = loadLastForm<FormState>();
    if (saved && saved.stage !== undefined) return setForm({ ...INITIAL, ...saved, mother: { ...INITIAL.mother, ...saved.mother }, father: { ...INITIAL.father, ...saved.father } });
    const profile = loadLastProfile<FamilyProfile>();
    if (profile) setForm(formFromProfile(profile));
  }, []);

  const steps = useMemo(() => stepsFor(form), [form]);
  const current = steps[Math.min(step, steps.length - 1)];
  const issues = problems(current, form);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((f) => ({ ...f, [key]: value }));
    setResult(null);
  };

  async function calculate() {
    setLoading(true);
    setError(null);
    try {
      const profile = buildProfile(form);
      const evaluated = await evaluateFamily(profile);
      saveLastResult(evaluated);
      saveLastForm(form);
      saveLastProfile(profile);
      setResult(evaluated);
    } catch (err) {
      const message = err instanceof Error ? err.message : "";
      const detail = /"detail":\s*"([^"]+)"/.exec(message)?.[1];
      setError(detail ? `Ten plan nie jest zgodny z przepisami: ${detail}` : "Nie udało się policzyć. Sprawdź dane i spróbuj ponownie.");
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
    if (steps[target] === "wynik") void calculate();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function go(i: number) {
    setStep(i);
    setTried(false);
    if (steps[i] === "wynik") void calculate();
  }

  return (
    <div className="flex flex-col gap-6">
      <Stepper steps={steps} current={Math.min(step, steps.length - 1)} onGo={go} />
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
            {loading && <Loader2 className="animate-spin text-muted-foreground" aria-label="Liczę" />}
            {error && (
              <div role="alert" className="flex flex-col items-start gap-3 rounded-sm border border-destructive/40 bg-destructive/5 p-4 text-sm">
                {error}
                {steps.includes("plan") && (
                  <Button type="button" variant="outline" onClick={() => go(steps.indexOf("plan"))}>
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
                    Zobacz oś czasu i wnioski <ChevronRight className="size-4" />
                  </Link>
                </div>
              </>
            )}
          </>
        )}
      </section>
      {tried && issues.length > 0 && (
        <ul role="alert" className="list-disc rounded-sm bg-destructive/5 p-3 pl-8 text-sm text-destructive">
          {issues.map((i) => (
            <li key={i}>{i}</li>
          ))}
        </ul>
      )}
      <div className="flex flex-wrap justify-between gap-3 border-t border-band-border pt-4">
        <div className="flex gap-3">
          {step > 0 && (
            <Button type="button" variant="outline" onClick={() => go(step - 1)}>
              <ChevronLeft /> Wstecz
            </Button>
          )}
          {current !== "wynik" && (
            <Button type="button" onClick={next}>
              {steps[step + 1] === "wynik" ? "Policz zasiłki i urlopy" : "Dalej"} <ChevronRight />
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
