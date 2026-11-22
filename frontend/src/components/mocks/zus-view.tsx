"use client";

import { Download, Loader2, Send, Sparkles } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { CalculatorResults } from "@/components/calculator/calculator-results";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input } from "@/components/ui/form-controls";
import {
  evaluateFamily,
  pueQuestion,
  zusDebt,
  zusEzla,
  zusInsurance,
  zusProfile,
  type Citizen,
  type DebtCertificate,
  type EvaluationResult,
  type EzlaRecord,
  type InsuranceData,
  type PueAnswer,
} from "@/lib/api";
import { formatDate, formatPln } from "@/lib/format";
import { saveLastForm, saveLastProfile, saveLastResult } from "@/lib/last-result";
import { PUBLIC_PATHS } from "@/lib/routes";
import { loadCitizen } from "@/lib/session";
import { cn } from "@/lib/utils";

const BAD = "bg-destructive/10 text-destructive border-destructive/20";

type Tab = "insurance" | "debt" | "ezla" | "pue";
const TABS: { id: Tab; label: string }[] = [
  { id: "insurance", label: "Ubezpieczenie" },
  { id: "debt", label: "Zadłużenie" },
  { id: "ezla", label: "e-ZLA" },
  { id: "pue", label: "PUE ZUS" },
];

type Loaded = { insurance: InsuranceData; debt: DebtCertificate; ezla: EzlaRecord[] };

function Simulation({ note }: { note: string }) {
  return <p className="text-xs text-muted-foreground">{note}</p>;
}

export function ZusView() {
  const [citizen, setCitizen] = useState<Citizen | null | undefined>(undefined);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [tab, setTab] = useState<Tab>("insurance");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [calculating, setCalculating] = useState(false);
  const [subject, setSubject] = useState("");
  const [text, setText] = useState("");
  const [answer, setAnswer] = useState<PueAnswer | null>(null);
  const [asking, setAsking] = useState(false);

  useEffect(() => setCitizen(loadCitizen()), []);

  if (citizen === undefined) return null;
  if (citizen === null) {
    return (
      <div className="flex flex-col items-start gap-4 rounded-xl border border-dashed p-6">
        <p>Zaloguj się przez mObywatel (symulacja), aby pobrać dane z ZUS.</p>
        <Button asChild>
          <Link href={PUBLIC_PATHS.login}>Zaloguj przez mObywatel</Link>
        </Button>
      </div>
    );
  }

  async function download() {
    if (!citizen) return;
    setLoading(true);
    setError(null);
    try {
      await new Promise((resolve) => setTimeout(resolve, 700)); // imitates the request to ZUS
      const [insurance, debt, ezla] = await Promise.all([
        zusInsurance(citizen.id),
        zusDebt(citizen.id),
        zusEzla(citizen.id),
      ]);
      setLoaded({ insurance, debt, ezla: ezla.records });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nie udało się pobrać danych.");
    } finally {
      setLoading(false);
    }
  }

  async function calculate() {
    if (!citizen) return;
    setCalculating(true);
    setError(null);
    try {
      const profile = await zusProfile(citizen.id);
      const evaluated = await evaluateFamily(profile);
      saveLastResult(evaluated);
      saveLastProfile(profile);
      saveLastForm(null);
      setResult(evaluated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nie udało się policzyć uprawnień.");
    } finally {
      setCalculating(false);
    }
  }

  async function ask(e: React.FormEvent) {
    e.preventDefault();
    if (!citizen) return;
    setAsking(true);
    try {
      setAnswer(await pueQuestion(citizen.id, subject, text));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nie udało się wysłać pytania.");
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-muted/40 p-4">
        <div>
          <p className="font-medium">
            {citizen.first_name} {citizen.last_name}
          </p>
          <p className="text-sm text-muted-foreground">
            PESEL {citizen.pesel_masked} · {citizen.scenario_title_pl}
          </p>
        </div>
        <Button onClick={download} disabled={loading}>
          {loading ? <Loader2 className="animate-spin" /> : <Download />}
          {loaded ? "Pobierz ponownie" : "Pobierz dane z ZUS"}
        </Button>
      </div>

      {error && (
        <div role="alert" className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm">
          {error}
        </div>
      )}

      {loaded && (
        <>
          <div role="tablist" className="flex flex-wrap gap-2">
            {TABS.map((t) => (
              <button
                key={t.id}
                role="tab"
                aria-selected={tab === t.id}
                onClick={() => setTab(t.id)}
                className={cn(
                  "rounded-full border px-3 py-1 text-sm transition-colors",
                  tab === t.id ? "border-primary bg-primary text-primary-foreground" : "hover:bg-muted",
                )}
              >
                {t.label}
              </button>
            ))}
          </div>

          {tab === "insurance" && (
            <Card>
              <CardHeader>
                <CardTitle>Poświadczenie ubezpieczenia chorobowego</CardTitle>
                <CardDescription>
                  Stan na dzień zdarzenia: {formatDate(loaded.insurance.event_date)}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                <Badge className={cn("w-fit", !loaded.insurance.insured_on_event && BAD)}>
                  {loaded.insurance.summary_pl}
                </Badge>
                {loaded.insurance.periods.length === 0 && (
                  <p className="text-sm">Brak zgłoszonych tytułów do ubezpieczenia chorobowego.</p>
                )}
                {loaded.insurance.periods.map((p) => (
                  <div key={p.from} className="rounded-lg border p-3 text-sm">
                    <p className="font-medium">{p.title_pl}</p>
                    <p>
                      {formatDate(p.from)} – {p.to ? formatDate(p.to) : "trwa"} ·{" "}
                      {p.sickness_insurance === "voluntary" ? "ubezpieczenie dobrowolne" : "ubezpieczenie obowiązkowe"}
                    </p>
                    <p className="text-muted-foreground">{p.payer_pl}</p>
                  </div>
                ))}
                {loaded.insurance.bases.length > 0 && (
                  <div>
                    <p className="mb-2 text-sm font-medium">Podstawa wymiaru składek (ostatnie miesiące)</p>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b text-left text-xs text-muted-foreground">
                            <th className="py-1 pr-4">Miesiąc</th>
                            <th className="py-1">Podstawa</th>
                          </tr>
                        </thead>
                        <tbody>
                          {loaded.insurance.bases.map((b) => (
                            <tr key={b.month} className="border-b last:border-0">
                              <td className="py-1 pr-4">{b.month}</td>
                              <td className="py-1">{formatPln(b.base)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
                <Simulation note={loaded.insurance.note_pl} />
              </CardContent>
            </Card>
          )}

          {tab === "debt" && (
            <Card>
              <CardHeader>
                <CardTitle>Zaświadczenie o stanie zadłużenia</CardTitle>
                <CardDescription>
                  Nr {loaded.debt.number} · na dzień {formatDate(loaded.debt.as_of)}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-3 text-sm">
                <Badge className={cn("w-fit", loaded.debt.blocks_benefit && BAD)}>
                  {loaded.debt.blocks_benefit ? "Zadłużenie wstrzymuje zasiłek" : "Zadłużenie nie blokuje zasiłku"}
                </Badge>
                <p>{loaded.debt.summary_pl}</p>
                <p className="text-muted-foreground">
                  Kwota zadłużenia: {formatPln(loaded.debt.debt_amount)} · próg (1% płacy minimalnej):{" "}
                  {formatPln(loaded.debt.threshold)}
                  {loaded.debt.in_installments && " · spłata w ratach"}
                </p>
                <Simulation note={loaded.debt.note_pl} />
              </CardContent>
            </Card>
          )}

          {tab === "ezla" && (
            <Card>
              <CardHeader>
                <CardTitle>Zaświadczenia lekarskie e-ZLA</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-3 text-sm">
                {loaded.ezla.length === 0 && <p>Brak wystawionych zaświadczeń e-ZLA.</p>}
                {loaded.ezla.map((z) => (
                  <div key={z.number} className="rounded-lg border p-3">
                    <p className="font-medium">
                      {z.number} · kod „{z.code}”
                    </p>
                    <p>{z.code_description_pl}</p>
                    <p>
                      {formatDate(z.from)} – {formatDate(z.to)} ({z.days} dni)
                    </p>
                    <p className="text-muted-foreground">
                      {z.issued_by_pl} · {z.payer_pl}
                    </p>
                  </div>
                ))}
                <Simulation note="Symulacja – dane przykładowe, nie pochodzą z ZUS." />
              </CardContent>
            </Card>
          )}

          {tab === "pue" && (
            <Card>
              <CardHeader>
                <CardTitle>Pytanie do PUE / eZUS</CardTitle>
                <CardDescription>Zadaj pytanie konsultantowi w razie wątpliwości co do danych.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={ask} className="flex flex-col gap-4">
                  <Field label="Temat">
                    <Input value={subject} onChange={(e) => setSubject(e.target.value)} required />
                  </Field>
                  <Field label="Treść pytania">
                    <textarea
                      className="min-h-24 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
                      value={text}
                      onChange={(e) => setText(e.target.value)}
                      required
                    />
                  </Field>
                  <Button type="submit" disabled={asking} className="w-fit">
                    {asking ? <Loader2 className="animate-spin" /> : <Send />}
                    Wyślij pytanie
                  </Button>
                </form>
                {answer && (
                  <div className="mt-4 rounded-lg border bg-secondary p-4 text-sm">
                    <p className="text-xs text-muted-foreground">
                      Zgłoszenie {answer.ticket} · {answer.received_at.slice(0, 10)}
                    </p>
                    <p className="mt-1">{answer.answer_pl}</p>
                    <p className="mt-2 text-xs text-muted-foreground">{answer.note_pl}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          <div className="flex flex-col items-start gap-3">
            <Button onClick={calculate} disabled={calculating} size="lg">
              {calculating ? <Loader2 className="animate-spin" /> : <Sparkles />}
              Policz uprawnienia z danych ZUS
            </Button>
          </div>
        </>
      )}

      {result && (
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap gap-2">
            <Button asChild variant="outline">
              <Link href={PUBLIC_PATHS.timeline}>Zobacz oś czasu</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href={PUBLIC_PATHS.applications}>Przejdź do wniosków</Link>
            </Button>
          </div>
          <CalculatorResults result={result} />
        </div>
      )}
    </div>
  );
}
