"use client";

import { ChevronDown, Info, Loader2, LogOut, Search } from "lucide-react";
import { Fragment, useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
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

import { DependenciesTab, DictionaryTab } from "./dictionary-tab";
import { RulesTab } from "./rules-tab";
import { TestTab } from "./test-tab";

type Tab =
  "parameters" | "rules" | "dictionary" | "graph" | "test" | "applications";
const TABS: [Tab, string][] = [
  ["parameters", "Parametry i stawki"],
  ["rules", "Reguły"],
  ["dictionary", "Słownik danych"],
  ["graph", "Zależności"],
  ["test", "Test na profilu"],
  ["applications", "Wnioski"],
];

const TOKEN_KEY = "parent-guide:admin-token";
const STATUS_LABEL: Record<ApplicationStatus, string> = {
  submitted: "Złożony",
  in_progress: "W rozpatrzeniu",
  decided: "Rozpatrzony",
};
const RECIPIENT: Record<string, string> = {
  zus: "ZUS",
  registry: "Urząd stanu cywilnego",
};

// Order of groups in the panel (anything else goes last) – same as backend parameter_labels.GROUP_ORDER.
const GROUP_ORDER = [
  "Stawki zasiłku",
  "Urlop macierzyński",
  "Urlop rodzicielski",
  "Urlop ojcowski",
  "Przyjęcie dziecka na wychowanie",
  "Podstawa i kwoty",
  "Uprawnienia i płatnik",
  "Terminy wniosków",
  "Zasiłek chorobowy w ciąży",
  "Inne świadczenia",
];

const UNIT: Record<string, string> = {
  weeks: "tyg.",
  days: "dni",
  months: "mies.",
  years: "lat",
  pln: "zł",
  people: "os.",
  pct: "%",
  number: "",
};

const todayIso = () => new Date().toLocaleDateString("sv-SE");
const plNumber = (n: number) =>
  n.toLocaleString("pl-PL", { maximumFractionDigits: 2 });

/** Stored value -> what the administrator types (percentages are stored as fractions). */
const toInput = (v: number, unit: string) =>
  unit === "pct" ? +(v * 100).toFixed(4) : v;
const fromInput = (v: number, unit: string) =>
  unit === "pct" ? +(v / 100).toFixed(6) : v;

function formatScalar(v: unknown, unit: string): string {
  if (v === null || v === undefined) return "nie ustalono";
  if (Array.isArray(v))
    return (
      v.map((x) => formatScalar(x, "number")).join("–") +
      (UNIT[unit] ? ` ${UNIT[unit]}` : "")
    );
  if (typeof v !== "number") return String(v);
  const n = plNumber(toInput(v, unit));
  return unit === "pct" ? `${n}%` : `${n}${UNIT[unit] ? ` ${UNIT[unit]}` : ""}`;
}

/** Compact value: "20 tyg." or "1 dziecko 20 · 2 dzieci 31 · …" (unit once at the end). */
function ValueView({ p }: { p: AdminParameter }) {
  if (p.value && typeof p.value === "object" && !Array.isArray(p.value)) {
    const entries = Object.entries(p.value as Record<string, unknown>);
    return (
      <span className="flex flex-wrap gap-x-3 gap-y-0.5">
        {entries.map(([k, v]) => (
          <span key={k} className="whitespace-nowrap">
            <span className="text-muted-foreground">
              {p.value_labels[k] ?? k}:
            </span>{" "}
            <b>{formatScalar(v, p.unit)}</b>
          </span>
        ))}
      </span>
    );
  }
  return <b>{formatScalar(p.value, p.unit)}</b>;
}

function errorText(err: unknown): string {
  const raw = err instanceof Error ? err.message : "";
  if (raw.includes("API 422") && raw.includes("past"))
    return "Zmiana nie może działać wstecz – dotyczy nowych wniosków.";
  if (raw.includes("API 422"))
    return "Nowa wartość musi mieć tę samą postać co obecna (liczby w tych samych polach).";
  if (raw.includes("API 409"))
    return "Istnieje już późniejsza wersja tego parametru – zmień ją albo usuń w historii.";
  if (raw.includes("API 401"))
    return "Sesja administratora wygasła – zaloguj się ponownie.";
  return "Nie udało się zapisać zmiany.";
}

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
    <form
      onSubmit={submit}
      className="flex max-w-sm flex-col gap-4 border border-border p-5"
    >
      <p className="text-sm text-muted-foreground">
        Hasło administratora (w wersji demonstracyjnej: admin).
      </p>
      <Field label="Hasło">
        <Input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoFocus
        />
      </Field>
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
      <Button type="submit" disabled={busy || !password}>
        {busy && <Loader2 className="animate-spin" />} Zaloguj
      </Button>
    </form>
  );
}

/** Inline editor: one number field per value (tables get one per row), date defaults to today. */
function Editor({
  p,
  token,
  onDone,
  onCancel,
}: {
  p: AdminParameter;
  token: string;
  onDone: (message: string) => void;
  onCancel: () => void;
}) {
  const isTable =
    p.value !== null && typeof p.value === "object" && !Array.isArray(p.value);
  const initial: Record<string, number | number[]> = isTable
    ? Object.fromEntries(
        Object.entries(p.value as Record<string, number | number[]>).map(
          ([k, v]) => [k, Array.isArray(v) ? v : toInput(v, p.unit)],
        ),
      )
    : {
        value: Array.isArray(p.value)
          ? (p.value as number[])
          : toInput(p.value as number, p.unit),
      };
  const [fields, setFields] = useState(initial);
  const [later, setLater] = useState(false);
  const [validFrom, setValidFrom] = useState(todayIso());
  const [basis, setBasis] = useState(p.legal_basis);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const set = (k: string, v: number | number[]) =>
    setFields((f) => ({ ...f, [k]: v }));
  const build = (v: number | number[]) =>
    Array.isArray(v) ? v : fromInput(v, p.unit);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const value = isTable
      ? Object.fromEntries(
          Object.entries(fields).map(([k, v]) => [k, build(v)]),
        )
      : build(fields.value);
    try {
      const res = await adminAddVersion(token, p.key, {
        value,
        valid_from: later ? validFrom : undefined,
        legal_basis: basis,
      });
      const from = formatDate(res.parameter.valid_from);
      onDone(
        `„${p.label_pl}” zmieniono. Nowe wnioski składane od ${from} korzystają z nowej wartości. ` +
          `Złożone wnioski (${res.applications_kept}) zachowują wartości z dnia złożenia.`,
      );
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  const numberInput = (k: string, v: number | number[], label: string) =>
    Array.isArray(v) ? (
      <Field key={k} label={label}>
        <div className="flex items-center gap-2">
          {v.map((x, i) => (
            <Input
              key={i}
              type="number"
              step="any"
              value={x}
              onChange={(e) =>
                set(
                  k,
                  v.map((y, j) => (j === i ? Number(e.target.value) : y)),
                )
              }
              className="h-9"
            />
          ))}
        </div>
      </Field>
    ) : (
      <Field key={k} label={label}>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            step="any"
            value={v}
            onChange={(e) => set(k, Number(e.target.value))}
            className="h-9"
          />
          <span className="w-10 shrink-0 text-sm text-muted-foreground">
            {UNIT[p.unit]}
          </span>
        </div>
      </Field>
    );

  return (
    <form
      onSubmit={save}
      className="flex flex-col gap-3 border-l-[5px] border-primary bg-muted p-4"
    >
      <p className="text-sm text-muted-foreground">{p.description_pl}</p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Object.entries(fields).map(([k, v]) =>
          numberInput(
            k,
            v,
            isTable ? (p.value_labels[k] ?? k) : "Nowa wartość",
          ),
        )}
      </div>
      <Field label="Podstawa prawna">
        <Input
          value={basis}
          onChange={(e) => setBasis(e.target.value)}
          className="h-9"
        />
      </Field>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={later}
          onChange={(e) => setLater(e.target.checked)}
          className="accent-primary"
        />
        Przepis wchodzi w życie później – ustaw datę
      </label>
      {later && (
        <Field label="Obowiązuje od" className="max-w-xs">
          <Input
            type="date"
            value={validFrom}
            min={todayIso()}
            onChange={(e) => setValidFrom(e.target.value)}
            className="h-9"
          />
        </Field>
      )}
      <p className="flex items-start gap-2 text-sm">
        <Info className="mt-0.5 size-4 shrink-0 text-navy" />
        Zmiana obejmie wnioski składane od{" "}
        {later ? formatDate(validFrom) : "dziś"}. Wnioski już złożone się nie
        zmienią.
      </p>
      {error && (
        <p role="alert" className="text-sm font-bold text-destructive">
          {error}
        </p>
      )}
      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={busy}>
          {busy && <Loader2 className="animate-spin" />} Zapisz zmianę
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
  const [group, setGroup] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [history, setHistory] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    () =>
      adminParameters(token)
        .then(setRows)
        .catch(() => setError("Nie udało się wczytać parametrów.")),
    [token],
  );
  useEffect(() => void load(), [load]);

  // key -> versions (newest first), grouped and filtered
  const groups = useMemo(() => {
    const byKey = new Map<string, AdminParameter[]>();
    for (const row of rows ?? [])
      byKey.set(row.key, [...(byKey.get(row.key) ?? []), row]);
    const q = query.trim().toLowerCase();
    const out = new Map<string, AdminParameter[][]>();
    for (const versions of byKey.values()) {
      const shown = versions.find((v) => v.current) ?? versions[0];
      if (group && shown.group_pl !== group) continue;
      if (
        q &&
        !`${shown.label_pl} ${shown.description_pl}`.toLowerCase().includes(q)
      )
        continue;
      out.set(shown.group_pl, [...(out.get(shown.group_pl) ?? []), versions]);
    }
    const rank = (g: string) => GROUP_ORDER.indexOf(g) + 1 || 99;
    return [...out.entries()].sort(([a], [b]) => rank(a) - rank(b));
  }, [rows, query, group]);

  const allGroups = useMemo(
    () =>
      [...new Set((rows ?? []).map((r) => r.group_pl))].sort(
        (a, b) =>
          (GROUP_ORDER.indexOf(a) + 1 || 99) -
          (GROUP_ORDER.indexOf(b) + 1 || 99),
      ),
    [rows],
  );

  async function remove(p: AdminParameter) {
    try {
      await adminDeleteVersion(token, p.key, p.valid_from);
      setNotice(
        `Usunięto zmianę „${p.label_pl}” z ${formatDate(p.valid_from)} – wraca poprzednia wartość.`,
      );
      await load();
    } catch {
      setError("Nie udało się usunąć zmiany.");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-2 sm:grid-cols-[1fr_16rem]">
        <label className="relative">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-icon" />
          <Input
            placeholder="Szukaj, np. stawka, ojcowski, termin"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="h-10 pl-9"
            aria-label="Szukaj parametru"
          />
        </label>
        <Select
          value={group}
          onChange={(e) => setGroup(e.target.value)}
          className="h-10"
          aria-label="Grupa"
        >
          <option value="">Wszystkie grupy</option>
          {allGroups.map((g) => (
            <option key={g}>{g}</option>
          ))}
        </Select>
      </div>
      {notice && (
        <div
          role="status"
          className="border-l-[5px] border-primary bg-secondary p-3 text-sm"
        >
          {notice}
        </div>
      )}
      {error && (
        <div
          role="alert"
          className="border-l-[5px] border-destructive bg-muted p-3 text-sm"
        >
          {error}
        </div>
      )}
      {!rows && <Loader2 className="animate-spin text-muted-foreground" />}

      {groups.map(([name, items]) => (
        <section key={name}>
          <h2 className="border-b-2 border-primary pb-1 text-base font-bold">
            {name}
          </h2>
          <table className="w-full text-sm">
            <tbody>
              {items.map((versions) => {
                const p = versions.find((v) => v.current) ?? versions[0];
                const future = versions.find((v) => v.valid_from > todayIso());
                return (
                  <Fragment key={p.key}>
                    <tr className="border-b border-border align-top">
                      <td className="w-[38%] py-2 pr-3">
                        <span className="font-bold" title={p.description_pl}>
                          {p.label_pl}
                        </span>
                        {future && (
                          <span className="mt-0.5 block text-xs text-navy">
                            od {formatDate(future.valid_from)}:{" "}
                            {formatScalar(future.value, future.unit)}
                          </span>
                        )}
                      </td>
                      <td className="py-2 pr-3">
                        <ValueView p={p} />
                      </td>
                      <td className="hidden w-32 whitespace-nowrap py-2 pr-3 text-xs text-muted-foreground md:table-cell">
                        od {formatDate(p.valid_from)}
                        {versions.length > 1 && (
                          <button
                            type="button"
                            onClick={() =>
                              setHistory(history === p.key ? null : p.key)
                            }
                            className="mt-0.5 flex items-center gap-0.5 text-link hover:underline"
                          >
                            historia ({versions.length})
                            <ChevronDown
                              className={cn(
                                "size-3",
                                history === p.key && "rotate-180",
                              )}
                            />
                          </button>
                        )}
                      </td>
                      <td className="w-20 py-1.5 text-right">
                        <Button
                          size="sm"
                          variant={editing === p.key ? "default" : "outline"}
                          onClick={() =>
                            setEditing(editing === p.key ? null : p.key)
                          }
                        >
                          Zmień
                        </Button>
                      </td>
                    </tr>
                    {history === p.key && (
                      <tr>
                        <td colSpan={4} className="bg-muted px-3 py-2">
                          <ul className="flex flex-col gap-1 text-xs">
                            {versions.map((v) => (
                              <li
                                key={v.valid_from}
                                className="flex flex-wrap items-center gap-2"
                              >
                                <span className="w-44">
                                  {formatDate(v.valid_from)} –{" "}
                                  {v.valid_to
                                    ? formatDate(v.valid_to)
                                    : "bez końca"}
                                </span>
                                <ValueView p={v} />
                                {v.current && (
                                  <span className="font-bold text-primary">
                                    obowiązuje
                                  </span>
                                )}
                                {!v.from_seed && (
                                  <button
                                    type="button"
                                    className="text-destructive hover:underline"
                                    onClick={() => remove(v)}
                                  >
                                    cofnij tę zmianę
                                  </button>
                                )}
                              </li>
                            ))}
                          </ul>
                        </td>
                      </tr>
                    )}
                    {editing === p.key && (
                      <tr>
                        <td colSpan={4} className="py-2">
                          <Editor
                            p={versions[0]}
                            token={token}
                            onCancel={() => setEditing(null)}
                            onDone={(message) => {
                              setEditing(null);
                              setNotice(message);
                              setError(null);
                              void load();
                            }}
                          />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </section>
      ))}
      {rows && groups.length === 0 && (
        <p className="text-sm text-muted-foreground">
          Brak parametrów dla tego wyszukiwania.
        </p>
      )}
    </div>
  );
}

function ApplicationsTab({ token }: { token: string }) {
  const [rows, setRows] = useState<AdminApplication[] | null>(null);
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    () =>
      adminApplications(token)
        .then(setRows)
        .catch(() => setError("Nie udało się wczytać wniosków.")),
    [token],
  );
  useEffect(() => void load(), [load]);

  async function change(id: number, status: ApplicationStatus) {
    try {
      await adminSetStatus(token, id, status, notes[id]);
      setNotes((n) => ({ ...n, [id]: "" }));
      await load();
    } catch {
      setError("Nie udało się zmienić statusu.");
    }
  }

  if (error)
    return (
      <p role="alert" className="text-sm text-destructive">
        {error}
      </p>
    );
  if (!rows) return <Loader2 className="animate-spin text-muted-foreground" />;
  if (rows.length === 0)
    return (
      <p className="text-sm text-muted-foreground">
        Nikt nie złożył jeszcze wniosku.
      </p>
    );

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-sm">
        <thead>
          <tr className="border-b-2 border-primary text-left">
            <th className="py-2 pr-3">Nr</th>
            <th className="py-2 pr-3">Wniosek</th>
            <th className="py-2 pr-3">Adresat</th>
            <th className="py-2 pr-3">Złożony</th>
            <th className="py-2 pr-3">Notatka do decyzji</th>
            <th className="py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((a) => (
            <tr key={a.id} className="border-b border-border align-top">
              <td className="py-2 pr-3 font-bold">{a.id}</td>
              <td className="py-2 pr-3">
                <span className="font-bold">{a.title_pl}</span>
                <span className="block text-xs text-muted-foreground">
                  {a.owner_id}
                  {a.last_note ? ` · ${a.last_note}` : ""}
                </span>
              </td>
              <td className="py-2 pr-3">
                {RECIPIENT[a.submitted_to ?? ""] ?? "Pracodawca"}
              </td>
              <td className="py-2 pr-3 text-xs">
                {a.created_at ? formatDate(a.created_at.slice(0, 10)) : "–"}
                {a.params_count > 0 && (
                  <span className="block text-muted-foreground">
                    parametry z dnia złożenia
                  </span>
                )}
              </td>
              <td className="py-1.5 pr-3">
                <Input
                  placeholder="opcjonalnie"
                  value={notes[a.id] ?? ""}
                  onChange={(e) =>
                    setNotes((n) => ({ ...n, [a.id]: e.target.value }))
                  }
                  className="h-9"
                  aria-label={`Notatka do wniosku ${a.id}`}
                />
              </td>
              <td className="py-1.5">
                <Select
                  value={a.status}
                  onChange={(e) =>
                    change(a.id, e.target.value as ApplicationStatus)
                  }
                  className="h-9"
                  aria-label={`Status wniosku ${a.id}`}
                >
                  {(Object.keys(STATUS_LABEL) as ApplicationStatus[]).map(
                    (s) => (
                      <option key={s} value={s}>
                        {STATUS_LABEL[s]}
                      </option>
                    ),
                  )}
                </Select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AdminView() {
  const [token, setToken] = useState<string | null | undefined>(undefined);
  const [tab, setTab] = useState<Tab>("parameters");

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
    <div className="flex flex-col gap-5">
      <div className="flex items-end justify-between gap-3 border-b border-band-border">
        <div role="tablist" className="flex flex-wrap">
          {TABS.map(([id, label]) => (
            <button
              key={id}
              role="tab"
              aria-selected={tab === id}
              onClick={() => setTab(id)}
              className={cn(
                "-mb-px border-b-4 px-4 py-2 text-[15px] font-bold",
                tab === id
                  ? "border-primary text-foreground"
                  : "border-transparent text-link hover:underline",
              )}
            >
              {label}
            </button>
          ))}
        </div>
        <button
          type="button"
          className="mb-2 flex items-center gap-1 text-sm text-link hover:underline"
          onClick={() => {
            sessionStorage.removeItem(TOKEN_KEY);
            setToken(null);
          }}
        >
          <LogOut className="size-4" /> Wyloguj
        </button>
      </div>
      {tab === "parameters" && (
        <p className="flex items-start gap-2 text-sm">
          <Info className="mt-0.5 size-4 shrink-0 text-navy" />
          Zmiana parametru obejmuje wnioski składane od dziś (albo od wskazanej
          daty wejścia przepisu w życie). Wnioski już złożone zachowują wartości
          z dnia złożenia.
        </p>
      )}
      {tab === "parameters" && <ParametersTab token={token} />}
      {tab === "rules" && <RulesTab token={token} />}
      {tab === "dictionary" && <DictionaryTab token={token} />}
      {tab === "graph" && <DependenciesTab token={token} />}
      {tab === "test" && <TestTab token={token} />}
      {tab === "applications" && <ApplicationsTab token={token} />}
    </div>
  );
}
