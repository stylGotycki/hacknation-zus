import type { FormData, FormDefinition, FormField, Paragraph } from "@/lib/api";
import { formatDate } from "@/lib/format";

/** Confirmation under the summary, required before sending (same key the backend checks). */
export const TRUTH_FIELD: FormField = {
  key: "declaration",
  label_pl: "Oświadczam, że dane zawarte we wniosku są zgodne z prawdą",
  type: "checkbox",
  required: true,
  hint_pl: null,
  options: null,
  when: null,
};

/** Same rule as the backend: "key" (truthy), "key=value" or "key!=value". */
export function holds(condition: string | null | undefined, data: FormData): boolean {
  if (!condition) return true;
  if (condition.includes("!=")) {
    const [key, value] = condition.split("!=");
    return String(data[key] ?? "") !== value;
  }
  if (condition.includes("=")) {
    const [key, value] = condition.split("=");
    return String(data[key] ?? "") === value;
  }
  const v = data[condition];
  return v !== undefined && v !== null && v !== "" && v !== false && v !== 0;
}

export const isEmpty = (value: unknown) => value === undefined || value === null || value === "" || value === false;

export function visibleSteps(definition: FormDefinition, data: FormData) {
  return definition.steps
    .map((step, index) => ({ ...step, index, fields: step.fields.filter((f) => holds(f.when, data)) }))
    .filter((step) => holds(step.when, data));
}

export function fieldIndex(definition: FormDefinition): Map<string, FormField> {
  const map = new Map<string, FormField>();
  for (const step of definition.steps) for (const f of step.fields) map.set(f.key, f);
  for (const f of definition.statements) map.set(f.key, f);
  return map;
}

/** A value as it would read on the printed form. */
export function formatValue(field: FormField | undefined, value: FormData[string] | undefined): string {
  if (isEmpty(value) && field?.type !== "checkbox") return "";
  if (!field) return String(value ?? "");
  if (field.type === "checkbox") return value ? "tak" : "nie";
  if (field.type === "date") return formatDate(String(value));
  if (field.type === "select") return field.options?.find(([v]) => v === value)?.[1] ?? String(value);
  return String(value);
}

const BLANK = "………";

/** Fills {key} placeholders; a hidden field gives nothing, a visible empty one a blank line like on paper. */
export function renderText(text: string, definition: FormDefinition, data: FormData): string {
  const fields = fieldIndex(definition);
  return text
    .replace(/\{([a-z_]+)\}/g, (_, key: string) => {
      const field = fields.get(key);
      if (field && !holds(field.when, data)) return "";
      const value = formatValue(field, data[key]);
      return value || BLANK;
    })
    .replace(/\s+([.,;])/g, "$1")
    .replace(/\s{2,}/g, " ")
    .trim();
}

export const shownParagraphs = (items: Paragraph[], data: FormData) => items.filter((p) => holds(p.when, data));
