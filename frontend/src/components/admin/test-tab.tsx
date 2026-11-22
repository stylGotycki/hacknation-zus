"use client";

import { Loader2, Play } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/form-controls";
import { AdminError, adminTestRules, api, type FamilyProfile, type RuleTestResult } from "@/lib/api";
import { formatDate, formatPln } from "@/lib/format";

type Scenario = { id: string; title_pl: string; profile: FamilyProfile };

const STATUS: Record<string, string> = {
  eligible: "przysługuje",
  conditional: "warunkowo",
  not_eligible: "nie przysługuje",
  info: "informacja",
};

/** Runs all rules for a persona or a pasted profile and shows every computed value. */
export function TestTab({ token }: { token: string }) {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [json, setJson] = useState("");
  const [out, setOut] = useState<RuleTestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    api<Scenario[]>("/scenarios").then((list) => {
      setScenarios(list);
      if (list[0]) setJson(JSON.stringify(list[0].profile, null, 2));
    });
  }, []);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      setOut(await adminTestRules(token, JSON.parse(json)));
    } catch (err) {
      setOut(null);
      setError(err instanceof SyntaxError ? "Profil nie jest poprawnym JSON-em." : err instanceof AdminError ? err.message : "Błąd");
    } finally {
      setBusy(false);
    }
  }

  const values = useMemo(
    () =>
      Object.entries(out?.values ?? {}).filter(([k, v]) => !filter || k.includes(filter) || JSON.stringify(v).includes(filter)),
    [out, filter],
  );

  return (
    <div className="grid gap-6 text-sm lg:grid-cols-[minmax(0,420px)_1fr]">
      <div className="flex flex-col gap-2">
        <label className="flex flex-col gap-1">
          <span className="font-bold">Persona</span>
          <Select onChange={(e) => setJson(JSON.stringify(scenarios.find((s) => s.id === e.target.value)?.profile, null, 2))}>
            {scenarios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.id} – {s.title_pl}
              </option>
            ))}
          </Select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="font-bold">Profil rodziny (JSON)</span>
          <textarea
            value={json}
            onChange={(e) => setJson(e.target.value)}
            rows={22}
            spellCheck={false}
            className="rounded-md border border-input bg-white p-2 font-mono text-[12px]"
          />
        </label>
        <Button type="button" onClick={run} disabled={busy}>
          {busy ? <Loader2 className="animate-spin" /> : <Play />} Uruchom reguły
        </Button>
        {error && <p role="alert" className="text-destructive">{error}</p>}
      </div>
      <div className="flex min-w-0 flex-col gap-4">
        {!out && <p className="text-muted-foreground">Wybierz personę albo wklej profil i uruchom reguły.</p>}
        {out && !out.ok && (
          <p role="alert" className="rounded-md bg-destructive/10 p-3">
            <b>Plan odrzucony (walidacja):</b> {out.violation}
          </p>
        )}
        {out?.result && (
          <>
            <section>
              <h2 className="border-b-2 border-primary pb-1 text-base font-bold">Świadczenia</h2>
              <ul>
                {out.result.benefits.map((b) => (
                  <li key={b.code} className="border-b border-border py-1">
                    <b>{b.title_pl}</b> – {STATUS[b.status]} {b.total_gross != null && <>· {formatPln(b.total_gross)}</>}
                    <span className="block text-muted-foreground">{b.summary_pl}</span>
                  </li>
                ))}
              </ul>
            </section>
            <section>
              <h2 className="border-b-2 border-primary pb-1 text-base font-bold">Okresy</h2>
              <table className="w-full">
                <tbody>
                  {out.result.timeline.map((p) => (
                    <tr key={p.id} className="border-b border-border">
                      <td className="py-1 pr-2 font-mono text-[12px]">{p.rule}</td>
                      <td className="py-1 pr-2">{p.label_pl}</td>
                      <td className="whitespace-nowrap py-1 pr-2">
                        {formatDate(p.start)} – {formatDate(p.end)}
                      </td>
                      <td className="py-1 pr-2">{p.days} dni</td>
                      <td className="py-1">{p.rate != null ? `${(p.rate * 100).toLocaleString("pl-PL")}%` : "–"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
            <section>
              <h2 className="border-b-2 border-primary pb-1 text-base font-bold">
                Terminy, ryzyka ({out.result.deadlines.length} / {out.result.risks.length})
              </h2>
              <ul className="columns-1 md:columns-2">
                {out.result.deadlines.map((d) => (
                  <li key={d.code}>
                    {formatDate(d.due)} – {d.title_pl}
                  </li>
                ))}
                {out.result.risks.map((r) => (
                  <li key={r.code}>
                    [{r.severity}] {r.title_pl}
                  </li>
                ))}
              </ul>
            </section>
          </>
        )}
        {out?.ok && (
          <section>
            <h2 className="border-b-2 border-primary pb-1 text-base font-bold">Wartości wszystkich reguł ({values.length})</h2>
            {Object.keys(out.errors).length > 0 && (
              <ul className="my-2 rounded-md bg-destructive/10 p-2 font-mono text-[12px]">
                {Object.entries(out.errors).map(([k, v]) => (
                  <li key={k}>
                    {k}: {v}
                  </li>
                ))}
              </ul>
            )}
            <Input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filtruj" className="my-2 max-w-xs" />
            <table className="w-full">
              <tbody>
                {values.map(([k, v]) => (
                  <tr key={k} className="border-b border-border align-top">
                    <td className="py-0.5 pr-3 font-mono text-[12px]">{k}</td>
                    <td className="break-all py-0.5 font-mono text-[12px] text-muted-foreground">{JSON.stringify(v)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}
      </div>
    </div>
  );
}
