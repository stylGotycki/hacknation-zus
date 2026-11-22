"use client";

import { ArrowDown, ArrowUp, Loader2, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Input } from "@/components/ui/form-controls";
import { adminRuleDictionary, adminRules, type AdminRule, type RuleDictionary } from "@/lib/api";

import { KIND_LABEL } from "./rules-tab";

/** Data dictionary: everything an expression can read – facts, functions, parameters, rule kinds. */
export function DictionaryTab({ token }: { token: string }) {
  const [dict, setDict] = useState<RuleDictionary | null>(null);
  const [query, setQuery] = useState("");
  useEffect(() => void adminRuleDictionary(token).then(setDict), [token]);
  if (!dict) return <Loader2 className="animate-spin text-muted-foreground" />;
  const q = query.toLowerCase();
  const match = (...v: string[]) => !q || v.some((x) => x.toLowerCase().includes(q));

  return (
    <div className="flex flex-col gap-6 text-sm">
      <label className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Szukaj w słowniku" className="pl-9" />
      </label>
      <section>
        <h2 className="border-b-2 border-primary pb-1 text-base font-bold">Język wyrażeń</h2>
        <p className="mt-2">
          Wyrażenia piszesz jak proste formuły: <code>+ - * /</code>, porównania <code>== != &lt; &lt;= &gt; &gt;=</code>,{" "}
          <code>and or not</code>, <code>in [&apos;a&apos;, &apos;b&apos;]</code>, teksty w apostrofach. Brak danych
          (puste pole) nie psuje obliczeń – wynik też jest pusty, a porównanie fałszywe. W tekstach (tytuł, opis) wstaw
          wartość w nawiasach klamrowych: <code>{"{mama_podstawa}"}</code>. Okres czytasz przez{" "}
          <code>kod.start, kod.koniec, kod.dni, kod.aktywny</code>.
        </p>
      </section>
      <section>
        <h2 className="border-b-2 border-primary pb-1 text-base font-bold">Rodzaje reguł</h2>
        <dl className="mt-2 grid gap-x-4 gap-y-1 sm:grid-cols-[140px_1fr]">
          {Object.entries(dict.kinds).map(([k, v]) => (
            <div key={k} className="contents">
              <dt className="font-bold">{KIND_LABEL[k as keyof typeof KIND_LABEL]}</dt>
              <dd>{v}</dd>
            </div>
          ))}
        </dl>
      </section>
      <section>
        <h2 className="border-b-2 border-primary pb-1 text-base font-bold">Dane o rodzinie (fakty)</h2>
        <table className="mt-1 w-full">
          <tbody>
            {dict.facts
              .filter((f) => match(f.path, f.description))
              .map((f) => (
                <tr key={f.path} className="border-b border-border align-top">
                  <td className="py-1 pr-3 font-mono text-[12px]">{f.path}</td>
                  <td className="w-20 py-1 pr-3 text-muted-foreground">{f.type}</td>
                  <td className="py-1">{f.description}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </section>
      <section>
        <h2 className="border-b-2 border-primary pb-1 text-base font-bold">Funkcje</h2>
        <table className="mt-1 w-full">
          <tbody>
            {dict.functions
              .filter((f) => match(f.name, f.description))
              .map((f) => (
                <tr key={f.name} className="border-b border-border">
                  <td className="w-40 py-1 pr-3 font-mono text-[12px]">{f.name}()</td>
                  <td className="py-1">{f.description}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </section>
      <section>
        <h2 className="border-b-2 border-primary pb-1 text-base font-bold">
          Parametry prawne – <code>param(&apos;klucz&apos;)</code>, <code>tabela(&apos;klucz&apos;, &apos;pole&apos;)</code>
        </h2>
        <table className="mt-1 w-full">
          <tbody>
            {dict.parameters
              .filter((p) => match(p.key, p.label))
              .map((p) => (
                <tr key={p.key} className="border-b border-border align-top">
                  <td className="py-1 pr-3 font-mono text-[12px]">{p.key}</td>
                  <td className="py-1 pr-3">{p.label}</td>
                  <td className="py-1 font-mono text-[12px] text-muted-foreground">{JSON.stringify(p.value)}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

/** Dependencies of one rule: what it reads (up) and what reads it (down), two levels each way. */
export function DependenciesTab({ token }: { token: string }) {
  const [rules, setRules] = useState<AdminRule[] | null>(null);
  const [code, setCode] = useState("mama_uprawniona");
  useEffect(() => void adminRules(token).then(setRules), [token]);
  const byCode = useMemo(() => new Map((rules ?? []).map((r) => [r.code, r])), [rules]);
  if (!rules) return <Loader2 className="animate-spin text-muted-foreground" />;
  const rule = byCode.get(code);

  const Level = ({ codes, dir, depth }: { codes: string[]; dir: "uses" | "used_by"; depth: number }) => (
    <ul className="ml-4 border-l-2 border-band-border pl-3">
      {codes.map((c) => {
        const r = byCode.get(c);
        return (
          <li key={c} className="py-0.5">
            <button type="button" className="font-mono text-[12px] text-link hover:underline" onClick={() => setCode(c)}>
              {c}
            </button>{" "}
            <span className="text-muted-foreground">{r?.title_pl.replace(/\{[^}]+\}/g, "…")}</span>
            {depth < 2 && r && r[dir].length > 0 && <Level codes={r[dir]} dir={dir} depth={depth + 1} />}
          </li>
        );
      })}
    </ul>
  );

  return (
    <div className="flex flex-col gap-4 text-sm">
      <p>
        Silnik sam ustala kolejność liczenia z nazw użytych w wyrażeniach. Zmiana jednej reguły wpływa na wszystkie reguły
        poniżej. Cykl zależności jest blokowany przy zapisie.
      </p>
      <label className="flex max-w-md flex-col gap-1">
        <span className="font-bold">Reguła</span>
        <Input list="rule-codes" value={code} onChange={(e) => setCode(e.target.value)} className="font-mono" />
        <datalist id="rule-codes">
          {rules.map((r) => (
            <option key={r.code} value={r.code}>
              {r.title_pl}
            </option>
          ))}
        </datalist>
      </label>
      {rule ? (
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <h3 className="flex items-center gap-1 font-bold">
              <ArrowUp className="size-4" /> Korzysta z ({rule.uses.length})
            </h3>
            {rule.facts.length > 0 && (
              <p className="ml-4 mt-1 text-muted-foreground">
                dane: <span className="font-mono text-[12px]">{rule.facts.join(", ")}</span>
                {rule.parameters.length > 0 && (
                  <>
                    {" "}
                    · parametry: <span className="font-mono text-[12px]">{rule.parameters.join(", ")}</span>
                  </>
                )}
              </p>
            )}
            <Level codes={rule.uses} dir="uses" depth={1} />
          </div>
          <div>
            <h3 className="flex items-center gap-1 font-bold">
              <ArrowDown className="size-4" /> Wpływa na ({rule.used_by.length})
            </h3>
            <Level codes={rule.used_by} dir="used_by" depth={1} />
          </div>
        </div>
      ) : (
        <p className="text-muted-foreground">Nie ma reguły o takim kodzie.</p>
      )}
    </div>
  );
}
