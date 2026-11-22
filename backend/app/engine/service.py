"""Runs the rules for a family profile and builds the API answer (`EvaluationResult`)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, timedelta
from typing import Any

from app.engine.facts import build_facts
from app.engine.runtime import PlanViolation, RuleDef, RunResult, Runtime
from app.rules.models import (
    AveragedRateComparison,
    BenefitResult,
    CalculationBase,
    Deadline,
    EvaluationResult,
    FamilyProfile,
    LeavePeriod,
    Risk,
    Status,
    Totals,
)

PERSON_PREFIX = {"mother": "mama", "father": "tata"}
STATUS = {
    "przysluguje": Status.ELIGIBLE,
    "warunkowo": Status.CONDITIONAL,
    "nie_przysluguje": Status.NOT_ELIGIBLE,
    "informacja": Status.INFO,
}
PAYER = {"pracodawca": "employer", "zus": "zus"}
SOON_DAYS = 14

__all__ = ["PlanViolation", "evaluate_profile"]


def _basis(text: str | None) -> list[str]:
    return [part.strip() for part in (text or "").split(";") if part.strip()]


def _periods(run: RunResult, scope: Mapping[str, Any], divisor: float) -> list[LeavePeriod]:
    out = []
    for p in sorted(run.periods, key=lambda x: (x["start"], x["rule"].code)):
        person = p["osoba"] or "family"
        base = scope.get(f"{PERSON_PREFIX.get(person, '')}_podstawa")
        rate = p["stawka"]
        work = float(p["praca"] or 0)
        monthly = (
            round(base * rate * (1 - work), 2) if base is not None and rate is not None else None
        )
        total = round(monthly / divisor * p["dni"], 2) if monthly is not None else None
        out.append(
            LeavePeriod(
                id=p["rule"].code,
                person=person,
                kind=p["rule"].period_kind or "maternity",
                label_pl=p["tytul"] or p["rule"].title_pl,
                start=p["start"],
                end=p["koniec"],
                days=p["dni"],
                weeks=round(p["dni"] / 7, 2),
                paid=True,
                rate=rate,
                monthly_gross=monthly,
                total_gross=total,
                total_net_estimate=None,
                work_fraction=work,
                payer=PAYER.get(p.get("platnik") or ""),
                rule=p["rule"].code,
            )
        )
    return out


def _run(
    rules: list[RuleDef], params: Mapping[str, Any], profile: FamilyProfile, today: date
) -> RunResult:
    return Runtime(rules, params, today).run(build_facts(profile))


def _family_total(rules, params, profile, today, divisor) -> float | None:
    try:
        run = _run(rules, params, profile, today)
    except PlanViolation:
        return None
    periods = _periods(run, run.scope, divisor)
    if any(p.total_gross is None for p in periods if p.kind in ("maternity", "parental")):
        return None
    return round(sum(p.total_gross or 0 for p in periods if p.kind in ("maternity", "parental")), 2)


def evaluate_profile(
    profile: FamilyProfile,
    rules: Iterable[RuleDef],
    params: Mapping[str, Any],
    today: date,
    params_date: date | None = None,
    rules_version: str | None = None,
    with_comparison: bool = True,
) -> tuple[EvaluationResult, RunResult]:
    """Raises PlanViolation when the plan breaks the law (a `walidacja` rule fired)."""
    rules = list(rules)
    facts = build_facts(profile)
    run = Runtime(rules, params, today).run(facts)
    scope = run.scope
    divisor = float(params.get("benefit_daily_divisor") or 30)
    timeline = _periods(run, scope, divisor)

    # --- Calculation bases --------------------------------------------------------------------
    bases = []
    for person, prefix in PERSON_PREFIX.items():
        parent = facts[prefix]
        if not parent["obecny"]:
            continue
        gross = parent.get("podstawa_brutto")
        net = scope.get(f"{prefix}_podstawa")
        deduction = float(params.get("social_contribution_deduction") or 0)
        minimum_applied = (
            gross is not None
            and net is not None
            and round(gross * (1 - deduction), 2) < net
            and parent["pracownik"]
        )
        bases.append(
            CalculationBase(
                person=person,
                gross_base=gross,
                net_base=net,
                minimum_wage_applied=bool(minimum_applied),
                note_pl=(
                    "Podstawa nieznana – podaj przeciętne wynagrodzenie lub podstawę składki chorobowej."
                    if net is None
                    else "Podstawa = przeciętne miesięczne wynagrodzenie (przychód) − 13,71%"
                    + (
                        "; podniesiona do minimum z płacy minimalnej (pełny etat)."
                        if minimum_applied
                        else "."
                    )
                ),
            )
        )

    # --- Messages -----------------------------------------------------------------------------
    deadlines, risks, documents, info, assumptions = [], [], {}, [], []
    for m in run.messages:
        kind = m.rule.kind
        if kind == "termin" and m.date:
            left = (m.date - today).days
            deadlines.append(
                Deadline(
                    code=m.rule.code,
                    person=m.person,
                    kind="use_by" if m.rule.deadline_kind == "use_by" else "apply",
                    title_pl=m.title,
                    due=m.date,
                    days_left=left,
                    status="overdue" if left < 0 else ("soon" if left <= SOON_DAYS else "open"),
                    note_pl=m.text,
                    benefit_code=m.rule.benefit,
                    legal_basis=m.rule.legal_basis or None,
                    late_pl=m.late_text or None,
                )
            )
        elif kind == "ryzyko":
            risks.append(
                Risk(
                    code=m.rule.code,
                    severity=m.rule.severity
                    if m.rule.severity in ("high", "medium", "info")
                    else "info",
                    person=m.person,
                    title_pl=m.title,
                    text_pl=m.text,
                    legal_basis=m.rule.legal_basis or None,
                )
            )
        elif kind == "dokument":
            documents.setdefault(m.rule.benefit or "", []).append(
                f"{m.title}: {m.text}" if m.title else m.text
            )
        elif kind == "informacja":
            info.append(f"{m.title}: {m.text}" if m.title else m.text)
        elif kind == "zalozenie":
            assumptions.append(f"{m.title}: {m.text}" if m.title else m.text)
    deadlines.sort(key=lambda d: d.due)
    severity_rank = {"high": 0, "medium": 1, "info": 2}
    risks.sort(key=lambda r: severity_rank[r.severity])

    # --- Benefits -----------------------------------------------------------------------------
    by_rule = {p.rule: p for p in timeline}
    benefits = []
    for b in sorted(run.benefits, key=lambda x: (x["rule"].order, x["rule"].code)):
        code = b["rule"].code
        own = [by_rule[p["code"]] for p in b["periods"] if p["code"] in by_rule]
        days = sum(p.days for p in own) or None
        totals = [p.total_gross for p in own]
        monthly = [p.monthly_gross for p in own if p.monthly_gross is not None]
        rates = {p.rate for p in own if p.rate is not None}
        apply_deadlines = [d for d in deadlines if d.benefit_code == code and d.kind == "apply"]
        upcoming = [d for d in apply_deadlines if d.days_left >= 0] or apply_deadlines
        first = upcoming[0] if upcoming else None
        benefits.append(
            BenefitResult(
                code=code,
                person=b["person"],
                title_pl=b["title"],
                status=STATUS.get(str(b["status"]), Status.INFO),
                summary_pl=b["summary"],
                reasons_pl=[],
                legal_basis=_basis(b["rule"].legal_basis),
                weeks=round(days / 7, 2) if days else None,
                days=days,
                rate=rates.pop() if len(rates) == 1 else None,
                monthly_gross=monthly[0] if monthly else None,
                total_gross=round(sum(totals), 2)
                if own and all(t is not None for t in totals)
                else None,
                start=min((p.start for p in own), default=None),
                end=max((p.end for p in own), default=None),
                payer=PAYER.get(str(b["payer"] or "")),
                apply_to_pl=b["apply_to"] or None,
                documents_pl=documents.get(code, []),
                deadline=first.due if first else None,
                days_left=first.days_left if first else None,
                deadline_note_pl=first.note_pl if first else None,
                periods=[p.rule for p in own if p.rule],
            )
        )

    # --- Averaged rate comparison ------------------------------------------------------------
    averaged = None
    if (
        with_comparison
        and scope.get("dziecko_zyje")
        and (scope.get("mama_uprawniona") or scope.get("przyjecie_tata_calosc"))
    ):
        std = _family_total(
            rules,
            params,
            profile.model_copy(
                update={"plan": profile.plan.model_copy(update={"averaged_rate": False})}
            ),
            today,
            divisor,
        )
        avg_profile = profile.model_copy(
            update={"plan": profile.plan.model_copy(update={"averaged_rate": True})}
        )
        avg = _family_total(rules, params, avg_profile, today, divisor)
        deadline = facts["dziecko"]["data"] + timedelta(
            days=int(params.get("averaged_application_deadline_days") or 21)
        )
        better = None
        if std is not None and avg is not None:
            diff = avg - std
            better = "equal" if abs(diff) < 1 else ("averaged" if diff > 0 else "standard")
        averaged = AveragedRateComparison(
            standard_total=std,
            averaged_total=avg,
            better=better,
            deadline=deadline,
            still_possible=bool(scope.get("usredniona_w_terminie")),
            note_pl="Porównanie łącznej kwoty zasiłku za urlop macierzyński i rodzicielski: 100% + 70% albo 81,5% "
            "przez cały okres (9 tygodni drugiego rodzica zawsze 70%) – art. 30a i 31 ustawy zasiłkowej.",
        )

    # --- Totals and tags ----------------------------------------------------------------------
    def total(person: str | None) -> float:
        return round(
            sum(p.total_gross or 0 for p in timeline if person is None or p.person == person), 2
        )

    child = facts["dziecko"]
    tags = [
        t
        for t, on in (
            ("stillbirth", child["martwe_urodzenie"]),
            ("child_death", child["data_zgonu"] is not None and not child["martwe_urodzenie"]),
            ("adoption", child["zdarzenie"] == "przysposobienie"),
            ("foster", child["zdarzenie"] == "rodzina_zastepcza"),
            ("za_zyciem", child["za_zyciem"]),
            ("multiple", child["liczba"] > 1),
            ("supplementary", bool(scope.get("uzup_tyg"))),
        )
        if on
    ]

    result = EvaluationResult(
        params_date=params_date or today,
        situation=profile.child.situation,
        event_date=child["data"],
        event_is_estimate=profile.child.situation.value == "birth" and not child["urodzone"],
        bases=bases,
        benefits=benefits,
        timeline=timeline,
        risks=risks,
        deadlines=deadlines,
        averaged_rate=averaged,
        totals=Totals(
            mother_gross=total("mother"),
            father_gross=total("father"),
            family_gross=total(None),
            family_net_estimate=0,
        ),
        situation_tags=tags,
        assumptions_pl=assumptions,
        info_pl=info,
        rules_version=rules_version,
        rule_errors=run.errors,
    )
    return result, run
