import { api } from "./client";
import { type EvaluationResult, type LegalParameter } from "./rules";
import { type ApplicationStatus } from "./applications";

// --- Admin panel (E8) -------------------------------------------------------------------------

export type AdminParameter = LegalParameter & {
  from_seed: boolean;
  current: boolean;
};
export type AdminApplication = {
  id: number;
  owner_id: string;
  form_code: string;
  title_pl: string;
  status: ApplicationStatus;
  submitted_to: string | null;
  created_at: string | null;
  last_note: string | null;
  params_count: number;
};

const adminHeaders = (token: string) => ({ "X-Admin-Token": token });
export const adminCheck = (token: string) =>
  api<{ ok: boolean }>("/admin/check", { headers: adminHeaders(token) });
export const adminParameters = (token: string) =>
  api<AdminParameter[]>("/admin/parameters", { headers: adminHeaders(token) });
export const adminAddVersion = (
  token: string,
  key: string,
  body: { value: unknown; valid_from?: string; legal_basis?: string },
) =>
  api<{ parameter: LegalParameter; applications_kept: number }>(
    `/admin/parameters/${key}/versions`,
    {
      method: "POST",
      headers: adminHeaders(token),
      body: JSON.stringify(body),
    },
  );
export const adminDeleteVersion = (
  token: string,
  key: string,
  validFrom: string,
) =>
  api<void>(`/admin/parameters/${key}/versions/${validFrom}`, {
    method: "DELETE",
    headers: adminHeaders(token),
  });
export const adminApplications = (token: string) =>
  api<AdminApplication[]>("/admin/applications", {
    headers: adminHeaders(token),
  });
export const adminSetStatus = (
  token: string,
  id: number,
  status: ApplicationStatus,
  note?: string,
) =>
  api<{ status: string }>(`/admin/applications/${id}/status`, {
    method: "POST",
    headers: adminHeaders(token),
    body: JSON.stringify({ status, note: note || null }),
  });

// --- Admin: rules of the guide (GET/PUT /api/admin/rules) ------------------------------------

export type RuleKind =
  | "wartosc"
  | "okres"
  | "swiadczenie"
  | "dokument"
  | "termin"
  | "ryzyko"
  | "informacja"
  | "zalozenie"
  | "walidacja";

export type RuleData = {
  code: string;
  kind: RuleKind;
  title_pl: string;
  group_pl: string;
  order: number;
  condition: string | null;
  expression: string | null;
  start: string | null;
  rate: string | null;
  work: string | null;
  person: string | null;
  period_kind: string | null;
  text_pl: string;
  severity: string | null;
  benefit: string | null;
  periods: string[];
  status: string | null;
  payer: string | null;
  apply_to_pl: string;
  deadline_kind: string | null;
  late_text_pl: string;
  legal_basis: string;
  source: string;
  description_pl: string;
  active: boolean;
  note?: string;
};

export type AdminRule = RuleData & {
  modified: boolean;
  in_seed: boolean;
  uses: string[];
  used_by: string[];
  facts: string[];
  parameters: string[];
  errors: string[];
};

export type RuleDictionary = {
  kinds: Record<RuleKind, string>;
  period_kinds: Record<string, string>;
  sources: Record<string, string>;
  persons: string[];
  facts: { path: string; type: string; description: string }[];
  functions: { name: string; description: string }[];
  parameters: { key: string; label: string; value: unknown }[];
  rules: { code: string; kind: string; title: string }[];
  version: string | null;
};

export type RuleTestResult = {
  ok: boolean;
  violation: string | null;
  result: EvaluationResult | null;
  values: Record<string, unknown>;
  errors: Record<string, string>;
};

/** Error of an admin call: Polish message plus the list of rule problems, if any. */
export class AdminError extends Error {
  constructor(
    message: string,
    public errors: string[] = [],
  ) {
    super(message);
  }
}

async function adminApi<T>(
  token: string,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`/api/admin${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...adminHeaders(token),
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = (await res.json()).detail;
    } catch {
      /* not JSON */
    }
    if (detail && typeof detail === "object" && "message" in detail) {
      const d = detail as { message: string; errors?: string[] };
      throw new AdminError(d.message, d.errors ?? []);
    }
    throw new AdminError(
      typeof detail === "string" ? detail : `Błąd ${res.status}`,
    );
  }
  return res.status === 204 ? (undefined as T) : (res.json() as Promise<T>);
}

export const adminRules = (token: string) =>
  adminApi<AdminRule[]>(token, "/rules");
export const adminRuleDictionary = (token: string) =>
  adminApi<RuleDictionary>(token, "/rules/dictionary");
export const adminValidateRule = (
  token: string,
  rule: RuleData,
  replace?: string,
) =>
  adminApi<{ ok: boolean; errors: string[] }>(
    token,
    `/rules/validate${replace ? `?replace=${encodeURIComponent(replace)}` : ""}`,
    { method: "POST", body: JSON.stringify(rule) },
  );
export const adminSaveRule = (token: string, rule: RuleData, isNew: boolean) =>
  adminApi<AdminRule>(token, isNew ? "/rules" : `/rules/${rule.code}`, {
    method: isNew ? "POST" : "PUT",
    body: JSON.stringify(rule),
  });
export const adminResetRule = (token: string, code: string) =>
  adminApi<AdminRule>(token, `/rules/${code}/reset`, { method: "POST" });
export const adminDeleteRule = (token: string, code: string) =>
  adminApi<void>(token, `/rules/${code}`, { method: "DELETE" });
export const adminRuleHistory = (token: string, code: string) =>
  adminApi<{ changed_at: string | null; note: string; data: RuleData }[]>(
    token,
    `/rules/${code}/history`,
  );
export const adminTestRules = (
  token: string,
  profile: unknown,
  draft?: RuleData,
) =>
  adminApi<RuleTestResult>(token, "/rules/test", {
    method: "POST",
    body: JSON.stringify({ profile, draft }),
  });
