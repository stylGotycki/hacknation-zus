import {
  type EmploymentType,
  type FamilyProfile,
  type MotherCannotCare,
  type ParentProfile,
} from "@/lib/api";
import { toIsoDate } from "@/lib/format";

export type Stage = "pregnancy" | "born" | "adoption" | "foster";

export type Outcome = "alive" | "stillborn" | "died";

export type Family = "both" | "mother" | "father";

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

export const EMPLOYMENT: [EmploymentType, string][] = [
  ["employee", "Umowa o pracę"],
  ["contract", "Umowa zlecenie"],
  ["self_employed", "Działalność gospodarcza"],
  ["cooperating", "Osoba współpracująca przy działalności"],
  ["unemployed", "Nie pracuję / bezrobocie / studia"],
  ["other", "Inny tytuł (np. umowa o dzieło)"],
];

export const parent = (base: string): ParentForm => ({
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

export const num = (value: string): number | null => {
  const parsed = Number(value.replace(",", ".").replace(/\s/g, ""));
  return value.trim() === "" || Number.isNaN(parsed) ? null : parsed;
};

export const todayIso = () => toIsoDate(new Date());

export const addDays = (iso: string, days: number) => {
  const d = new Date(`${iso}T12:00:00`);
  d.setDate(d.getDate() + days);
  return toIsoDate(d);
};

export const isBirth = (f: FormState) =>
  f.stage === "pregnancy" || f.stage === "born";

export const hasMother = (f: FormState) => isBirth(f) || f.family !== "father";

export const hasFather = (f: FormState) =>
  isBirth(f) ? f.family === "both" : f.family !== "mother";

export const alive = (f: FormState) =>
  f.stage !== "born" || f.outcome !== "stillborn";

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

export const motherInsured = (f: FormState) =>
  hasMother(f) && (insured(f.mother) || (f.mother.ended && isBirth(f)));

export const fatherInsured = (f: FormState) =>
  hasFather(f) && insured(f.father);

export type StepId =
  | "sytuacja"
  | "dziecko"
  | "rodzina"
  | "mama"
  | "tata"
  | "trudne"
  | "plan"
  | "wynik";

export const STEP_TITLE: Record<StepId, string> = {
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
export function problems(step: StepId, f: FormState): string[] {
  const out: string[] = [];
  const today = todayIso();
  if (step === "sytuacja" && !f.stage) out.push("Wybierz sytuację.");
  if (step === "dziecko") {
    if (!f.date) out.push("Podaj datę.");
    if (f.stage === "pregnancy" && f.date && f.date < today)
      out.push(
        "Przewidywana data porodu minęła – jeśli dziecko już się urodziło, wybierz „Dziecko się urodziło”.",
      );
    if (f.stage === "born" && f.date > today)
      out.push(
        "Data porodu nie może być w przyszłości – wybierz „Jestem w ciąży”.",
      );
    if (f.stage === "born" && f.outcome === "died") {
      if (!f.diedOn) out.push("Podaj datę zgonu dziecka.");
      else if (f.diedOn < f.date || f.diedOn > today)
        out.push(
          "Data zgonu musi przypadać między porodem a dzisiejszym dniem.",
        );
    }
    const count = num(f.children) ?? 0;
    if (count < 1 || count > 10) out.push("Liczba dzieci: od 1 do 10.");
    if (
      (f.stage === "adoption" || f.stage === "foster") &&
      ((num(f.age) ?? -1) < 0 || (num(f.age) ?? 99) >= 18)
    )
      out.push("Podaj wiek dziecka (0–17 lat).");
  }
  if (step === "mama" || step === "tata") {
    const p = step === "mama" ? f.mother : f.father;
    if (insured(p) && num(p.base) === null && !p.history.trim())
      out.push("Podaj przeciętne wynagrodzenie (przychód) brutto.");
    if (step === "mama" && p.ended && !p.endedOn)
      out.push("Podaj dzień ustania ubezpieczenia.");
    if (
      step === "mama" &&
      p.sick &&
      (!p.sickStart || !p.sickEnd || p.sickEnd < p.sickStart)
    )
      out.push("Podaj okres zwolnienia lekarskiego.");
  }
  if (step === "trudne" && f.difficult !== "none" && !f.difficultFrom)
    out.push("Podaj datę zdarzenia.");
  return out;
}

export function parentProfile(p: ParentForm, withWork: boolean): ParentProfile {
  const employee = p.employment === "employee";
  const history = p.history
    .split(/[\s;]+/)
    .map(num)
    .filter((v): v is number => v !== null)
    .slice(0, 12);
  return {
    employment: p.employment,
    sickness_insurance: employee
      ? "mandatory"
      : insured(p) && !p.childcareLeave
        ? "voluntary"
        : "none",
    start_relief: p.employment === "self_employed" && p.startRelief,
    average_monthly_base: num(p.base),
    monthly_bases: history.length ? history : null,
    working_time_fraction:
      employee && p.partTime
        ? Math.min(1, Math.max(0.01, (num(p.fraction) ?? 100) / 100))
        : 1,
    employer_insured_count:
      employee || p.employment === "contract"
        ? p.payer === "over20"
          ? 50
          : 10
        : null,
    contribution_debt: ["self_employed", "cooperating"].includes(p.employment)
      ? (num(p.debt) ?? 0)
      : 0,
    debt_paid_on: p.debtPaidOn || null,
    on_childcare_leave: p.childcareLeave,
    planned_work_fraction:
      withWork && employee ? (num(p.workPercent) ?? 0) / 100 : 0,
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
    child.children_surviving =
      (num(f.children) ?? 1) > 1 && f.outcome !== "alive"
        ? num(f.surviving)
        : null;
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
  const difficult =
    f.stage === "born" && hasFather(f) && f.difficult !== "none";
  return {
    child,
    mother,
    father,
    mother_cannot_care: difficult ? (f.difficult as MotherCannotCare) : null,
    mother_situation_from: difficult ? f.difficultFrom || null : null,
    mother_situation_to: difficult ? f.difficultTo || null : null,
    plan: {
      maternity_before_birth_weeks:
        f.stage === "pregnancy" ? (num(f.beforeBirthWeeks) ?? 0) : 0,
      maternity_weeks_to_father:
        birth && both && !difficult ? (num(f.toFatherWeeks) ?? 0) : 0,
      parental_weeks_father: both ? num(f.fatherParentalWeeks) : null,
      parental_father_start:
        both && f.fatherParentalStart ? f.fatherParentalStart : null,
      parental_mother_start: f.motherParentalStart || null,
      parental_parts_mother: num(f.partsMother) ?? 1,
      parental_parts_father: num(f.partsFather) ?? 1,
      paternity_start:
        hasFather(f) && f.paternityStart ? f.paternityStart : null,
      paternity_parts: Number(f.paternityParts),
      use_supplementary_leave: f.supplementary,
      supplementary_taken_by: both
        ? f.supplementaryBy
        : fatherInsured(f) && !motherInsured(f)
          ? "father"
          : "mother",
      averaged_rate: f.averaged,
      averaged_rate_applied_on:
        f.averaged && f.averagedAppliedOn ? f.averagedAppliedOn : null,
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
      base:
        src.average_monthly_base != null
          ? String(src.average_monthly_base)
          : "",
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
  const stage: Stage =
    c.situation === "adoption"
      ? "adoption"
      : c.situation === "foster"
        ? "foster"
        : c.birth_date
          ? "born"
          : "pregnancy";
  const plan = p.plan ?? {};
  return {
    ...INITIAL,
    stage,
    date:
      (stage === "born"
        ? c.birth_date
        : stage === "pregnancy"
          ? c.due_date
          : c.placement_date) ?? "",
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
    family:
      p.mother && p.father
        ? "both"
        : p.father && !p.mother
          ? "father"
          : "mother",
    mother: toParent(p.mother),
    father: toParent(p.father),
    difficult: p.mother_cannot_care ?? "none",
    difficultFrom: p.mother_situation_from ?? "",
    difficultTo: p.mother_situation_to ?? "",
    beforeBirthWeeks: String(plan.maternity_before_birth_weeks ?? 0),
    toFatherWeeks: String(plan.maternity_weeks_to_father ?? 0),
    fatherParentalWeeks:
      plan.parental_weeks_father != null
        ? String(plan.parental_weeks_father)
        : "9",
    fatherParentalStart: plan.parental_father_start ?? "",
    motherParentalStart: plan.parental_mother_start ?? "",
    paternityStart: plan.paternity_start ?? "",
    paternityParts: plan.paternity_parts === 2 ? "2" : "1",
    averaged: Boolean(plan.averaged_rate),
    averagedAppliedOn: plan.averaged_rate_applied_on ?? "",
  };
}
