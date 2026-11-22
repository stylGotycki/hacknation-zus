"use client";

import { ChevronRight, Lightbulb } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import type {
  ApplicationRecord,
  ApplicationStatus,
  BenefitResult,
  Deadline,
  EvaluationResult,
  Payment,
  Suggestion,
} from "@/lib/api";
import { PUBLIC_PATHS } from "@/lib/routes";
import { loadCitizen } from "@/lib/session";
import {
  formatDate,
  formatDaysLeft,
  formatPercent,
  formatPln,
  formatWeeks,
} from "@/lib/format";
import { TimelineEvent, TimelineExtras } from "@/components/timeline/model";

export const STATUS_LABEL: Record<ApplicationStatus, string> = {
  submitted: "złożony",
  in_progress: "w rozpatrzeniu",
  decided: "rozpatrzony",
};

export const RECIPIENT = {
  employer: "pracodawcy",
  zus: "ZUS",
  registry: "urzędu stanu cywilnego",
} as const;

export const PAYER_LABEL = {
  employer: "Wypłaca pracodawca",
  zus: "Wypłaca ZUS",
} as const;

export function benefitFor(
  result: EvaluationResult,
  event: TimelineEvent,
): BenefitResult | undefined {
  if (event.deadline?.benefit_code)
    return result.benefits.find((b) => b.code === event.deadline!.benefit_code);
  const p = event.period;
  if (!p) return undefined;
  return result.benefits.find(
    (b) => p.rule !== null && b.periods.includes(p.rule),
  );
}

export function DetailList({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  if (!items.length) return null;
  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
        {title}
      </p>
      <ul className="ml-4 list-disc text-sm">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

/** Leave kind behind an event (from its period or from the benefit of its deadline). */
export function kindOf(event: TimelineEvent): string | null {
  if (event.period) return event.period.kind;
  const code = event.deadline?.benefit_code ?? "";
  const prefixes: [string, string][] = [
    ["macierzynski", "maternity"],
    ["uzupelniajacy", "supplementary"],
    ["rodzicielski", "parental"],
    ["ojcowski", "paternity"],
  ];
  return prefixes.find(([prefix]) => code.startsWith(prefix))?.[1] ?? null;
}

export const KIND_FORMS: Record<string, string[]> = {
  maternity: [
    "leave_maternity_before",
    "leave_taken_in",
    "leave_maternity_father",
    "leave_maternity_resignation",
  ],
  supplementary: ["leave_supplementary"],
  parental: ["leave_parental", "parental_work"],
  paternity: ["leave_paternity"],
};

/** The form a parent files for this event: the request tied to its deadline, else one for its leave. */
export function suggestionFor(
  event: TimelineEvent,
  extras: TimelineExtras,
): Suggestion | undefined {
  const d = event.deadline;
  if (d) {
    const tied = extras.suggestions.find((s) =>
      s.deadline_codes.includes(d.code),
    );
    if (tied) return tied;
  }
  const kind = kindOf(event);
  const person = event.period?.person ?? d?.person;
  if (!kind || (person !== "mother" && person !== "father")) return undefined;
  const mine = extras.suggestions.filter((s) => s.person === person);
  return (
    mine.find((s) => KIND_FORMS[kind]?.includes(s.form_code)) ??
    mine.find((s) => s.form_code === "zus_zam")
  );
}

export function ApplicationHistory({
  application,
}: {
  application: ApplicationRecord;
}) {
  return (
    <ol className="ml-1 flex flex-col gap-1 border-l-[3px] border-navy pl-3 text-sm">
      {application.history.map((h) => (
        <li key={h.at + h.status}>
          <span className="text-xs text-muted-foreground">
            {formatDate(h.at.slice(0, 10))}
          </span>{" "}
          · {h.note}
        </li>
      ))}
    </ol>
  );
}

export function ApplicationBox({
  event,
  extras,
}: {
  event: TimelineEvent;
  extras: TimelineExtras;
}) {
  const [loggedIn, setLoggedIn] = useState(false);
  useEffect(() => setLoggedIn(loadCitizen() !== null), []);
  if (event.application) {
    const a = event.application;
    return (
      <section className="flex flex-col gap-2 border-l-[5px] border-navy bg-background p-3">
        <p className="font-bold">{a.title_pl}</p>
        <p className="text-sm">
          Złożony do {RECIPIENT[a.submitted_to ?? "employer"]} · status:{" "}
          <b>{STATUS_LABEL[a.status]}</b>
        </p>
        <ApplicationHistory application={a} />
        <Link
          href={PUBLIC_PATHS.applications}
          className="inline-flex items-center gap-1 text-sm font-bold text-link hover:underline"
        >
          Przejdź do wniosków <ChevronRight className="size-4" />
        </Link>
      </section>
    );
  }
  const suggestion = suggestionFor(event, extras);
  if (!suggestion) return null;
  const filed = extras.applications.find(
    (a) =>
      a.form_code === suggestion.form_code &&
      (a.person === null || a.person === suggestion.person),
  );
  return (
    <section className="flex flex-col gap-2 border-l-[5px] border-navy bg-background p-3">
      <p className="text-xs font-bold uppercase tracking-wide text-navy">
        Wniosek
      </p>
      <p className="font-bold">{suggestion.title_pl}</p>
      <p className="text-sm">
        Składasz do {RECIPIENT[suggestion.submitted_to]}
        {suggestion.deadline && filed?.status !== "decided" && (
          <>
            {" "}
            · termin: <b>{formatDate(suggestion.deadline)}</b>
            {suggestion.days_left !== null &&
              ` (${formatDaysLeft(suggestion.days_left)})`}
          </>
        )}
      </p>
      {filed ? (
        <>
          <p className="text-sm">
            Złożony{" "}
            {filed.created_at ? formatDate(filed.created_at.slice(0, 10)) : ""}{" "}
            · status: <b>{STATUS_LABEL[filed.status]}</b>
          </p>
          <ApplicationHistory application={filed} />
        </>
      ) : (
        <Link
          href={
            loggedIn
              ? `${PUBLIC_PATHS.applications}?form=${suggestion.form_code}`
              : PUBLIC_PATHS.login
          }
          className="inline-flex h-10 w-fit items-center gap-2 rounded-sm bg-primary px-4 text-sm font-bold text-white hover:bg-primary-dark"
        >
          {loggedIn ? "Wypełnij wniosek" : "Zaloguj się, aby złożyć wniosek"}{" "}
          <ChevronRight className="size-4" />
        </Link>
      )}
    </section>
  );
}

export function PaymentDetails({ payment }: { payment: Payment }) {
  return (
    <div className="flex flex-col gap-2 text-sm">
      <p>
        <span className="font-medium">Przelew {formatDate(payment.date)}</span>
        {payment.payer &&
          ` · ${payment.payer === "zus" ? "wypłaca ZUS" : "wypłaca pracodawca"}`}
      </p>
      <ul className="ml-4 list-disc">
        {payment.lines.map((l) => (
          <li key={l.label_pl}>
            {l.label_pl}: {l.days} dni – {formatPln(l.amount_gross)}
          </li>
        ))}
      </ul>
      <p className="text-xs text-muted-foreground">
        Kwota brutto to część zasiłku za dni urlopu w tym miesiącu. Dzień
        przelewu to założenie planera (parametr „Dzień przelewu zasiłku w
        miesiącu”) – termin wypłaty zależy od płatnika (art. 64 ust. 1 ustawy
        zasiłkowej).
      </p>
    </div>
  );
}

export function LateAdvice({ deadline }: { deadline: Deadline }) {
  return (
    <div className="flex gap-2 border-l-[5px] border-amber-500 bg-amber-50 p-3 text-sm">
      <Lightbulb
        className="mt-0.5 size-4 shrink-0 text-amber-700"
        aria-hidden
      />
      <p>
        <span className="font-bold">Termin minął – co możesz zrobić: </span>
        {deadline.late_pl}
      </p>
    </div>
  );
}

export function EventDetails({
  result,
  event,
  extras,
}: {
  result: EvaluationResult;
  event: TimelineEvent;
  extras: TimelineExtras;
}) {
  const benefit = benefitFor(result, event);
  const p = event.period;
  const d = event.deadline;
  return (
    <div className="mt-2 flex flex-col gap-3 border border-border bg-muted p-3">
      <ApplicationBox event={event} extras={extras} />
      {p && (
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-xs text-muted-foreground">Okres</dt>
            <dd>
              {formatDate(p.start)} – {formatDate(p.end)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Długość</dt>
            <dd>
              {formatWeeks(p.weeks)} ({p.days} dni)
            </dd>
          </div>
          {p.rate !== null && (
            <div>
              <dt className="text-xs text-muted-foreground">Stawka</dt>
              <dd>{formatPercent(p.rate)} podstawy</dd>
            </div>
          )}
          {p.monthly_gross !== null && (
            <div>
              <dt className="text-xs text-muted-foreground">
                Miesięcznie brutto
              </dt>
              <dd>{formatPln(p.monthly_gross)}</dd>
            </div>
          )}
          {p.total_gross !== null && (
            <div>
              <dt className="text-xs text-muted-foreground">
                Za cały okres brutto
              </dt>
              <dd>{formatPln(p.total_gross)}</dd>
            </div>
          )}
          {p.work_fraction > 0 && (
            <div>
              <dt className="text-xs text-muted-foreground">
                Praca w trakcie urlopu
              </dt>
              <dd>{formatPercent(p.work_fraction)} etatu</dd>
            </div>
          )}
        </dl>
      )}
      {event.payment && <PaymentDetails payment={event.payment} />}
      {d && !(event.application?.status === "decided") && (
        <p className="text-sm">
          <span className="font-medium">Termin: {formatDate(d.due)}.</span>{" "}
          {d.note_pl}
        </p>
      )}
      {d && d.status === "overdue" && d.late_pl && !event.application && (
        <LateAdvice deadline={d} />
      )}
      {benefit && (
        <>
          <p className="text-sm">
            <span className="font-medium">{benefit.title_pl}.</span>{" "}
            {benefit.summary_pl}
          </p>
          {benefit.payer && (
            <p className="text-sm text-muted-foreground">
              {PAYER_LABEL[benefit.payer]}
            </p>
          )}
          {benefit.apply_to_pl && (
            <p className="text-sm">
              <span className="font-medium">Gdzie złożyć: </span>
              {benefit.apply_to_pl}
            </p>
          )}
          {benefit.deadline && (
            <p className="text-sm">
              <span className="font-medium">Wniosek do: </span>
              {formatDate(benefit.deadline)}
              {benefit.days_left !== null &&
                ` (${formatDaysLeft(benefit.days_left)})`}
              {benefit.deadline_note_pl && ` – ${benefit.deadline_note_pl}`}
            </p>
          )}
          <DetailList title="Dokumenty" items={benefit.documents_pl} />
          <DetailList title="Dlaczego" items={benefit.reasons_pl} />
          {benefit.legal_basis.length > 0 && (
            <p className="text-xs text-muted-foreground">
              Podstawa prawna: {benefit.legal_basis.join("; ")}
            </p>
          )}
        </>
      )}
      {!benefit && !p && !d && !event.application && !event.payment && (
        <p className="text-sm text-muted-foreground">
          Brak dodatkowych szczegółów.
        </p>
      )}
    </div>
  );
}
