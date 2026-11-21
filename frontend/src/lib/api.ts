/**
 * Thin fetch wrapper for the FastAPI backend.
 * - In the browser: relative `/api/...` (nginx, or the Next.js rewrite, forwards it).
 * - On the server (Server Components): straight to the backend inside the Docker network.
 */
const BASE =
  typeof window === "undefined" ? (process.env.INTERNAL_API_URL ?? "http://localhost:8000") : "";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

// --- Types mirroring backend schemas (keep in sync with /api/docs) -----------------------

export type LegalParameter = {
  key: string;
  value: unknown;
  valid_from: string;
  valid_to: string | null;
  description_pl: string;
  legal_basis: string;
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
  job_loss_reason?: "employer_bankruptcy" | "unlawful_dismissal" | "other" | null;
  average_monthly_base?: number | null;
  working_time_fraction?: number;
  fixed_term_contract?: boolean;
  employer_insured_count?: number | null;
  start_relief?: boolean;
  contribution_debt?: number;
  debt_paid_on?: string | null;
  debt_in_installments?: boolean;
  base_raised_in_pregnancy?: boolean;
  planned_work_fraction?: number;
  on_pregnancy_sick_leave?: boolean;
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
  parental_parts_mother?: number;
  parental_parts_father?: number;
  paternity_parts?: number;
  use_supplementary_leave?: boolean;
  supplementary_taken_by?: "mother" | "father";
};

export type FamilyProfile = {
  child: ChildProfile;
  mother?: ParentProfile | null;
  father?: ParentProfile | null;
  mother_cannot_care?: "hospital" | "disabled" | "death" | "abandoned" | null;
  averaged_rate_applied_on?: string | null;
  plan?: Plan;
};

export type BenefitStatus = "eligible" | "conditional" | "not_eligible" | "info";

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
  monthly_net_estimate: number | null;
  total_gross: number | null;
  total_net_estimate: number | null;
  raised_to_minimum: boolean;
  start: string | null;
  end: string | null;
  payer: "employer" | "zus" | "municipality" | null;
  apply_to_pl: string | null;
  documents_pl: string[];
  deadline: string | null;
  days_left: number | null;
  deadline_note_pl: string | null;
};

export type LeavePeriod = {
  id: string;
  person: Person;
  kind: "pregnancy_sickness" | "maternity" | "supplementary" | "parental" | "paternity";
  label_pl: string;
  start: string;
  end: string;
  days: number;
  weeks: number;
  paid: boolean;
  rate: number | null;
  monthly_gross: number | null;
  total_gross: number | null;
  total_net_estimate: number | null;
  work_fraction: number;
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
};

export type AveragedRateComparison = {
  standard_total: number | null;
  averaged_total: number | null;
  better: "standard" | "averaged" | "equal" | null;
  deadline: string;
  still_possible: boolean;
  note_pl: string;
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
};

export function evaluateFamily(profile: FamilyProfile, date?: string) {
  const query = date ? `?date=${encodeURIComponent(date)}` : "";
  return api<EvaluationResult>(`/rules/evaluate${query}`, {
    method: "POST",
    body: JSON.stringify(profile),
  });
}
