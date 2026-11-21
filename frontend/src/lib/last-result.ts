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
