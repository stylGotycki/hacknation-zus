import { AlertTriangle, Info, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { VerticalTimeline } from "@/components/timeline/vertical-timeline";
import type { BenefitResult, BenefitStatus, Deadline, EvaluationResult, Person, Risk } from "@/lib/api";
import { formatDate, formatDaysLeft, formatPercent, formatPln, formatWeeks } from "@/lib/format";
import { fatherHasAllowance } from "@/lib/result-view";
import { cn } from "@/lib/utils";

const STATUS_LABEL: Record<BenefitStatus, string> = {
  eligible: "Przysługuje",
  conditional: "Pod warunkiem",
  not_eligible: "Nie przysługuje",
  info: "Informacja",
};

const STATUS_CLASS: Record<BenefitStatus, string> = {
  eligible: "bg-primary text-primary-foreground border-transparent",
  conditional: "bg-amber-100 text-amber-900 border-amber-200",
  not_eligible: "bg-destructive/10 text-destructive border-destructive/20",
  info: "bg-secondary text-secondary-foreground border-transparent",
};

const PERSON_LABEL: Record<Person, string> = { mother: "Mama", father: "Tata", family: "Rodzina" };

const PAYER_LABEL = {
  employer: "Wypłaca pracodawca",
  zus: "Wypłaca ZUS",
} as const;

const DEADLINE_CHIP = {
  open: "bg-muted text-navy",
  soon: "bg-amber-100 text-amber-900",
  overdue: "bg-destructive/10 text-destructive",
} as const;

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-xl font-semibold tracking-tight sm:text-2xl">{value}</p>
      {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

function BenefitCard({ benefit }: { benefit: BenefitResult }) {
  return (
    <Card className="gap-3">
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="font-normal">
            {PERSON_LABEL[benefit.person]}
          </Badge>
          <Badge className={cn("border", STATUS_CLASS[benefit.status])}>{STATUS_LABEL[benefit.status]}</Badge>
          {benefit.payer && <Badge variant="outline" className="font-normal">{PAYER_LABEL[benefit.payer]}</Badge>}
        </div>
        <CardTitle className="text-base">{benefit.title_pl}</CardTitle>
        <CardDescription>{benefit.summary_pl}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 text-sm">
        {benefit.start && benefit.end && (
          <p>
            <span className="text-muted-foreground">Okres: </span>
            {formatDate(benefit.start)} – {formatDate(benefit.end)} ({formatWeeks(benefit.weeks)})
          </p>
        )}
        {benefit.monthly_gross !== null && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <Stat label="Stawka" value={formatPercent(benefit.rate)} />
            <Stat label="Miesięcznie brutto" value={formatPln(benefit.monthly_gross)} />
            {benefit.total_gross !== null && (
              <Stat label="Łącznie brutto" value={formatPln(benefit.total_gross)} />
            )}
          </div>
        )}
        {benefit.apply_to_pl && (
          <p>
            <span className="font-medium">Gdzie złożyć: </span>
            {benefit.apply_to_pl}
          </p>
        )}
        {benefit.deadline && benefit.days_left !== null && (
          <p className="flex flex-wrap items-center gap-2 rounded-md bg-muted p-2">
            <span
              className={cn(
                "rounded-md px-2 py-0.5 text-xs font-medium",
                DEADLINE_CHIP[benefit.days_left < 0 ? "overdue" : benefit.days_left <= 14 ? "soon" : "open"],
              )}
            >
              {formatDaysLeft(benefit.days_left)}
            </span>
            <span>
              <span className="font-medium">Wniosek do {formatDate(benefit.deadline)}. </span>
              {benefit.deadline_note_pl}
            </span>
          </p>
        )}
        {(benefit.reasons_pl.length > 0 || benefit.documents_pl.length > 0 || benefit.legal_basis.length > 0) && (
          <details>
            <summary className="cursor-pointer text-primary">Szczegóły, dokumenty i podstawa prawna</summary>
            <div className="mt-3 flex flex-col gap-3">
              {benefit.reasons_pl.length > 0 && (
                <ul className="list-disc space-y-1 pl-5">
                  {benefit.reasons_pl.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              )}
              {benefit.documents_pl.length > 0 && (
                <div>
                  <p className="font-medium">Dokumenty</p>
                  <ul className="list-disc space-y-1 pl-5">
                    {benefit.documents_pl.map((doc) => (
                      <li key={doc}>{doc}</li>
                    ))}
                  </ul>
                </div>
              )}
              {benefit.legal_basis.length > 0 && (
                <p className="text-xs text-muted-foreground">Podstawa: {benefit.legal_basis.join("; ")}</p>
              )}
            </div>
          </details>
        )}
      </CardContent>
    </Card>
  );
}

function DeadlineList({ deadlines }: { deadlines: Deadline[] }) {
  const apply = deadlines.filter((d) => d.kind === "apply");
  if (apply.length === 0) return null;
  return (
    <div className="flex flex-col gap-4">
      <h3 className="text-lg font-semibold">Ile czasu na wnioski</h3>
      <ul className="flex flex-col gap-3">
        {apply.map((d) => (
          <li key={d.code} className="flex flex-col gap-1 rounded-xl border bg-card p-4 text-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-medium">
                {d.person !== "family" && `${PERSON_LABEL[d.person]}: `}
                {d.title_pl}
              </p>
              <span className={cn("rounded-md px-2 py-0.5 text-xs font-medium", DEADLINE_CHIP[d.status])}>
                {formatDaysLeft(d.days_left)}
              </span>
            </div>
            <p className="text-muted-foreground">Termin: {formatDate(d.due)}</p>
            <p className="text-muted-foreground">{d.note_pl}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

const RISK_STYLE = {
  high: { icon: ShieldAlert, box: "border-destructive/40 bg-destructive/5", label: "Ważne" },
  medium: { icon: AlertTriangle, box: "border-amber-300 bg-amber-50", label: "Uwaga" },
  info: { icon: Info, box: "bg-card", label: "Warto wiedzieć" },
} as const;

function RiskItem({ risk }: { risk: Risk }) {
  const style = RISK_STYLE[risk.severity];
  const Icon = style.icon;
  return (
    <li className={cn("flex gap-3 rounded-xl border p-4 text-sm", style.box)}>
      <Icon className="mt-0.5 size-5 shrink-0" />
      <div className="flex flex-col gap-1">
        <p className="font-medium">{risk.title_pl}</p>
        <p className="text-muted-foreground">{risk.text_pl}</p>
        {risk.legal_basis && <p className="text-xs text-muted-foreground">Podstawa: {risk.legal_basis}</p>}
      </div>
    </li>
  );
}

export function CalculatorResults({ result }: { result: EvaluationResult }) {
  const showFather = fatherHasAllowance(result);
  const t = result.totals;
  const hasAmounts = t.family_gross > 0;
  const ordered = [...result.benefits].sort((a, b) => {
    const rank: Record<BenefitStatus, number> = { eligible: 0, conditional: 1, info: 2, not_eligible: 0 };
    return rank[a.status] - rank[b.status];
  });

  return (
    <section aria-label="Wynik" className="flex flex-col gap-8">
      <div className="flex flex-col gap-3">
        <h2 className="text-xl font-semibold tracking-tight sm:text-2xl">Wynik</h2>
        <p className="text-sm text-muted-foreground">
          {result.event_is_estimate ? "Przewidywana data porodu" : "Data zdarzenia"}: {formatDate(result.event_date)}.
          Parametry prawne na dzień {formatDate(result.params_date)}.
        </p>
        {hasAmounts ? (
          <div className={cn("grid grid-cols-2 gap-3", showFather ? "lg:grid-cols-3" : "lg:grid-cols-2")}>
            <Stat label="Zasiłki razem (brutto)" value={formatPln(t.family_gross)} />
            {t.mother_gross > 0 && <Stat label="Mama (brutto)" value={formatPln(t.mother_gross)} />}
            {showFather && <Stat label="Tata (brutto)" value={formatPln(t.father_gross)} />}
          </div>
        ) : (
          <p className="rounded-xl border border-dashed p-4 text-sm">
            Nie ma kwot do pokazania – sprawdź poniżej, dlaczego zasiłek nie przysługuje lub jakich danych brakuje.
          </p>
        )}
      </div>

      {result.averaged_rate && (
        <Card>
          <CardHeader>
            <CardTitle>Stawki 100% i 70% czy stała 81,5%?</CardTitle>
            <CardDescription>
              Wniosek najpóźniej do {formatDate(result.averaged_rate.deadline)}
              {result.averaged_rate.still_possible ? "" : " (termin minął)"}.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 text-sm">
            {result.averaged_rate.standard_total !== null && (
              <div className="grid grid-cols-2 gap-3">
                <Stat label="100% + 70%" value={formatPln(result.averaged_rate.standard_total)} />
                <Stat label="Stała 81,5%" value={formatPln(result.averaged_rate.averaged_total)} />
              </div>
            )}
            <p className="text-muted-foreground">{result.averaged_rate.note_pl}</p>
          </CardContent>
        </Card>
      )}

      <DeadlineList deadlines={result.deadlines} />

      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold">Świadczenia</h3>
        {ordered.map((benefit) => (
          <BenefitCard key={benefit.code} benefit={benefit} />
        ))}
      </div>

      {result.timeline.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Oś czasu</CardTitle>
            <CardDescription>
              Każdy punkt to zdarzenie: start i koniec urlopu oraz termin do złożenia wniosku. Linie to
              „gałęzie” mamy i taty, jak w historii zmian.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <VerticalTimeline result={result} />
          </CardContent>
        </Card>
      )}

      {result.risks.length > 0 && (
        <div className="flex flex-col gap-4">
          <h3 className="text-lg font-semibold">Ryzyka i na co uważać</h3>
          <ul className="flex flex-col gap-3">
            {result.risks.map((risk) => (
              <RiskItem key={risk.code} risk={risk} />
            ))}
          </ul>
        </div>
      )}

      {result.info_pl.length > 0 && (
        <div className="flex flex-col gap-2 text-sm">
          <h3 className="text-lg font-semibold">Warto wiedzieć</h3>
          <ul className="list-disc space-y-1 pl-5">
            {result.info_pl.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
        <p className="mb-2 font-medium text-foreground">Założenia obliczeń (kwoty brutto)</p>
        <ul className="list-disc space-y-1 pl-5">
          {result.assumptions_pl.map((assumption) => (
            <li key={assumption}>{assumption}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
