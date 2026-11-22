"use client";

import { AlertTriangle, Check, History, Loader2, Plus, RotateCcw, Search, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/form-controls";
import {
  AdminError,
  adminDeleteRule,
  adminResetRule,
  adminRuleHistory,
  adminRules,
  adminSaveRule,
  adminValidateRule,
  type AdminRule,
  type RuleData,
  type RuleKind,
} from "@/lib/api";
import { cn } from "@/lib/utils";

export const KIND_LABEL: Record<RuleKind, string> = {
  wartosc: "Wartość",
  okres: "Okres",
  swiadczenie: "Świadczenie",
  dokument: "Dokument",
  termin: "Termin",
  ryzyko: "Ryzyko",
  informacja: "Informacja",
  zalozenie: "Założenie",
  walidacja: "Walidacja",
};
const KIND_COLOR: Record<RuleKind, string> = {
  wartosc: "bg-muted text-foreground",
  okres: "bg-primary/15 text-foreground",
  swiadczenie: "bg-navy text-white",
  dokument: "bg-muted text-foreground",
  termin: "bg-orange/20 text-foreground",
  ryzyko: "bg-destructive/15 text-foreground",
  informacja: "bg-muted text-foreground",
  zalozenie: "bg-muted text-foreground",
  walidacja: "bg-destructive text-white",
};
export const SOURCE_LABEL: Record<string, string> = {
  KP: "Kodeks pracy",
  UZ: "Ustawa zasiłkowa",
  RZ: "Rozp. – dokumenty do zasiłków",
  RW: "Rozp. – wnioski o urlopy",
  PR: "Poradnik ZUS 2026",
  ZAL: "Załącznik do zadania",
};

/** Which fields the editor shows for each kind of rule. */
type FieldDef = { key: keyof RuleData; label: string; hint?: string; code?: boolean; rows?: number };
const COMMON_TOP: FieldDef[] = [
  { key: "title_pl", label: "Nazwa / tytuł", hint: "Może zawierać {wyrażenie}" },
  { key: "condition", label: "Warunek", hint: "Reguła działa, gdy warunek jest prawdziwy (puste = zawsze)", code: true },
];
const FIELDS: Record<RuleKind, FieldDef[]> = {
  wartosc: [{ key: "expression", label: "Wyrażenie", code: true, rows: 3 }],
  okres: [
    { key: "person", label: "Osoba", hint: "mama, tata albo wyrażenie" },
    { key: "period_kind", label: "Rodzaj okresu" },
    { key: "start", label: "Początek (data)", code: true },
    { key: "expression", label: "Liczba dni", code: true },
    { key: "rate", label: "Stawka (np. 1, 0.7)", code: true },
    { key: "work", label: "Część etatu w pracy (0–0,5)", code: true },
    { key: "payer", label: "Płatnik ('zus' / 'pracodawca')", code: true },
  ],
  swiadczenie: [
    { key: "person", label: "Osoba", hint: "mama, tata, rodzina albo wyrażenie" },
    { key: "status", label: "Status", hint: "przysluguje | warunkowo | nie_przysluguje | informacja", code: true },
    { key: "text_pl", label: "Opis", hint: "Tekst z {wyrażeniami}", rows: 3 },
    { key: "periods", label: "Okresy (kody, po przecinku)" },
    { key: "payer", label: "Płatnik", code: true },
    { key: "apply_to_pl", label: "Gdzie złożyć", rows: 2 },
  ],
  dokument: [
    { key: "person", label: "Osoba" },
    { key: "benefit", label: "Świadczenie (kod karty)" },
    { key: "text_pl", label: "Treść", rows: 3 },
  ],
  termin: [
    { key: "person", label: "Osoba" },
    { key: "benefit", label: "Świadczenie (kod karty)" },
    { key: "deadline_kind", label: "Rodzaj: apply / use_by" },
    { key: "expression", label: "Data terminu", code: true },
    { key: "text_pl", label: "Opis", rows: 2 },
    {
      key: "late_text_pl",
      label: "Porada po terminie",
      hint: "Pokazywana, gdy termin minął: co przepada i co jeszcze da się zrobić. Może zawierać {wyrażenie}",
      rows: 3,
    },
  ],
  ryzyko: [
    { key: "person", label: "Osoba" },
    { key: "severity", label: "Waga: high / medium / info" },
    { key: "text_pl", label: "Treść", rows: 3 },
  ],
  informacja: [{ key: "text_pl", label: "Treść", rows: 3 }],
  zalozenie: [{ key: "text_pl", label: "Treść", rows: 3 }],
  walidacja: [{ key: "text_pl", label: "Komunikat dla użytkownika", rows: 2 }],
};
const COMMON_BOTTOM: FieldDef[] = [
  { key: "legal_basis", label: "Podstawa prawna" },
  { key: "group_pl", label: "Grupa" },
  { key: "description_pl", label: "Opis dla administratora", rows: 2 },
];

const EMPTY: RuleData = {
  code: "",
  kind: "wartosc",
  title_pl: "",
  group_pl: "Reguły dodane w panelu",
  order: 900,
  condition: null,
  expression: "",
  start: null,
  rate: null,
  work: null,
  person: null,
  period_kind: null,
  text_pl: "",
  severity: null,
  benefit: null,
  periods: [],
  status: null,
  payer: null,
  apply_to_pl: "",
  deadline_kind: null,
  late_text_pl: "",
  legal_basis: "",
  source: "UZ",
  description_pl: "",
  active: true,
};

const strip = (r: AdminRule): RuleData => {
  const { modified, in_seed, uses, used_by, facts, parameters, errors, ...data } = r;
  void modified, void in_seed, void uses, void used_by, void facts, void parameters, void errors;
  return data;
};

function Chip({ code, onOpen }: { code: string; onOpen: (c: string) => void }) {
  return (
    <button
      type="button"
      onClick={() => onOpen(code)}
      className="rounded bg-muted px-1.5 py-0.5 font-mono text-[12px] text-link hover:underline"
    >
      {code}
    </button>
  );
}

function RuleEditor({
  token,
  rule,
  isNew,
  onSaved,
  onCancel,
  onOpen,
}: {
  token: string;
  rule: AdminRule | null;
  isNew: boolean;
  onSaved: (code: string) => void;
  onCancel: () => void;
  onOpen: (code: string) => void;
}) {
  const [data, setData] = useState<RuleData>(rule ? strip(rule) : EMPTY);
  const [note, setNote] = useState("");
  const [state, setState] = useState<{ kind: "idle" | "busy" | "ok" | "error"; text?: string; errors?: string[] }>({
    kind: "idle",
  });
  const [history, setHistory] = useState<Awaited<ReturnType<typeof adminRuleHistory>> | null>(null);

  const set = (key: keyof RuleData, value: string) =>
    setData((d) => ({
      ...d,
      [key]: key === "periods" ? value.split(",").map((s) => s.trim()).filter(Boolean) : value,
    }));

  async function run(action: "validate" | "save" | "reset" | "delete" | "toggle") {
    setState({ kind: "busy" });
    try {
      if (action === "validate") {
        const out = await adminValidateRule(token, data, isNew ? undefined : data.code);
        setState(out.ok ? { kind: "ok", text: "Reguła poprawna – zależności i parametry się zgadzają." } : { kind: "error", text: "Reguła ma błędy:", errors: out.errors });
        return;
      }
      if (action === "reset") await adminResetRule(token, data.code);
      else if (action === "delete") await adminDeleteRule(token, data.code);
      else await adminSaveRule(token, { ...data, active: action === "toggle" ? !data.active : data.active, note }, isNew);
      setState({ kind: "ok", text: "Zapisano. Zmiana obejmuje obliczenia od teraz." });
      onSaved(action === "delete" ? "" : data.code);
    } catch (err) {
      const e = err instanceof AdminError ? err : new AdminError("Nie udało się zapisać");
      setState({ kind: "error", text: e.message, errors: e.errors });
    }
  }

  const fields = [...COMMON_TOP, ...FIELDS[data.kind], ...COMMON_BOTTOM];
  return (
    <div className="flex flex-col gap-3 border-l-4 border-primary bg-white p-4">
      <div className="grid gap-3 sm:grid-cols-[1fr_180px_160px]">
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-bold">Kod</span>
          <Input
            value={data.code}
            disabled={!isNew}
            onChange={(e) => set("code", e.target.value)}
            className="font-mono"
            placeholder="np. moja_regula"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-bold">Rodzaj</span>
          <Select value={data.kind} disabled={!isNew} onChange={(e) => set("kind", e.target.value)}>
            {(Object.keys(KIND_LABEL) as RuleKind[]).map((k) => (
              <option key={k} value={k}>
                {KIND_LABEL[k]}
              </option>
            ))}
          </Select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-bold">Źródło</span>
          <Select value={data.source} onChange={(e) => set("source", e.target.value)}>
            {Object.entries(SOURCE_LABEL).map(([k, v]) => (
              <option key={k} value={k}>
                {k} – {v}
              </option>
            ))}
          </Select>
        </label>
      </div>
      {fields.map((f) => {
        const raw = data[f.key];
        const value = Array.isArray(raw) ? raw.join(", ") : ((raw as string | null) ?? "");
        const rows = f.rows ?? (f.code && value.length > 90 ? 3 : 1);
        return (
          <label key={f.key} className="flex flex-col gap-1 text-sm">
            <span className="font-bold">
              {f.label}
              {f.hint && <span className="ml-2 font-normal text-muted-foreground">{f.hint}</span>}
            </span>
            {rows > 1 ? (
              <textarea
                rows={rows}
                value={value}
                onChange={(e) => set(f.key, e.target.value)}
                className={cn(
                  "rounded-md border border-input bg-white px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-navy",
                  f.code && "font-mono text-[13px]",
                )}
              />
            ) : (
              <Input value={value} onChange={(e) => set(f.key, e.target.value)} className={cn(f.code && "font-mono text-[13px]")} />
            )}
          </label>
        );
      })}
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-bold">Powód zmiany</span>
        <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="np. nowelizacja z 1.01.2027" />
      </label>
      {rule && (rule.uses.length > 0 || rule.used_by.length > 0 || rule.parameters.length > 0) && (
        <div className="grid gap-2 text-sm sm:grid-cols-3">
          <div>
            <b>Korzysta z reguł:</b>
            <div className="mt-1 flex flex-wrap gap-1">{rule.uses.map((c) => <Chip key={c} code={c} onOpen={onOpen} />)}</div>
          </div>
          <div>
            <b>Korzystają z niej:</b>
            <div className="mt-1 flex flex-wrap gap-1">{rule.used_by.map((c) => <Chip key={c} code={c} onOpen={onOpen} />)}</div>
          </div>
          <div>
            <b>Parametry i dane:</b>
            <div className="mt-1 flex flex-wrap gap-1 font-mono text-[12px]">
              {[...rule.parameters, ...rule.facts].map((c) => (
                <span key={c} className="rounded bg-muted px-1.5 py-0.5">{c}</span>
              ))}
            </div>
          </div>
        </div>
      )}
      {state.kind !== "idle" && state.kind !== "busy" && (
        <div role="status" className={cn("rounded-md p-3 text-sm", state.kind === "ok" ? "bg-primary/10" : "bg-destructive/10")}>
          <p className="flex items-center gap-2 font-bold">
            {state.kind === "ok" ? <Check className="size-4" /> : <AlertTriangle className="size-4" />}
            {state.text}
          </p>
          {state.errors && state.errors.length > 0 && (
            <ul className="mt-1 list-disc pl-6 font-mono text-[12px]">
              {state.errors.map((e) => (
                <li key={e}>{e}</li>
              ))}
            </ul>
          )}
        </div>
      )}
      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="outline" onClick={() => run("validate")} disabled={state.kind === "busy"}>
          Sprawdź
        </Button>
        <Button type="button" onClick={() => run("save")} disabled={state.kind === "busy" || !data.code}>
          {state.kind === "busy" && <Loader2 className="animate-spin" />} Zapisz
        </Button>
        {!isNew && (
          <Button type="button" variant="outline" onClick={() => run("toggle")}>
            {data.active ? "Wyłącz regułę" : "Włącz regułę"}
          </Button>
        )}
        {rule?.in_seed && rule.modified && (
          <Button type="button" variant="outline" onClick={() => run("reset")}>
            <RotateCcw /> Przywróć wersję ze źródeł
          </Button>
        )}
        {rule && !rule.in_seed && (
          <Button type="button" variant="outline" onClick={() => run("delete")}>
            Usuń
          </Button>
        )}
        {!isNew && (
          <Button
            type="button"
            variant="ghost"
            onClick={async () => setHistory(history ? null : await adminRuleHistory(token, data.code))}
          >
            <History /> Historia
          </Button>
        )}
        <Button type="button" variant="ghost" onClick={onCancel}>
          <X /> Zamknij
        </Button>
      </div>
      {history && (
        <ul className="text-sm">
          {history.length === 0 && <li className="text-muted-foreground">Brak zmian – wersja ze źródeł.</li>}
          {history.map((h, i) => (
            <li key={i} className="border-b border-border py-1">
              <b>{h.changed_at?.slice(0, 16).replace("T", " ")}</b> – {h.note || "zmiana"}
              <span className="block font-mono text-[12px] text-muted-foreground">
                poprzednio: {h.data.expression ?? h.data.condition ?? h.data.text_pl}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function RulesTab({ token }: { token: string }) {
  const [rules, setRules] = useState<AdminRule[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<RuleKind | "">("");
  const [source, setSource] = useState("");
  const [open, setOpen] = useState<string | null>(null);

  const load = useCallback(
    () =>
      adminRules(token)
        .then(setRules)
        .catch(() => setError("Nie udało się wczytać reguł.")),
    [token],
  );
  useEffect(() => void load(), [load]);

  const openRule = (code: string) => {
    setOpen(code);
    setQuery("");
    setKind("");
    requestAnimationFrame(() => document.getElementById(`rule-${code}`)?.scrollIntoView({ block: "start" }));
  };

  const groups = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = (rules ?? []).filter(
      (r) =>
        (!kind || r.kind === kind) &&
        (!source || r.source === source) &&
        (!q ||
          [r.code, r.title_pl, r.legal_basis, r.expression, r.condition, r.text_pl]
            .filter(Boolean)
            .some((v) => (v as string).toLowerCase().includes(q))),
    );
    const map = new Map<string, AdminRule[]>();
    for (const r of list) map.set(r.group_pl || "Inne", [...(map.get(r.group_pl || "Inne") ?? []), r]);
    return [...map.entries()];
  }, [rules, query, kind, source]);

  if (error) return <p role="alert" className="text-sm text-destructive">{error}</p>;
  if (!rules) return <Loader2 className="animate-spin text-muted-foreground" />;
  const broken = rules.filter((r) => r.errors.length > 0);
  const modified = rules.filter((r) => r.modified).length;

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm">
        <b>{rules.length}</b> reguł ze źródeł: Kodeks pracy, ustawa zasiłkowa, dwa rozporządzenia, Poradnik ZUS 2026 i
        załącznik do zadania. Każda reguła to wyrażenie – zależności między regułami silnik odczytuje sam z nazw użytych w
        wyrażeniach i liczy je we właściwej kolejności. {modified > 0 && <>Zmienionych w panelu: <b>{modified}</b>.</>}
      </p>
      {broken.length > 0 && (
        <p role="alert" className="rounded-md bg-destructive/10 p-3 text-sm">
          <AlertTriangle className="mr-1 inline size-4" /> Reguły z błędami: {broken.map((r) => r.code).join(", ")}
        </p>
      )}
      <div className="flex flex-wrap items-end gap-2">
        <label className="relative min-w-60 flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Szukaj: kod, nazwa, artykuł, fragment wyrażenia"
            className="pl-9"
            aria-label="Szukaj reguły"
          />
        </label>
        <Select value={kind} onChange={(e) => setKind(e.target.value as RuleKind | "")} className="w-44" aria-label="Rodzaj">
          <option value="">Wszystkie rodzaje</option>
          {(Object.keys(KIND_LABEL) as RuleKind[]).map((k) => (
            <option key={k} value={k}>
              {KIND_LABEL[k]}
            </option>
          ))}
        </Select>
        <Select value={source} onChange={(e) => setSource(e.target.value)} className="w-56" aria-label="Źródło">
          <option value="">Wszystkie źródła</option>
          {Object.entries(SOURCE_LABEL).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </Select>
        <Button type="button" onClick={() => setOpen("__new__")}>
          <Plus /> Nowa reguła
        </Button>
      </div>
      {open === "__new__" && (
        <RuleEditor
          token={token}
          rule={null}
          isNew
          onOpen={openRule}
          onCancel={() => setOpen(null)}
          onSaved={(code) => {
            void load();
            setOpen(code || null);
          }}
        />
      )}
      {groups.map(([group, list]) => (
        <section key={group} className="flex flex-col">
          <h2 className="border-b-2 border-primary pb-1 text-base font-bold">
            {group} <span className="font-normal text-muted-foreground">({list.length})</span>
          </h2>
          <ul>
            {list.map((r) => (
              <li key={r.code} id={`rule-${r.code}`} className="scroll-mt-4 border-b border-border">
                <button
                  type="button"
                  onClick={() => setOpen(open === r.code ? null : r.code)}
                  aria-expanded={open === r.code}
                  className={cn("grid w-full gap-x-3 py-2 text-left text-sm sm:grid-cols-[110px_1fr_220px]", !r.active && "opacity-50")}
                >
                  <span>
                    <span className={cn("rounded px-1.5 py-0.5 text-[12px] font-bold", KIND_COLOR[r.kind])}>{KIND_LABEL[r.kind]}</span>
                  </span>
                  <span className="min-w-0">
                    <span className="font-mono text-[12px] text-link">{r.code}</span>
                    {r.modified && <span className="ml-2 rounded bg-orange px-1 text-[11px] font-bold text-white">zmieniona</span>}
                    {!r.active && <span className="ml-2 rounded bg-muted px-1 text-[11px]">wyłączona</span>}
                    {r.errors.length > 0 && <AlertTriangle className="ml-2 inline size-4 text-destructive" />}
                    <span className="block font-bold">{r.title_pl.replace(/\{[^}]+\}/g, "…")}</span>
                    <span className="block truncate font-mono text-[12px] text-muted-foreground">
                      {r.kind === "okres" ? `od ${r.start} · dni: ${r.expression}` : (r.expression ?? r.condition ?? r.text_pl)}
                    </span>
                  </span>
                  <span className="text-[12px] text-muted-foreground">
                    <b className="text-foreground">{SOURCE_LABEL[r.source] ?? r.source}</b>
                    <span className="block">{r.legal_basis}</span>
                  </span>
                </button>
                {open === r.code && (
                  <RuleEditor
                    key={r.code + r.modified + (r.expression ?? "")}
                    token={token}
                    rule={r}
                    isNew={false}
                    onOpen={openRule}
                    onCancel={() => setOpen(null)}
                    onSaved={(code) => {
                      void load();
                      setOpen(code || null);
                    }}
                  />
                )}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
