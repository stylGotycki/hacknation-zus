import { api } from "./client";
import { type FamilyProfile } from "./rules";

// --- Applications (E6) ----------------------------------------------------------------------

export type FormField = {
  key: string;
  label_pl: string;
  type: "text" | "date" | "number" | "select" | "checkbox" | "textarea";
  required: boolean;
  hint_pl: string | null;
  options: [string, string][] | null;
  /** "key", "key=value" or "key!=value": the field is shown (and required) only when it holds. */
  when: string | null;
};
export type FormStepDef = {
  title_pl: string;
  fields: FormField[];
  when: string | null;
};
export type Paragraph = { text_pl: string; when: string | null };
export type Role = "mother" | "father";
export type FormDefinition = {
  code: string;
  title_pl: string;
  description_pl: string;
  submitted_to: "employer" | "zus" | "registry";
  addressee_pl: string;
  legal_basis_pl: string;
  deadline_pl: string;
  roles: Role[];
  fulfils: string[];
  steps: FormStepDef[];
  body: Paragraph[];
  attachments: Paragraph[];
  statements: FormField[];
  instructions_pl: string[];
  sources_pl: string;
};
export type FormData = Record<string, string | number | boolean | null>;
export type Suggestion = {
  form_code: string;
  person: Role;
  title_pl: string;
  submitted_to: "employer" | "zus" | "registry";
  deadline: string | null;
  days_left: number | null;
  status: "open" | "soon" | "overdue" | null;
  late_pl: string | null;
  deadline_codes: string[];
  prefill: FormData;
};
/** `form_code` of a draft is the draft key: the form code, or `code:role` when both parents may file it. */
export type Draft = {
  id: number;
  form_code: string;
  step: number;
  data: FormData;
  updated_at: string | null;
};
export type ApplicationStatus = "submitted" | "in_progress" | "decided";
export type ApplicationRecord = {
  id: number;
  form_code: string;
  title_pl: string;
  person: Role | null;
  fulfils: string[];
  status: ApplicationStatus;
  submitted_to: "employer" | "zus" | "registry" | null;
  data: FormData;
  history: { at: string; status: string; note: string }[];
  created_at: string | null;
};

export const draftKey = (definition: FormDefinition, data: FormData) => {
  const role =
    definition.roles.length === 1
      ? null
      : (data.applicant_role as string | undefined);
  return role ? `${definition.code}:${role}` : definition.code;
};

export const listForms = () => api<FormDefinition[]>("/forms");
export const getSuggestions = (profile: FamilyProfile) =>
  api<Suggestion[]>("/applications/suggestions", {
    method: "POST",
    body: JSON.stringify(profile),
  });
/** Data of both parents known so far (mObywatel identity + earlier forms), to prefill new forms. */
export type People = Record<Role, Record<string, string>>;
export const getPeople = () => api<People>("/people");
export const listDrafts = () => api<Draft[]>("/drafts");
export const saveDraft = (code: string, step: number, data: FormData) =>
  api<Draft>(`/drafts/${code}`, {
    method: "PUT",
    body: JSON.stringify({ step, data }),
  });
export const deleteDraft = (code: string) =>
  api<void>(`/drafts/${code}`, { method: "DELETE" });
export const listApplications = () => api<ApplicationRecord[]>("/applications");
export const submitApplication = (
  form_code: string,
  data: FormData,
  draft_key?: string,
) =>
  api<ApplicationRecord>("/applications", {
    method: "POST",
    body: JSON.stringify({ form_code, data, draft_key }),
  });

/** What the user entered in the calculator, kept on their account (guest or mObywatel). */
export type GuideState = {
  form: unknown;
  step: number;
  profile: FamilyProfile | null;
  updated_at: string | null;
};
export const getGuideState = () => api<GuideState>("/state");
export const saveGuideState = (state: {
  form: unknown;
  step: number;
  profile: FamilyProfile | null;
}) => api<GuideState>("/state", { method: "PUT", body: JSON.stringify(state) });
export const advanceApplication = (id: number) =>
  api<ApplicationRecord>(`/applications/${id}/advance`, { method: "POST" });
