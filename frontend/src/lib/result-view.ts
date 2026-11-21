import type { EvaluationResult } from "@/lib/api";

/** Benefits that are real allowances (not general information like the care allowance). */
const isAllowanceFor = (code: string, person: string) =>
  code.endsWith(`_allowance_${person}`) && !code.startsWith("care_");

/**
 * The father is shown only if he actually gets an allowance (or may get one after a condition
 * is met). When he is not in the family's benefits, everything about him is left out.
 */
export function fatherHasAllowance(result: EvaluationResult): boolean {
  return result.benefits.some(
    (b) => isAllowanceFor(b.code, "father") && (b.status === "eligible" || b.status === "conditional"),
  );
}

/** Same result without anything that concerns a father who has no allowance. */
export function withoutIdleFather(result: EvaluationResult): EvaluationResult {
  if (fatherHasAllowance(result)) return result;
  return {
    ...result,
    benefits: result.benefits.filter((b) => b.person !== "father"),
    timeline: result.timeline.filter((p) => p.person !== "father"),
    risks: result.risks.filter((r) => r.person !== "father"),
    deadlines: result.deadlines.filter((d) => d.person !== "father"),
    totals: { ...result.totals, father_gross: 0 },
  };
}
