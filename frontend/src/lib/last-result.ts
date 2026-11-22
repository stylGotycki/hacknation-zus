import type { EvaluationResult } from "@/lib/api";

const KEY = "parent-guide:last-result";

/** The last calculator result lives in the browser tab so other pages (timeline) can show it. */
export function saveLastResult(result: EvaluationResult): void {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(result));
  } catch {
    // Storage can be blocked; the timeline page then simply asks for a calculation.
  }
}

export function loadLastResult(): EvaluationResult | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as EvaluationResult) : null;
  } catch {
    return null;
  }
}

const FORM_KEY = "parent-guide:last-form";

/** The calculator form state, so the wizard can hand its answers over to the calculator. */
export function saveLastForm(form: unknown): void {
  try {
    sessionStorage.setItem(FORM_KEY, JSON.stringify(form));
  } catch {
    // Storage can be blocked; the calculator then starts with its defaults.
  }
}

export function loadLastForm<T>(): T | null {
  try {
    const raw = sessionStorage.getItem(FORM_KEY);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

const PROFILE_KEY = "parent-guide:last-profile";

/** The profile behind the last result, so the applications page can suggest and prefill forms. */
export function saveLastProfile(profile: unknown): void {
  try {
    sessionStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  } catch {
    // Without storage the applications page lets the user pick a form by hand.
  }
}

export function loadLastProfile<T>(): T | null {
  try {
    const raw = sessionStorage.getItem(PROFILE_KEY);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

const STEP_KEY = "parent-guide:last-step";

/** The calculator step the user stopped at. */
export function saveLastStep(step: number): void {
  try {
    sessionStorage.setItem(STEP_KEY, String(step));
  } catch {
    // Without storage the calculator starts from the first step.
  }
}

export function loadLastStep(): number {
  try {
    return Number(sessionStorage.getItem(STEP_KEY) ?? 0) || 0;
  } catch {
    return 0;
  }
}
