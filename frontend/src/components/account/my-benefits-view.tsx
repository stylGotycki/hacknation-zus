"use client";

import { ChevronRight, CircleAlert, Clock, Info } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import {
  type ApplicationRecord,
  type EvaluationResult,
  listApplications,
} from "@/lib/api";
import { formatDate, formatPln, formatWeeks } from "@/lib/format";
import { loadLastResult } from "@/lib/last-result";
import {
  type PeriodRow,
  type PeriodState,
  WHO,
  paymentSummary,
  periodRows,
  todayIso,
  whatNow,
} from "@/lib/my-benefits";
import { PUBLIC_PATHS } from "@/lib/routes";
import { ensureRestored, loadCitizen } from "@/lib/session";
import { cn } from "@/lib/utils";

const STATE: Record<PeriodState, { label: string; cls: string }> = {
  done: { label: "Wykorzystany", cls: "bg-muted text-foreground" },
  now: { label: "Trwa", cls: "bg-primary text-white" },
  planned: { label: "Zaplanowany", cls: "bg-info/10 text-info" },
  unpaid: { label: "Bez zasiłku", cls: "bg-amber-100 text-amber-900" },
};

const TONE = {
  late: { Icon: CircleAlert, cls: "border-amber-500 bg-amber-50" },
  soon: { Icon: Clock, cls: "border-destructive bg-destructive/5" },
  info: { Icon: Info, cls: "border-navy bg-muted" },
} as const;

/** The parent's account at a glance: what is used, what is left and until when, plus what to do now. */
export function MyBenefitsView() {
  const [result, setResult] = useState<EvaluationResult | null | undefined>(
    undefined,
  );
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    void ensureRestored().then(() => {
      setLoggedIn(loadCitizen() !== null);
      setResult(loadLastResult());
      listApplications()
        .then(setApplications)
        .catch(() => setApplications([]));
    });
  }, []);

  if (result === undefined) return null;
  if (result === null) {
    return (
      <div className="flex flex-col items-start gap-3 border-l-[5px] border-primary bg-muted p-5">
        <p>
          Ta strona powstaje z wyliczenia. Najpierw sprawdź uprawnienia w
          kalkulatorze albo zaloguj się i pobierz dane z ZUS.
        </p>
        <Link
          href={PUBLIC_PATHS.calculator}
          className="inline-flex items-center gap-1 font-bold text-link hover:underline"
        >
          Przejdź do kalkulatora <ChevronRight className="size-4" />
        </Link>
      </div>
    );
  }

  const today = todayIso();
  const rows = periodRows(result, today);
  const money = paymentSummary(result, today);
  const todos = whatNow(result, applications, today, loggedIn);
  const grant = result.benefits.find((b) => b.code === "becikowe");
  const people = (["mother", "father"] as const).filter((p) =>
    rows.some((r) => r.period.person === p),
  );

  return (
    <div className="flex flex-col gap-10">
      {!loggedIn && (
        <p className="border-l-[5px] border-navy bg-muted p-3 text-sm">
          Widzisz wyliczenie z tej przeglądarki.{" "}
          <Link
            className="font-bold text-primary underline"
            href={PUBLIC_PATHS.login}
          >
            Zaloguj się przez mObywatel
          </Link>
          , żeby zapisać je na koncie i śledzić swoje wnioski.
        </p>
      )}

      <section aria-labelledby="co-teraz" className="flex flex-col gap-3">
        <h2 id="co-teraz" className="text-xl font-semibold">
          Co teraz
        </h2>
        {todos.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Na dziś nic nie wymaga Twojej uwagi.
          </p>
        ) : (
          <ul className="flex flex-col gap-2">
            {todos.map((t) => {
              const { Icon, cls } = TONE[t.tone];
              return (
                <li
                  key={t.title}
                  className={cn("flex gap-3 border-l-[5px] p-3", cls)}
                >
                  <Icon aria-hidden className="mt-0.5 size-5 shrink-0" />
                  <div className="flex flex-col gap-1 text-sm">
                    <p className="font-bold">{t.title}</p>
                    <p>{t.text}</p>
                    {t.href && (
                      <Link
                        href={t.href}
                        className="inline-flex w-fit items-center gap-1 font-bold text-link hover:underline"
                      >
                        Przejdź do wniosków <ChevronRight className="size-4" />
                      </Link>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section aria-labelledby="kwoty" className="flex flex-col gap-3">
        <h2 id="kwoty" className="text-xl font-semibold">
          Zasiłki w pieniądzach
        </h2>
        <div className="grid gap-3 sm:grid-cols-3">
          <Stat
            label={`Wypłacone do dziś (${money.receivedCount} przelewów)`}
            value={formatPln(money.received)}
          />
          <Stat label="Jeszcze do wypłaty" value={formatPln(money.expected)} />
          <Stat
            label="Razem (brutto)"
            value={formatPln(money.received + money.expected)}
          />
        </div>
        <p className="text-xs text-muted-foreground">
          Kwoty brutto z planu przelewów na osi czasu. Dzień przelewu to
          założenie planera, a rzeczywisty termin wypłaty zależy od płatnika
          (pracodawcy albo ZUS).{" "}
          <Link
            className="font-bold text-link hover:underline"
            href={PUBLIC_PATHS.timeline}
          >
            Zobacz oś czasu
          </Link>
        </p>
      </section>

      {people.map((person) => (
        <section
          key={person}
          aria-labelledby={`urlopy-${person}`}
          className="flex flex-col gap-3"
        >
          <h2 id={`urlopy-${person}`} className="text-xl font-semibold">
            {WHO[person]}: urlopy i zasiłki
          </h2>
          <ul className="flex flex-col gap-3">
            {rows
              .filter((r) => r.period.person === person)
              .map((r) => (
                <PeriodCard key={r.period.id} row={r} />
              ))}
          </ul>
        </section>
      ))}

      {grant && (
        <section aria-labelledby="inne" className="flex flex-col gap-3">
          <h2 id="inne" className="text-xl font-semibold">
            Inne świadczenia
          </h2>
          <div className="flex flex-col gap-2 border border-border p-4">
            <p className="font-bold">{grant.title_pl}</p>
            <p className="text-sm">{grant.summary_pl}</p>
            {grant.deadline && (
              <p className="text-sm font-bold">
                Wniosek do gminy najpóźniej {formatDate(grant.deadline)}
                {grant.days_left !== null && grant.days_left < 0
                  ? " (termin minął)"
                  : ""}
              </p>
            )}
            {grant.apply_to_pl && (
              <p className="text-sm text-muted-foreground">
                {grant.apply_to_pl}
              </p>
            )}
          </div>
        </section>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 border border-border p-4">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-2xl font-bold">{value}</span>
    </div>
  );
}

function PeriodCard({ row }: { row: PeriodRow }) {
  const { period, state, used, left, useBy } = row;
  const pct = period.days ? Math.round((used / period.days) * 100) : 0;
  return (
    <li className="flex flex-col gap-2 border border-border p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-bold">{period.label_pl}</p>
        <span
          className={cn(
            "rounded-sm px-2 py-0.5 text-xs font-bold",
            STATE[state].cls,
          )}
        >
          {STATE[state].label}
        </span>
      </div>
      <p className="text-sm">
        {formatDate(period.start)} – {formatDate(period.end)} ·{" "}
        {formatWeeks(period.weeks)} ({period.days} dni)
        {period.rate !== null &&
          ` · ${Math.round(period.rate * 1000) / 10}% podstawy`}
      </p>
      <div
        role="progressbar"
        aria-label={`Wykorzystano ${used} z ${period.days} dni`}
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-2.5 w-full bg-muted"
      >
        <div className="h-full bg-primary" style={{ width: `${pct}%` }} />
      </div>
      <dl className="grid gap-x-6 gap-y-1 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-xs text-muted-foreground">Wykorzystano</dt>
          <dd className="font-bold">{used} dni</dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">Zostało</dt>
          <dd className="font-bold">
            {state === "unpaid" ? "–" : `${left} dni`}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">
            {state === "done" ? "Zakończony" : "Do kiedy"}
          </dt>
          <dd className="font-bold">
            {formatDate(useBy && state === "planned" ? useBy.due : period.end)}
          </dd>
        </div>
      </dl>
      {period.total_gross !== null && period.paid && (
        <p className="text-sm text-muted-foreground">
          Zasiłek za ten okres: {formatPln(period.total_gross)} brutto
          {period.payer
            ? ` · wypłaca ${period.payer === "zus" ? "ZUS" : "pracodawca"}`
            : ""}
        </p>
      )}
      {useBy && state !== "done" && (
        <p className="text-sm text-muted-foreground">
          Najpóźniej do {formatDate(useBy.due)} trzeba wykorzystać cały ten
          urlop ({useBy.note_pl})
        </p>
      )}
    </li>
  );
}
