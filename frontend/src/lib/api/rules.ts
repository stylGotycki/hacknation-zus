import { api } from "./client";

// --- Types mirroring backend schemas (keep in sync with /api/docs) -----------------------

export type LegalParameter = {
  key: string;
  value: unknown;
  valid_from: string;
  valid_to: string | null;
  description_pl: string;
  legal_basis: string;
  /** Polish name, group and unit for the admin panel (weeks, days, months, years, pct, pln, people, number). */
  label_pl: string;
  group_pl: string;
  unit: string;
  value_labels: Record<string, string>;
};

export type ParametersResponse = { date: string; parameters: LegalParameter[] };

// --- Rules engine (POST /api/rules/evaluate) --------------------------------------------------

export type Situation = "birth" | "adoption" | "foster";
export type EmploymentType =
  | "employee"
  | "contract"
  | "self_employed"
  | "cooperating"
  | "unemployed"
  | "other";
export type InsuranceKind = "none" | "mandatory" | "voluntary";
export type Person = "mother" | "father" | "family";

export type ParentProfile = {
  employment: EmploymentType;
  sickness_insurance?: InsuranceKind | null;
  insured_days?: number | null;
  insurance_ended_on?: string | null;
  job_loss_reason?:
    "employer_bankruptcy" | "unlawful_dismissal" | "other" | null;
  average_monthly_base?: number | null;
  monthly_bases?: number[] | null;
  working_time_fraction?: number;
  fixed_term_contract?: boolean;
  employer_insured_count?: number | null;
  start_relief?: boolean;
  contribution_debt?: number;
  debt_paid_on?: string | null;
  planned_work_fraction?: number;
  sick_leave_start?: string | null;
  sick_leave_end?: string | null;
  sick_days_used_this_year?: number;
  age_over_50?: boolean;
  on_childcare_leave?: boolean;
};

export type ChildProfile = {
  situation?: Situation;
  birth_date?: string | null;
  due_date?: string | null;
  placement_date?: string | null;
  children_count?: number;
  za_zyciem?: boolean;
  stillborn?: boolean;
  died_on?: string | null;
  children_surviving?: number | null;
  gestation_weeks?: number | null;
  birth_weight_g?: number | null;
  hospital_days?: number;
  hospital_first_day?: number | null;
  age_years?: number | null;
  school_deferred?: boolean;
};

export type Plan = {
  maternity_before_birth_weeks?: number;
  maternity_weeks_to_father?: number;
  parental_weeks_father?: number | null;
  parental_father_start?: string | null;
  parental_mother_start?: string | null;
  parental_parts_mother?: number;
  parental_parts_father?: number;
  paternity_start?: string | null;
  paternity_parts?: number;
  use_supplementary_leave?: boolean;
  supplementary_taken_by?: "mother" | "father";
  averaged_rate?: boolean;
  averaged_rate_applied_on?: string | null;
};

export type MotherCannotCare =
  "hospital" | "disabled" | "death" | "abandoned" | "employed";

export type FamilyProfile = {
  child: ChildProfile;
  mother?: ParentProfile | null;
  father?: ParentProfile | null;
  mother_cannot_care?: MotherCannotCare | null;
  mother_situation_from?: string | null;
  mother_situation_to?: string | null;
  plan?: Plan;
};

export type BenefitStatus =
  "eligible" | "conditional" | "not_eligible" | "info";

export type BenefitResult = {
  code: string;
  person: Person;
  title_pl: string;
  status: BenefitStatus;
  summary_pl: string;
  reasons_pl: string[];
  legal_basis: string[];
  weeks: number | null;
  days: number | null;
  rate: number | null;
  monthly_gross: number | null;
  total_gross: number | null;
  start: string | null;
  end: string | null;
  payer: "employer" | "zus" | null;
  apply_to_pl: string | null;
  documents_pl: string[];
  deadline: string | null;
  days_left: number | null;
  deadline_note_pl: string | null;
  periods: string[];
};

export type LeavePeriod = {
  id: string;
  person: Person;
  kind:
    | "pregnancy_sickness"
    | "maternity"
    | "maternity_equivalent"
    | "supplementary"
    | "parental"
    | "paternity";
  label_pl: string;
  start: string;
  end: string;
  days: number;
  weeks: number;
  paid: boolean;
  rate: number | null;
  monthly_gross: number | null;
  total_gross: number | null;
  work_fraction: number;
  payer: "employer" | "zus" | null;
  rule: string | null;
  /** Allowance raised to the parental benefit amount (UZ art. 31 ust. 3a). */
  raised_to_minimum?: boolean;
};

export type Risk = {
  code: string;
  severity: "high" | "medium" | "info";
  person: Person;
  title_pl: string;
  text_pl: string;
  legal_basis: string | null;
};

export type Deadline = {
  code: string;
  person: Person;
  kind: "apply" | "use_by";
  title_pl: string;
  due: string;
  days_left: number;
  status: "open" | "soon" | "overdue";
  note_pl: string;
  benefit_code: string | null;
  legal_basis: string | null;
  /** Advice once the deadline has passed: what is lost, what can still be done. */
  late_pl: string | null;
};

export type AveragedRateComparison = {
  standard_total: number | null;
  averaged_total: number | null;
  better: "standard" | "averaged" | "equal" | null;
  deadline: string;
  still_possible: boolean;
  note_pl: string;
};

export type PaymentLine = {
  label_pl: string;
  days: number;
  amount_gross: number;
};
/** One expected transfer: the allowance for the days of one calendar month. */
export type Payment = {
  id: string;
  person: Person;
  month: string;
  date: string;
  days: number;
  amount_gross: number;
  payer: "employer" | "zus" | null;
  lines: PaymentLine[];
};

export type EvaluationResult = {
  params_date: string;
  situation: Situation;
  event_date: string;
  event_is_estimate: boolean;
  bases: {
    person: Person;
    gross_base: number | null;
    net_base: number | null;
    minimum_wage_applied: boolean;
    note_pl: string;
  }[];
  benefits: BenefitResult[];
  timeline: LeavePeriod[];
  payments: Payment[];
  risks: Risk[];
  deadlines: Deadline[];
  averaged_rate: AveragedRateComparison | null;
  totals: {
    mother_gross: number;
    father_gross: number;
    family_gross: number;
    family_net_estimate: number;
  };
  situation_tags: string[];
  assumptions_pl: string[];
  info_pl: string[];
  rules_version: string | null;
  rule_errors: Record<string, string>;
};

export function evaluateFamily(profile: FamilyProfile, date?: string) {
  const query = date ? `?date=${encodeURIComponent(date)}` : "";
  return api<EvaluationResult>(`/rules/evaluate${query}`, {
    method: "POST",
    body: JSON.stringify(profile),
  });
}

/** A ready-made case (built from the types of cases ZUS supplied) – GET /api/scenarios. */
export type SampleCase = {
  id: string;
  title_pl: string;
  description_pl: string;
  tags: string[];
  profile: FamilyProfile;
};
export const listSampleCases = () => api<SampleCase[]>("/scenarios");
