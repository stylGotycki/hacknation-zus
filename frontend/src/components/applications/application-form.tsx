"use client";

import {
  ArrowLeft,
  ArrowRight,
  Check,
  ClipboardCheck,
  Loader2,
  Pencil,
  Save,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox, Field, Input, Select } from "@/components/ui/form-controls";
import {
  draftKey,
  saveDraft,
  submitApplication,
  type ApplicationRecord,
  type FormData,
  type FormDefinition,
  type FormField,
  type People,
} from "@/lib/api";
import { formatDate, toIsoDate } from "@/lib/format";
import {
  TRUTH_FIELD,
  formatValue,
  isEmpty,
  renderText,
  shownParagraphs,
  visibleSteps,
} from "@/lib/form-logic";
import { cn } from "@/lib/utils";

/** Fields of the other parent in a form -> the same fact in the parent's record. */
const OTHER_PARENT_KEYS: Record<string, string> = {
  other_first_name: "first_name",
  other_last_name: "last_name",
  other_pesel: "pesel",
  other_address: "address",
};

const SEND_LABEL = {
  zus: "Wyślij do ZUS",
  employer: "Wyślij do pracodawcy",
  registry: "Wyślij do urzędu",
} as const;

function FieldInput({
  field,
  value,
  onChange,
}: {
  field: FormField;
  value: FormData[string] | undefined;
  onChange: (value: FormData[string]) => void;
}) {
  const label = field.label_pl + (field.required ? " *" : "");
  if (field.type === "checkbox") {
    return (
      <Checkbox
        label={label}
        hint={field.hint_pl ?? undefined}
        checked={Boolean(value)}
        onChange={(e) => onChange(e.target.checked)}
      />
    );
  }
  return (
    <Field label={label} hint={field.hint_pl ?? undefined}>
      {field.type === "textarea" ? (
        <textarea
          className="min-h-20 w-full rounded-sm border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
          value={String(value ?? "")}
          onChange={(e) => onChange(e.target.value)}
        />
      ) : field.type === "select" ? (
        <Select
          value={String(value ?? "")}
          onChange={(e) => onChange(e.target.value)}
        >
          <option value="">Wybierz…</option>
          {field.options?.map(([v, text]) => (
            <option key={v} value={v}>
              {text}
            </option>
          ))}
        </Select>
      ) : (
        <Input
          type={field.type === "date" ? "date" : "text"}
          inputMode={field.type === "number" ? "numeric" : undefined}
          value={String(value ?? "")}
          onChange={(e) =>
            onChange(
              field.type === "number" &&
                e.target.value !== "" &&
                !Number.isNaN(Number(e.target.value))
                ? Number(e.target.value)
                : e.target.value,
            )
          }
        />
      )}
    </Field>
  );
}

/** The request as it reads on paper: header, text, statements, attachments, signature. */
function LetterPreview({
  definition,
  data,
}: {
  definition: FormDefinition;
  data: FormData;
}) {
  const text = (t: string) => renderText(t, definition, data);
  const body = shownParagraphs(definition.body, data);
  const attachments = shownParagraphs(definition.attachments, data);
  const statements = definition.statements.filter((s) => data[s.key]);
  const zus = definition.submitted_to === "zus";
  return (
    <article
      aria-label="Podgląd wniosku"
      className="flex flex-col gap-4 border border-band-border bg-white p-5 font-serif text-[15px] leading-relaxed text-foreground shadow-sm sm:p-8"
    >
      <div className="flex flex-wrap justify-between gap-4 text-sm">
        <div>
          <p className="font-bold">
            {String(data.first_name ?? "………")} {String(data.last_name ?? "")}
          </p>
          {zus && data.pesel && <p>PESEL: {String(data.pesel)}</p>}
          {zus && data.address && <p>{String(data.address)}</p>}
        </div>
        <p>
          {String(data.place ?? "………")}, {formatDate(toIsoDate(new Date()))}
        </p>
      </div>
      <div className="ml-auto max-w-xs text-sm">
        <p className="font-bold">{definition.addressee_pl}</p>
        {data.employer_name && <p>{String(data.employer_name)}</p>}
        {data.employer_address && <p>{String(data.employer_address)}</p>}
        {zus && data.payer_name && (
          <p>
            Płatnik składek: {String(data.payer_name)}
            {data.payer_nip ? `, NIP ${String(data.payer_nip)}` : ""}
            {data.payer_regon ? `, REGON ${String(data.payer_regon)}` : ""}
            {data.payer_address ? `, ${String(data.payer_address)}` : ""}
          </p>
        )}
      </div>
      <h3 className="text-center font-sans text-lg font-bold">
        {definition.title_pl}
      </h3>
      {body.map((p) => (
        <p key={p.text_pl} className="indent-8">
          {text(p.text_pl)}
        </p>
      ))}
      {statements.map((s) => (
        <p key={s.key} className="indent-8">
          {s.label_pl}.
        </p>
      ))}
      {attachments.length > 0 && (
        <div>
          <p className="font-bold">Załączniki:</p>
          <ol className="ml-6 list-decimal">
            {attachments.map((a) => (
              <li key={a.text_pl}>{text(a.text_pl)}</li>
            ))}
          </ol>
        </div>
      )}
      <div className="mt-4 flex justify-end">
        <p className="border-t border-dotted border-foreground px-6 pt-1 text-center text-xs">
          {zus ? "podpis ubezpieczonego" : "podpis pracownika"}
          <br />
          (podpis elektroniczny przy wysyłce)
        </p>
      </div>
      <p className="font-sans text-xs text-muted-foreground">
        Podstawa prawna: {definition.legal_basis_pl}
      </p>
    </article>
  );
}

export function ApplicationForm({
  definition,
  initialData,
  initialStep,
  people,
  onClose,
  onSubmitted,
}: {
  definition: FormDefinition;
  initialData: FormData;
  initialStep: number;
  people: People;
  onClose: () => void;
  onSubmitted: (application: ApplicationRecord) => void;
}) {
  const [data, setData] = useState<FormData>(initialData);
  const steps = useMemo(
    () => visibleSteps(definition, data),
    [definition, data],
  );
  const summaryIndex = steps.length; // the last page: summary, statements and confirmation
  const [step, setStep] = useState(Math.min(initialStep, summaryIndex));
  const [saved, setSaved] = useState<"idle" | "saving" | "saved">("idle");
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [tried, setTried] = useState(false);
  const dirty = useRef(false);
  const key = draftKey(definition, data);

  // Fill what is already known about the applicant (and the other parent) into empty fields: the
  // data of the husband or wife typed in an earlier form, or the mObywatel identity.
  const role =
    definition.roles.length === 1
      ? definition.roles[0]
      : (data.applicant_role as string | undefined);
  useEffect(() => {
    if (role !== "mother" && role !== "father") return;
    const other = role === "mother" ? "father" : "mother";
    const fields = new Set(
      definition.steps.flatMap((st) => st.fields.map((f) => f.key)),
    );
    const known: FormData = {};
    for (const [k, v] of Object.entries(people[role]))
      if (fields.has(k)) known[k] = v;
    for (const [formKey, k] of Object.entries(OTHER_PARENT_KEYS)) {
      if (fields.has(formKey) && people[other][k])
        known[formKey] = people[other][k];
    }
    setData((d) => {
      const fill = Object.entries(known).filter(([k]) => isEmpty(d[k]));
      return fill.length ? { ...d, ...Object.fromEntries(fill) } : d;
    });
  }, [role, people, definition]);

  // Autosave the draft (with the step) shortly after the user stops typing.
  useEffect(() => {
    if (!dirty.current) return;
    setSaved("saving");
    const timer = setTimeout(() => {
      saveDraft(key, step, data)
        .then(() => setSaved("saved"))
        .catch(() => setSaved("idle"));
    }, 700);
    return () => clearTimeout(timer);
  }, [data, step, key]);

  const atSummary = step >= summaryIndex;
  const current = steps[Math.min(step, steps.length - 1)];
  const confirmFields = [...definition.statements, TRUTH_FIELD];
  const missing = (atSummary ? confirmFields : current.fields).filter(
    (f) => f.required && isEmpty(data[f.key]),
  );
  const missingAnywhere = steps.flatMap((s) =>
    s.fields.filter((f) => f.required && isEmpty(data[f.key])),
  );

  const set = (k: string, value: FormData[string]) => {
    dirty.current = true;
    setData((d) => ({ ...d, [k]: value }));
  };

  function go(to: number) {
    dirty.current = true;
    setError(null);
    setTried(false);
    setStep(to);
    requestAnimationFrame(() =>
      window.scrollTo({ top: 0, behavior: "smooth" }),
    );
  }

  function next() {
    setTried(true);
    if (missing.length) return;
    go(step + 1);
  }

  async function submit() {
    setTried(true);
    if (missing.length || missingAnywhere.length) return;
    setSending(true);
    setError(null);
    try {
      onSubmitted(await submitApplication(definition.code, data, key));
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message.replace(/^API \d+: /, "")
          : "Nie udało się złożyć wniosku.",
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-2">
        <h2 className="text-xl font-bold">{definition.title_pl}</h2>
        <p className="text-sm text-muted-foreground">
          {definition.description_pl}
        </p>
        {definition.deadline_pl && (
          <p className="text-sm">
            <span className="font-bold">Termin: </span>
            {definition.deadline_pl}
          </p>
        )}
        <ol className="mt-2 flex flex-wrap gap-1.5 text-xs" aria-label="Postęp">
          {[...steps.map((s) => s.title_pl), "Podsumowanie"].map((title, i) => (
            <li key={title}>
              <button
                type="button"
                onClick={() => i < step && go(i)}
                disabled={i >= step}
                aria-current={i === step ? "step" : undefined}
                className={cn(
                  "rounded-sm border px-2.5 py-1 font-bold",
                  i === step
                    ? "border-primary bg-primary text-white"
                    : i < step
                      ? "border-primary text-primary hover:bg-secondary"
                      : "border-band-border text-muted-foreground",
                )}
              >
                {i + 1}. {title}
              </button>
            </li>
          ))}
        </ol>
      </header>

      {!atSummary && (
        <section aria-label={current.title_pl} className="flex flex-col gap-4">
          <h3 className="font-bold">{current.title_pl}</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            {current.fields.map((field) => (
              <div
                key={field.key}
                className={cn(
                  field.type === "textarea" || field.type === "checkbox"
                    ? "sm:col-span-2"
                    : "",
                )}
              >
                <FieldInput
                  field={field}
                  value={data[field.key]}
                  onChange={(v) => set(field.key, v)}
                />
              </div>
            ))}
          </div>
        </section>
      )}

      {atSummary && (
        <section aria-label="Podsumowanie" className="flex flex-col gap-5">
          <div className="flex items-start gap-3 border-l-[5px] border-primary bg-muted p-4 text-sm">
            <ClipboardCheck className="mt-0.5 size-5 shrink-0 text-primary" />
            <p>
              Sprawdź wniosek przed wysłaniem. Tak będzie wyglądał dokument,
              który otrzyma{" "}
              {definition.submitted_to === "zus"
                ? "ZUS"
                : definition.submitted_to === "employer"
                  ? "pracodawca"
                  : "urząd"}
              . Jeśli coś się nie zgadza, kliknij „Popraw” przy danej części.
            </p>
          </div>

          <LetterPreview definition={definition} data={data} />

          <div className="flex flex-col gap-3">
            <h3 className="font-bold">Wprowadzone dane</h3>
            {steps.map((s, i) => (
              <section key={s.title_pl} className="border border-band-border">
                <div className="flex items-center justify-between gap-2 bg-muted px-3 py-2">
                  <h4 className="text-sm font-bold">{s.title_pl}</h4>
                  <button
                    type="button"
                    onClick={() => go(i)}
                    className="inline-flex items-center gap-1 text-sm font-bold text-link hover:underline"
                  >
                    <Pencil className="size-3.5" /> Popraw
                  </button>
                </div>
                <dl className="grid gap-x-4 gap-y-1 p-3 text-sm sm:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
                  {s.fields.map((f) => (
                    <div key={f.key} className="contents">
                      <dt className="text-muted-foreground">{f.label_pl}</dt>
                      <dd
                        className={cn(
                          "font-medium",
                          isEmpty(data[f.key]) &&
                            f.type !== "checkbox" &&
                            "text-muted-foreground",
                        )}
                      >
                        {formatValue(f, data[f.key]) ||
                          (f.required ? (
                            <span className="text-destructive">
                              brak – uzupełnij
                            </span>
                          ) : (
                            "–"
                          ))}
                      </dd>
                    </div>
                  ))}
                </dl>
              </section>
            ))}
          </div>

          {definition.instructions_pl.length > 0 && (
            <div className="text-sm">
              <h3 className="font-bold">Pouczenie</h3>
              <ul className="ml-5 list-disc text-muted-foreground">
                {definition.instructions_pl.map((i) => (
                  <li key={i}>{i}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex flex-col gap-3 border-t border-band-border pt-4">
            <h3 className="font-bold">Oświadczenia</h3>
            {confirmFields.map((f) => (
              <FieldInput
                key={f.key}
                field={f}
                value={data[f.key]}
                onChange={(v) => set(f.key, v)}
              />
            ))}
          </div>
        </section>
      )}

      {error && (
        <div
          role="alert"
          className="border border-destructive/40 bg-destructive/5 p-3 text-sm"
        >
          {error}
        </div>
      )}
      {tried &&
        (missing.length > 0 || (atSummary && missingAnywhere.length > 0)) && (
          <p
            role="alert"
            className="bg-destructive/5 p-3 text-sm text-destructive"
          >
            {atSummary && missingAnywhere.length > 0
              ? `Uzupełnij brakujące dane: ${missingAnywhere.map((f) => f.label_pl).join(", ")}.`
              : atSummary
                ? "Zaznacz oświadczenia, aby wysłać wniosek."
                : "Uzupełnij pola oznaczone gwiazdką, aby przejść dalej."}
          </p>
        )}

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-band-border pt-4">
        <Button
          variant="outline"
          onClick={step === 0 ? onClose : () => go(step - 1)}
        >
          <ArrowLeft /> {step === 0 ? "Zamknij" : "Wstecz"}
        </Button>
        <span className="text-xs text-muted-foreground" aria-live="polite">
          {saved === "saving" && "Zapisuję wersję roboczą…"}
          {saved === "saved" && (
            <span className="inline-flex items-center gap-1">
              <Save className="size-3.5" /> Wersja robocza zapisana na Twoim
              koncie
            </span>
          )}
        </span>
        {atSummary ? (
          <Button onClick={submit} disabled={sending}>
            {sending ? <Loader2 className="animate-spin" /> : <Check />}
            {SEND_LABEL[definition.submitted_to]}
          </Button>
        ) : (
          <Button onClick={next}>
            {step === summaryIndex - 1 ? "Przejdź do podsumowania" : "Dalej"}{" "}
            <ArrowRight />
          </Button>
        )}
      </div>
    </div>
  );
}
