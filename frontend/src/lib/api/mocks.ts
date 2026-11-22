import { api } from "./client";
import { type FamilyProfile } from "./rules";

// --- Mocks of external systems (E7) ----------------------------------------------------------

export type Citizen = {
  id: string;
  first_name: string;
  last_name: string;
  pesel_masked: string;
  scenario_title_pl: string;
  scenario_description_pl: string;
  /** false: an account opened with the user's own PESEL – no data in the simulated ZUS. */
  demo: boolean;
};
export type LoginResult = {
  owner_id: string;
  citizen: Citizen;
  provider_pl: string;
};
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
export type PueAnswer = {
  ticket: string;
  received_at: string;
  answer_pl: string;
  note_pl: string;
};

export const listCitizens = () => api<Citizen[]>("/mock/citizens");
export const mobywatelLogin = (citizen_id: string) =>
  api<LoginResult>("/mock/mobywatel/login", {
    method: "POST",
    body: JSON.stringify({ citizen_id }),
  });
export const mobywatelLoginPesel = (
  pesel: string,
  first_name: string,
  last_name: string,
) =>
  api<LoginResult>("/mock/mobywatel/login-pesel", {
    method: "POST",
    body: JSON.stringify({ pesel, first_name, last_name }),
  });
export const zusInsurance = (id: string) =>
  api<InsuranceData>(`/mock/zus/${id}/insurance`);
export const zusDebt = (id: string) =>
  api<DebtCertificate>(`/mock/zus/${id}/debt-certificate`);
export const zusEzla = (id: string) =>
  api<{ records: EzlaRecord[]; note_pl: string }>(`/mock/zus/${id}/ezla`);
export const zusProfile = (id: string) =>
  api<FamilyProfile>(`/mock/zus/${id}/profile`);
export const pueQuestion = (
  citizen_id: string,
  subject: string,
  text: string,
) =>
  api<PueAnswer>("/mock/pue/question", {
    method: "POST",
    body: JSON.stringify({ citizen_id, subject, text }),
  });
