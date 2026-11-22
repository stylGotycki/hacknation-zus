import type { EvaluationResult } from "@/lib/api";

/** Does the father get (or may get after a condition) any allowance? Then his totals are shown. */
export function fatherHasAllowance(result: EvaluationResult): boolean {
  return result.benefits.some(
    (b) =>
      b.person === "father" &&
      (b.status === "eligible" || b.status === "conditional"),
  );
}
