"use client";

import { Loader2, LogOut } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select } from "@/components/ui/form-controls";
import {
  adminAddVersion,
  adminApplications,
  adminCheck,
  adminDeleteVersion,
  adminParameters,
  adminSetStatus,
  type AdminApplication,
  type AdminParameter,
  type ApplicationStatus,
} from "@/lib/api";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

const TOKEN_KEY = "parent-guide:admin-token";
const STATUS_LABEL: Record<ApplicationStatus, string> = {
  submitted: "Złożony",
  in_progress: "W rozpatrzeniu",
  decided: "Rozpatrzony",
};

const pretty = (value: unknown) => JSON.stringify(value, null, typeof value === "object" ? 2 : 0);
const todayIso = () => new Date().toISOString().slice(0, 10);

function Login({ onLogin }: { onLogin: (token: string) => void }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await adminCheck(password);
      sessionStorage.setItem(TOKEN_KEY, password);
      onLogin(password);
    } catch {
      setError("Nieprawidłowe hasło.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="mx-auto max-w-md">
      <CardHeader>
        <CardTitle>Panel administratora</CardTitle>
        <CardDescription>Podaj hasło administratora (w środowisku demo: admin).</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="flex flex-col gap-4">
          <Field label="Hasło">
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoFocus />
          </Field>
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
          <Button type="submit" disabled={busy || !password}>
            {busy && <Loader2 className="animate-spin" />} Zaloguj
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function ParameterEditor({
  versions,
  token,
  onDone,
  onCancel,
}: {
  versions: AdminParameter[];
  token: string;
  onDone: (message: string) => void;
  onCancel: () => void;
}) {
  const latest = versions[0];
  const [valueText, setValueText] = useState(pretty(latest.value));
  const [validFrom, setValidFrom] = useState(todayIso() > latest.valid_from ? todayIso() : "");
  const [basis, setBasis] = useState(latest.legal_basis);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    let value: unknown;
    try {
      value = JSON.parse(valueText);
    } catch {
      setError("Wartość musi być poprawnym JSON (liczba, tekst albo obiekt).");
      return;
    }
    setBusy(true);
    try {
      await adminAddVersion(token, latest.key, { value, valid_from: validFrom, legal_basis: basis });
      onDone(`Zapisano nową wersję parametru ${latest.key} od ${formatDate(validFrom)}.`);
    } catch (err) {
      const raw = err instanceof Error ? err.message : "Nie udało się zapisać.";
      setError(raw.replace(/^API \d+: /, "").replace(/^\{"detail":"?|"?\}$/g, ""));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={save} className="mt-3 flex flex-col gap-3 rounded-lg border bg-muted/40 p-3">
      <Field label="Nowa wartość (JSON)" hint="Typ i klucze muszą zgadzać się z obecną wartością.">
        <textarea
          className="min-h-24 w-full rounded-md border bg-background px-3 py-2 font-mono text-xs outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
          value={valueText}
          onChange={(e) => setValueText(e.target.value)}
        />
      </Field>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Obowiązuje od" hint={`Po ${formatDate(latest.valid_from)} (data obecnej wersji).`}>
          <Input type="date" value={validFrom} min={latest.valid_from} onChange={(e) => setValidFrom(e.target.value)} required />
        </Field>
        <Field label="Podstawa prawna">
          <Input value={basis} onChange={(e) => setBasis(e.target.value)} />
        </Field>
      </div>
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={busy || !validFrom}>
          {busy && <Loader2 className="animate-spin" />} Zapisz nową wersję
        </Button>
        <Button type="button" size="sm" variant="outline" onClick={onCancel}>
          Anuluj
        </Button>
      </div>
    </form>
  );
}

function ParametersTab({ token }: { token: string }) {
  const [rows, setRows] = useState<AdminParameter[] | null>(null);
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [history, setHistory] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => adminParameters(token).then(setRows).catch((e: Error) => setError(e.message)), [token]);
  useEffect(() => void load(), [load]);

  const byKey = new Map<string, AdminParameter[]>();
  for (const row of rows ?? []) byKey.set(row.key, [...(byKey.get(row.key) ?? []), row]);
  const keys = [...byKey.keys()].filter((k) => {
    const q = query.toLowerCase();
    return !q || k.includes(q) || byKey.get(k)![0].description_pl.toLowerCase().includes(q);
  });

  async function remove(key: string, validFrom: string) {
    try {
      await adminDeleteVersion(token, key, validFrom);
      setNotice(`Usunięto wersję ${key} od ${formatDate(validFrom)}.`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nie udało się usunąć.");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">
        Zmiana tworzy nową wersję od wskazanej daty – poprzednia kończy się dzień wcześniej, więc dawne sprawy liczą
        się według dawnych przepisów. Kalkulator korzysta z nowej wartości od razu.
      </p>
      <Input placeholder="Szukaj parametru…" value={query} onChange={(e) => setQuery(e.target.value)} />
      {notice && <div className="rounded-lg border border-primary/40 bg-secondary p-3 text-sm">{notice}</div>}
      {error && <div role="alert" className="rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm">{error}</div>}
      {!rows && <Loader2 className="animate-spin text-muted-foreground" />}
      <ul className="flex flex-col gap-3">
        {keys.map((key) => {
          const versions = byKey.get(key)!;
          const shown = versions.find((v) => v.current) ?? versions[0];
          return (
            <li key={key} className="rounded-lg border p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-mono text-sm font-medium">{key}</p>
                <div className="flex gap-2">
                  {versions.length > 1 && (
                    <Button size="sm" variant="ghost" onClick={() => setHistory(history === key ? null : key)}>
                      Historia ({versions.length})
                    </Button>
                  )}
                  <Button size="sm" variant="outline" onClick={() => setEditing(editing === key ? null : key)}>
                    Zmień
                  </Button>
                </div>
              </div>
              <p className="text-sm text-muted-foreground">{shown.description_pl}</p>
              <pre className="mt-2 whitespace-pre-wrap break-words rounded bg-muted px-2 py-1 font-mono text-xs">
                {pretty(shown.value)}
              </pre>
              <p className="mt-1 text-xs text-muted-foreground">
                Od {formatDate(shown.valid_from)} · {shown.legal_basis}
              </p>
              {history === key && (
                <ul className="mt-3 flex flex-col gap-1 border-l-2 pl-3 text-xs">
                  {versions.map((v) => (
                    <li key={v.valid_from} className="flex flex-wrap items-center gap-2">
                      <span>
                        {formatDate(v.valid_from)} – {v.valid_to ? formatDate(v.valid_to) : "obowiązuje"}:{" "}
                        <code>{JSON.stringify(v.value)}</code>
                      </span>
                      {v.current && <Badge>teraz</Badge>}
                      {!v.from_seed && (
                        <Button size="sm" variant="ghost" onClick={() => remove(v.key, v.valid_from)}>
                          Usuń wersję
                        </Button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
              {editing === key && (
                <ParameterEditor
                  versions={versions}
                  token={token}
                  onCancel={() => setEditing(null)}
                  onDone={(message) => {
                    setEditing(null);
                    setNotice(message);
                    setError(null);
                    void load();
                  }}
                />
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function ApplicationsTab({ token }: { token: string }) {
  const [rows, setRows] = useState<AdminApplication[] | null>(null);
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => adminApplications(token).then(setRows).catch((e: Error) => setError(e.message)), [token]);
  useEffect(() => void load(), [load]);

  async function change(id: number, status: ApplicationStatus) {
    try {
      await adminSetStatus(token, id, status, notes[id]);
      setNotes((n) => ({ ...n, [id]: "" }));
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nie udało się zmienić statusu.");
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {error && <div role="alert" className="rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm">{error}</div>}
      {!rows && <Loader2 className="animate-spin text-muted-foreground" />}
      {rows?.length === 0 && <p className="text-sm text-muted-foreground">Nikt nie złożył jeszcze wniosku.</p>}
      {rows?.map((a) => (
        <div key={a.id} className="rounded-lg border p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="font-medium">
              #{a.id} {a.title_pl}
            </p>
            <Badge variant={a.status === "decided" ? "default" : "secondary"}>{STATUS_LABEL[a.status]}</Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            Wnioskodawca: {a.owner_id} · adresat: {{ zus: "ZUS", registry: "urząd stanu cywilnego" }[a.submitted_to ?? ""] ?? "pracodawca"}
          </p>
          {a.last_note && <p className="mt-1 text-sm">{a.last_note}</p>}
          <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto_auto]">
            <Input
              placeholder="Notatka do decyzji (opcjonalnie)"
              value={notes[a.id] ?? ""}
              onChange={(e) => setNotes((n) => ({ ...n, [a.id]: e.target.value }))}
            />
            <Select value={a.status} onChange={(e) => change(a.id, e.target.value as ApplicationStatus)} aria-label="Status">
              {(Object.keys(STATUS_LABEL) as ApplicationStatus[]).map((s) => (
                <option key={s} value={s}>
                  {STATUS_LABEL[s]}
                </option>
              ))}
            </Select>
          </div>
        </div>
      ))}
    </div>
  );
}

export function AdminView() {
  const [token, setToken] = useState<string | null | undefined>(undefined);
  const [tab, setTab] = useState<"parameters" | "applications">("parameters");

  useEffect(() => {
    const saved = sessionStorage.getItem(TOKEN_KEY);
    if (!saved) return setToken(null);
    adminCheck(saved)
      .then(() => setToken(saved))
      .catch(() => setToken(null));
  }, []);

  if (token === undefined) return null;
  if (token === null) return <Login onLogin={setToken} />;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div role="tablist" className="flex gap-2">
          {(
            [
              ["parameters", "Parametry prawne"],
              ["applications", "Wnioski"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              role="tab"
              aria-selected={tab === id}
              onClick={() => setTab(id)}
              className={cn(
                "rounded-full border px-3 py-1 text-sm transition-colors",
                tab === id ? "border-primary bg-primary text-primary-foreground" : "hover:bg-muted",
              )}
            >
              {label}
            </button>
          ))}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            sessionStorage.removeItem(TOKEN_KEY);
            setToken(null);
          }}
        >
          <LogOut /> Wyloguj
        </Button>
      </div>
      {tab === "parameters" ? <ParametersTab token={token} /> : <ApplicationsTab token={token} />}
    </div>
  );
}
