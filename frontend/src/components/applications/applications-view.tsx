"use client";

import { FilePlus2, Loader2, Play } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ApplicationForm } from "@/components/applications/application-form";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  advanceApplication,
  getSuggestions,
  listApplications,
  listDrafts,
  listForms,
  type ApplicationRecord,
  type ApplicationStatus,
  type Draft,
  type FamilyProfile,
  type FormData,
  type FormDefinition,
  type Suggestion,
} from "@/lib/api";
import { formatDate, formatDaysLeft } from "@/lib/format";
import { loadLastProfile } from "@/lib/last-result";
import { PUBLIC_PATHS } from "@/lib/routes";

const STATUS_LABEL: Record<ApplicationStatus, string> = {
  submitted: "Złożony",
  in_progress: "W rozpatrzeniu",
  decided: "Rozpatrzony",
};
const TO_LABEL = { employer: "pracodawca", zus: "ZUS", registry: "urząd stanu cywilnego" } as const;

type Editing = { definition: FormDefinition; data: FormData; step: number };

export function ApplicationsView() {
  const [forms, setForms] = useState<FormDefinition[]>([]);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[] | null>(null);
  const [hasProfile, setHasProfile] = useState(true);
  const [editing, setEditing] = useState<Editing | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const refresh = useCallback(async () => {
    const [d, a] = await Promise.all([listDrafts(), listApplications()]);
    setDrafts(d);
    setApplications(a);
  }, []);

  useEffect(() => {
    const profile = loadLastProfile<FamilyProfile>();
    setHasProfile(Boolean(profile));
    Promise.all([listForms(), refresh(), profile ? getSuggestions(profile) : Promise.resolve(null)])
      .then(([f, , s]) => {
        setForms(f);
        setSuggestions(s);
        // A link such as /wnioski?form=civil_registry_extract opens that form straight away.
        const wanted = new URLSearchParams(window.location.search).get("form");
        const definition = f.find((item) => item.code === wanted);
        if (definition) setEditing({ definition, data: {}, step: 0 });
      })
      .catch((e: Error) => setError(e.message));
  }, [refresh]);

  const definitionOf = (code: string) => forms.find((f) => f.code === code);

  function open(code: string, data: FormData = {}, step = 0) {
    const definition = definitionOf(code);
    if (!definition) return;
    setNotice(null);
    setEditing({ definition, data, step });
    requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "smooth" }));
  }

  async function advance(id: number) {
    setBusyId(id);
    try {
      await advanceApplication(id);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nie udało się zmienić statusu.");
    } finally {
      setBusyId(null);
    }
  }

  if (editing) {
    return (
      <ApplicationForm
        key={editing.definition.code}
        definition={editing.definition}
        initialData={editing.data}
        initialStep={editing.step}
        onClose={() => {
          setEditing(null);
          void refresh();
        }}
        onSubmitted={(application) => {
          setEditing(null);
          setNotice(
            `Wniosek „${application.title_pl}” został wysłany (${TO_LABEL[application.submitted_to ?? "zus"]}). ` +
              "Śledź jego status poniżej.",
          );
          void refresh();
        }}
      />
    );
  }

  return (
    <div className="flex flex-col gap-8">
      {error && (
        <div role="alert" className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm">
          {error}
        </div>
      )}
      {notice && <div className="rounded-xl border border-primary/40 bg-secondary p-4 text-sm">{notice}</div>}

      <section className="flex flex-col gap-3">
        <h2 className="text-xl font-semibold">Wnioski do złożenia</h2>
        {!hasProfile && (
          <div className="flex flex-col items-start gap-3 rounded-xl border border-dashed p-5 text-sm">
            <p>
              Policz najpierw uprawnienia – podpowiemy, jakie wnioski złożyć, i wypełnimy je danymi z wyliczenia.
            </p>
            <Button asChild>
              <Link href={PUBLIC_PATHS.calculator}>Sprawdź uprawnienia</Link>
            </Button>
          </div>
        )}
        {suggestions && suggestions.length === 0 && (
          <p className="text-sm text-muted-foreground">Z tego wyliczenia nie wynikają wnioski do złożenia.</p>
        )}
        <div className="grid gap-3 sm:grid-cols-2">
          {suggestions?.map((s) => (
            <Card key={`${s.form_code}-${s.person}`}>
              <CardHeader>
                <CardTitle className="text-base">{s.title_pl}</CardTitle>
                <CardDescription>Adresat: {TO_LABEL[s.submitted_to]}</CardDescription>
              </CardHeader>
              <CardContent className="mt-auto flex flex-col gap-3">
                {s.deadline && s.days_left !== null && (
                  <p className="text-sm">
                    Najpóźniej do {formatDate(s.deadline)} ({formatDaysLeft(s.days_left)})
                  </p>
                )}
                <Button onClick={() => open(s.form_code, s.prefill)}>
                  <FilePlus2 /> Wypełnij wniosek
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
        <details className="text-sm">
          <summary className="cursor-pointer text-muted-foreground">Inny wniosek</summary>
          <div className="mt-3 flex flex-wrap gap-2">
            {forms.map((f) => (
              <Button key={f.code} variant="outline" size="sm" onClick={() => open(f.code)}>
                {f.title_pl}
              </Button>
            ))}
          </div>
        </details>
      </section>

      {drafts.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-xl font-semibold">Wersje robocze</h2>
          <ul className="flex flex-col gap-2">
            {drafts.map((d) => (
              <li key={d.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3">
                <div>
                  <p className="font-medium">{definitionOf(d.form_code)?.title_pl ?? d.form_code}</p>
                  {d.updated_at && (
                    <p className="text-xs text-muted-foreground">Zapisano {formatDate(d.updated_at.slice(0, 10))}</p>
                  )}
                </div>
                <Button variant="outline" size="sm" onClick={() => open(d.form_code, d.data, d.step)}>
                  Kontynuuj
                </Button>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="flex flex-col gap-3">
        <h2 className="text-xl font-semibold">Złożone wnioski</h2>
        {applications.length === 0 && <p className="text-sm text-muted-foreground">Nie złożono jeszcze żadnego wniosku.</p>}
        <ul className="flex flex-col gap-3">
          {applications.map((a) => (
            <li key={a.id} className="rounded-lg border p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-medium">{a.title_pl}</p>
                <Badge variant={a.status === "decided" ? "default" : "secondary"}>{STATUS_LABEL[a.status]}</Badge>
              </div>
              <p className="text-xs text-muted-foreground">Adresat: {a.submitted_to ? TO_LABEL[a.submitted_to] : "–"}</p>
              <ol className="mt-3 flex flex-col gap-1 border-l-2 border-primary/40 pl-3 text-sm">
                {a.history.map((h) => (
                  <li key={h.at + h.status}>
                    <span className="text-xs text-muted-foreground">{h.at.slice(0, 10)} · </span>
                    {h.note}
                  </li>
                ))}
              </ol>
              {a.status !== "decided" && (
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-3"
                  onClick={() => advance(a.id)}
                  disabled={busyId === a.id}
                >
                  {busyId === a.id ? <Loader2 className="animate-spin" /> : <Play />}
                  Symuluj kolejny etap
                </Button>
              )}
            </li>
          ))}
        </ul>
        <p className="text-xs text-muted-foreground">
          Przycisk „Symuluj kolejny etap” działa tylko w demonstracji – w prawdziwym systemie status zmienia
          pracodawca lub ZUS.
        </p>
      </section>
    </div>
  );
}
