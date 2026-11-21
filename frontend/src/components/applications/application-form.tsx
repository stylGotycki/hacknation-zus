"use client";

import { ArrowLeft, ArrowRight, Check, Loader2, Save } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox, Field, Input, Select } from "@/components/ui/form-controls";
import {
  saveDraft,
  submitApplication,
  type ApplicationRecord,
  type FormData,
  type FormDefinition,
  type FormField,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const isEmpty = (value: unknown) => value === undefined || value === null || value === "" || value === false;

function FieldInput({
  field,
  value,
  onChange,
}: {
  field: FormField;
  value: FormData[string] | undefined;
  onChange: (value: FormData[string]) => void;
}) {
  const label = field.label_pl + (field.required && field.type !== "checkbox" ? " *" : "");
  if (field.type === "checkbox") {
    return (
      <Checkbox
        label={label + (field.required ? " *" : "")}
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
          className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm shadow-xs outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
          value={String(value ?? "")}
          onChange={(e) => onChange(e.target.value)}
        />
      ) : field.type === "select" ? (
        <Select value={String(value ?? "")} onChange={(e) => onChange(e.target.value)}>
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
          inputMode={field.type === "number" ? "decimal" : undefined}
          value={String(value ?? "")}
          onChange={(e) =>
            onChange(
              field.type === "number" && e.target.value !== "" && !Number.isNaN(Number(e.target.value))
                ? Number(e.target.value)
                : e.target.value,
            )
          }
        />
      )}
    </Field>
  );
}

export function ApplicationForm({
  definition,
  initialData,
  initialStep,
  onClose,
  onSubmitted,
}: {
  definition: FormDefinition;
  initialData: FormData;
  initialStep: number;
  onClose: () => void;
  onSubmitted: (application: ApplicationRecord) => void;
}) {
  const [data, setData] = useState<FormData>(initialData);
  const [step, setStep] = useState(Math.min(initialStep, definition.steps.length - 1));
  const [saved, setSaved] = useState<"idle" | "saving" | "saved">("idle");
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const dirty = useRef(false);

  // Autosave the draft shortly after the user stops typing.
  useEffect(() => {
    if (!dirty.current) return;
    setSaved("saving");
    const timer = setTimeout(() => {
      saveDraft(definition.code, step, data)
        .then(() => setSaved("saved"))
        .catch(() => setSaved("idle"));
    }, 700);
    return () => clearTimeout(timer);
  }, [data, step, definition.code]);

  const current = definition.steps[step];
  const last = step === definition.steps.length - 1;
  const missing = current.fields.filter((f) => f.required && isEmpty(data[f.key]));

  const set = (key: string, value: FormData[string]) => {
    dirty.current = true;
    setData((d) => ({ ...d, [key]: value }));
  };

  function go(delta: number) {
    dirty.current = true;
    setError(null);
    setStep((s) => s + delta);
  }

  async function submit() {
    setSending(true);
    setError(null);
    try {
      onSubmitted(await submitApplication(definition.code, data));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nie udało się złożyć wniosku.");
    } finally {
      setSending(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{definition.title_pl}</CardTitle>
        <CardDescription>{definition.description_pl}</CardDescription>
        <div className="mt-2 flex gap-1.5" aria-label="Postęp">
          {definition.steps.map((s, i) => (
            <span key={s.title_pl} className={cn("h-1.5 flex-1 rounded-full", i <= step ? "bg-primary" : "bg-muted")} />
          ))}
        </div>
        <p className="text-xs text-muted-foreground">
          Krok {step + 1} z {definition.steps.length}: {current.title_pl}
        </p>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          {current.fields.map((field) => (
            <div key={field.key} className={cn(field.type === "textarea" || field.type === "checkbox" ? "sm:col-span-2" : "")}>
              <FieldInput field={field} value={data[field.key]} onChange={(v) => set(field.key, v)} />
            </div>
          ))}
        </div>
        {error && (
          <div role="alert" className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm">
            {error}
          </div>
        )}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Button variant="outline" onClick={step === 0 ? onClose : () => go(-1)}>
            <ArrowLeft /> {step === 0 ? "Zamknij" : "Wstecz"}
          </Button>
          <span className="text-xs text-muted-foreground" aria-live="polite">
            {saved === "saving" && "Zapisuję wersję roboczą…"}
            {saved === "saved" && (
              <span className="inline-flex items-center gap-1">
                <Save className="size-3.5" /> Wersja robocza zapisana
              </span>
            )}
          </span>
          {last ? (
            <Button onClick={submit} disabled={sending || missing.length > 0}>
              {sending ? <Loader2 className="animate-spin" /> : <Check />}
              {{ zus: "Wyślij do ZUS", employer: "Wyślij do pracodawcy", registry: "Wyślij do urzędu" }[definition.submitted_to]}
            </Button>
          ) : (
            <Button onClick={() => go(1)} disabled={missing.length > 0}>
              Dalej <ArrowRight />
            </Button>
          )}
        </div>
        {missing.length > 0 && (
          <p className="text-xs text-muted-foreground">Uzupełnij pola oznaczone gwiazdką, aby przejść dalej.</p>
        )}
      </CardContent>
    </Card>
  );
}
