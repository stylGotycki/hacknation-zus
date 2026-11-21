/**
 * Thin fetch wrapper for the FastAPI backend.
 * - In the browser: relative `/api/...` (nginx, or the Next.js rewrite, forwards it).
 * - On the server (Server Components): straight to the backend inside the Docker network.
 */
const BASE =
  typeof window === "undefined" ? (process.env.INTERNAL_API_URL ?? "http://localhost:8000") : "";

/** Stable anonymous id of this browser; the mObywatel mock (E7) will replace it with a real identity. */
function ownerHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  try {
    let id = localStorage.getItem("parent-guide:owner");
    if (!id) {
      id = `guest-${crypto.randomUUID()}`;
      localStorage.setItem("parent-guide:owner", id);
    }
    return { "X-Owner-Id": id };
  } catch {
    return { "X-Owner-Id": "guest" };
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...ownerHeader(), ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }
  return res.status === 204 ? (undefined as T) : (res.json() as Promise<T>);
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
  sick_leave_start?: string | null;
  sick_leave_end?: string | null;
  sick_days_used_this_year?: number;
  age_over_50?: boolean;
  monthly_bases?: number[] | null;
  on_childcare_leave?: boolean;
};

export type CareProfile = {
  situation?: "sick_child" | "healthy_child" | "family_member";
  child_age_years?: number;
  child_disabled?: boolean;
  other_household_member_available?: boolean;
  days_planned?: number;
  days_used_this_year?: number;
  days_used_for_family_members?: number;
};

export type ParentalBlock = { person: "mother" | "father"; weeks: number; start?: string | null };

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
  parental_blocks?: ParentalBlock[] | null;
  paternity_starts?: string[] | null;
};

export type FamilyProfile = {
  child: ChildProfile;
  mother?: ParentProfile | null;
  father?: ParentProfile | null;
  mother_cannot_care?: "hospital" | "disabled" | "death" | "abandoned" | null;
  averaged_rate_applied_on?: string | null;
  plan?: Plan;
  care?: CareProfile | null;
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
  employer_days?: number | null;
  zus_days?: number | null;
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

export type Scenario = {
  id: string;
  title_pl: string;
  description_pl: string;
  tags: string[];
  profile: FamilyProfile;
};

export function listScenarios() {
  return api<Scenario[]>("/scenarios");
}

// --- Applications (E6) ----------------------------------------------------------------------

export type FormField = {
  key: string;
  label_pl: string;
  type: "text" | "date" | "number" | "select" | "checkbox" | "textarea";
  required: boolean;
  hint_pl: string | null;
  options: [string, string][] | null;
};
export type FormStepDef = { title_pl: string; fields: FormField[] };
export type FormDefinition = {
  code: string;
  title_pl: string;
  description_pl: string;
  submitted_to: "employer" | "zus" | "registry";
  steps: FormStepDef[];
};
export type FormData = Record<string, string | number | boolean | null>;
export type Suggestion = {
  form_code: string;
  person: "mother" | "father";
  title_pl: string;
  submitted_to: "employer" | "zus";
  deadline: string | null;
  days_left: number | null;
  prefill: FormData;
};
export type Draft = { id: number; form_code: string; step: number; data: FormData; updated_at: string | null };
export type ApplicationStatus = "submitted" | "in_progress" | "decided";
export type ApplicationRecord = {
  id: number;
  form_code: string;
  title_pl: string;
  status: ApplicationStatus;
  submitted_to: "employer" | "zus" | "registry" | null;
  data: FormData;
  history: { at: string; status: string; note: string }[];
  created_at: string | null;
};

export const listForms = () => api<FormDefinition[]>("/forms");
export const getSuggestions = (profile: FamilyProfile) =>
  api<Suggestion[]>("/applications/suggestions", { method: "POST", body: JSON.stringify(profile) });
export const listDrafts = () => api<Draft[]>("/drafts");
export const saveDraft = (code: string, step: number, data: FormData) =>
  api<Draft>(`/drafts/${code}`, { method: "PUT", body: JSON.stringify({ step, data }) });
export const deleteDraft = (code: string) => api<void>(`/drafts/${code}`, { method: "DELETE" });
export const listApplications = () => api<ApplicationRecord[]>("/applications");
export const submitApplication = (form_code: string, data: FormData) =>
  api<ApplicationRecord>("/applications", { method: "POST", body: JSON.stringify({ form_code, data }) });
export const advanceApplication = (id: number) =>
  api<ApplicationRecord>(`/applications/${id}/advance`, { method: "POST" });

// --- Mocks of external systems (E7) ----------------------------------------------------------

export type Citizen = {
  id: string;
  first_name: string;
  last_name: string;
  pesel_masked: string;
  scenario_title_pl: string;
  scenario_description_pl: string;
};
export type LoginResult = { owner_id: string; citizen: Citizen; provider_pl: string };
export type InsuranceData = {
  role: "mother" | "father";
  event_date: string;
  insured_on_event: boolean;
  summary_pl: string;
  periods: {
    title_code: string;
    title_pl: string;
    sickness_insurance: string;
    from: string;
    to: string | null;
    payer_pl: string;
  }[];
  bases: { month: string; base: number }[];
  note_pl: string;
};
export type DebtCertificate = {
  as_of: string;
  number: string;
  debt_amount: number;
  threshold: number;
  in_installments: boolean;
  blocks_benefit: boolean;
  summary_pl: string;
  note_pl: string;
};
export type EzlaRecord = {
  number: string;
  code: string;
  code_description_pl: string;
  from: string;
  to: string;
  days: number;
  issued_by_pl: string;
  payer_pl: string;
};
export type PueAnswer = { ticket: string; received_at: string; answer_pl: string; note_pl: string };

export const listCitizens = () => api<Citizen[]>("/mock/citizens");
export const mobywatelLogin = (citizen_id: string) =>
  api<LoginResult>("/mock/mobywatel/login", { method: "POST", body: JSON.stringify({ citizen_id }) });
export const zusInsurance = (id: string) => api<InsuranceData>(`/mock/zus/${id}/insurance`);
export const zusDebt = (id: string) => api<DebtCertificate>(`/mock/zus/${id}/debt-certificate`);
export const zusEzla = (id: string) => api<{ records: EzlaRecord[]; note_pl: string }>(`/mock/zus/${id}/ezla`);
export const zusProfile = (id: string) => api<FamilyProfile>(`/mock/zus/${id}/profile`);
export const pueQuestion = (citizen_id: string, subject: string, text: string) =>
  api<PueAnswer>("/mock/pue/question", { method: "POST", body: JSON.stringify({ citizen_id, subject, text }) });

// --- Admin panel (E8) -------------------------------------------------------------------------

export type AdminParameter = LegalParameter & { from_seed: boolean; current: boolean };
export type AdminApplication = {
  id: number;
  owner_id: string;
  form_code: string;
  title_pl: string;
  status: ApplicationStatus;
  submitted_to: string | null;
  created_at: string | null;
  last_note: string | null;
};

const adminHeaders = (token: string) => ({ "X-Admin-Token": token });
export const adminCheck = (token: string) => api<{ ok: boolean }>("/admin/check", { headers: adminHeaders(token) });
export const adminParameters = (token: string) =>
  api<AdminParameter[]>("/admin/parameters", { headers: adminHeaders(token) });
export const adminAddVersion = (
  token: string,
  key: string,
  body: { value: unknown; valid_from: string; description_pl?: string; legal_basis?: string },
) =>
  api<LegalParameter>(`/admin/parameters/${key}/versions`, {
    method: "POST",
    headers: adminHeaders(token),
    body: JSON.stringify(body),
  });
export const adminDeleteVersion = (token: string, key: string, validFrom: string) =>
  api<void>(`/admin/parameters/${key}/versions/${validFrom}`, { method: "DELETE", headers: adminHeaders(token) });
export const adminApplications = (token: string) =>
  api<AdminApplication[]>("/admin/applications", { headers: adminHeaders(token) });
export const adminSetStatus = (token: string, id: number, status: ApplicationStatus, note?: string) =>
  api<{ status: string }>(`/admin/applications/${id}/status`, {
    method: "POST",
    headers: adminHeaders(token),
    body: JSON.stringify({ status, note: note || null }),
  });
