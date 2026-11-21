"""Entry point of the rules engine: `evaluate(profile, params)`."""

from datetime import date, timedelta

from app.rules.benefits import (
    allowance_benefits,
    care_benefits,
    fallback_benefit,
    pregnancy_benefits,
)
from app.rules.context import Context
from app.rules.deadlines import build_deadlines
from app.rules.eligibility import debt_state, insurance_on, payer_for
from app.rules.leaves import compute_entitlement
from app.rules.models import (
    AveragedRateComparison,
    EvaluationResult,
    FamilyProfile,
    LeavePeriod,
    Person,
    Situation,
    Totals,
)
from app.rules.money import calculation_base
from app.rules.params import Params
from app.rules.planning import build_periods, resolve_plan
from app.rules.risks import build_risks


def _sum(periods: list[LeavePeriod], person: Person | None, field: str) -> float:
    return round(
        sum(
            getattr(p, field) or 0
            for p in periods
            if p.paid and (person is None or p.person == person)
        ),
        2,
    )


def _averaged_comparison(
    ctx: Context, standard: list[LeavePeriod], averaged: list[LeavePeriod]
) -> AveragedRateComparison | None:
    """Only the mother can choose the averaged 81.5% rate, and only for a birth."""
    if ctx.profile.child.situation != Situation.BIRTH or not ctx.insured("mother"):
        return None
    if ctx.ent.surviving_children == 0:
        return None
    deadline_days = ctx.params.integer("averaged_application_deadline_days")
    deadline = ctx.event + timedelta(days=deadline_days)
    still_possible = ctx.today <= deadline
    std_total = _sum(standard, None, "total_gross")
    avg_total = _sum(averaged, None, "total_gross")
    have_amounts = ctx.bases["mother"].net_base is not None

    better = None
    if have_amounts:
        diff = round(avg_total - std_total, 2)
        better = "equal" if abs(diff) < 1 else ("averaged" if diff > 0 else "standard")

    applied_late = (
        ctx.profile.averaged_rate_applied_on is not None
        and ctx.profile.averaged_rate_applied_on > deadline
    )
    note = (
        f"Wniosek o wypłatę zasiłku za cały okres macierzyńskiego i rodzicielskiego (81,5%) trzeba złożyć "
        f"najpóźniej {deadline:%d.%m.%Y} ({deadline_days} dni po porodzie)."
    )
    if applied_late:
        note += " Podany termin złożenia wniosku jest po terminie – liczymy stawki 100% i 70%."
    elif not still_possible:
        note += " Termin już minął – zostają stawki 100% i 70%."
    if have_amounts:
        note += (
            f" Porównanie łącznych kwot brutto: stawki 100%/70% = {std_total:.2f} zł, "
            f"stawka 81,5% = {avg_total:.2f} zł."
        )
    note += (
        " Wybór wpływa na rozkład wypłat w czasie: 81,5% daje stałą kwotę przez cały okres, "
        "a stawki 100%/70% – wyższą kwotę na początku. Jeśli w pierwszym roku życia dziecka nie "
        "wykorzystasz ani jednego dnia zasiłku rodzicielskiego, możesz wnioskować o wyrównanie "
        "zasiłku macierzyńskiego do 100%."
    )
    return AveragedRateComparison(
        standard_total=std_total if have_amounts else None,
        averaged_total=avg_total if have_amounts else None,
        better=better,
        deadline=deadline,
        still_possible=still_possible,
        note_pl=note,
    )


def evaluate(profile: FamilyProfile, params: Params, today: date | None = None) -> EvaluationResult:
    """Compute entitlements, amounts, timeline and risks for a family.

    Pure function: all legal numbers come from `params`. Raises `PlanError` when the chosen plan
    breaks a legal limit and `MissingParameterError` when a parameter is not defined.
    """
    today = today or date.today()
    child = profile.child
    event = child.event_date
    assert event is not None

    parents: dict[Person, object] = {}
    if profile.mother is not None:
        parents["mother"] = profile.mother
    if profile.father is not None:
        parents["father"] = profile.father

    ent = compute_entitlement(child, params)
    insurance = {p: insurance_on(parent, event) for p, parent in parents.items()}  # type: ignore[arg-type]
    bases = {p: calculation_base(p, parent, params) for p, parent in parents.items()}  # type: ignore[arg-type]
    payers = {p: payer_for(parent, params) for p, parent in parents.items()}  # type: ignore[arg-type]
    plan = resolve_plan(profile, ent, insurance, params)

    ctx = Context(
        profile=profile,
        params=params,
        today=today,
        event=event,
        event_is_estimate=child.situation == Situation.BIRTH and child.birth_date is None,
        ent=ent,
        parents=parents,  # type: ignore[arg-type]
        insurance=insurance,
        bases=bases,
        payers=payers,
        plan=plan,
    )
    for person, parent in ctx.parents.items():
        ctx.debts[person] = debt_state(parent, event, params)

    # The averaged 81.5% rate counts only if the application was filed within the deadline.
    deadline = event + timedelta(days=params.integer("averaged_application_deadline_days"))
    applied_on = profile.averaged_rate_applied_on
    ctx.averaged_deadline = deadline
    ctx.averaged_applied = (
        applied_on is not None
        and child.situation == Situation.BIRTH
        and applied_on <= deadline
        and ctx.insured("mother")
    )

    ctx.periods = build_periods(ctx, averaged=ctx.averaged_applied)
    standard = ctx.periods if not ctx.averaged_applied else build_periods(ctx, averaged=False)
    averaged = ctx.periods if ctx.averaged_applied else build_periods(ctx, averaged=True)
    comparison = _averaged_comparison(ctx, standard, averaged)

    benefits = (
        pregnancy_benefits(ctx)
        + allowance_benefits(ctx)
        + care_benefits(ctx)
        + fallback_benefit(ctx)
    )
    risks = build_risks(ctx, comparison)
    deadlines = build_deadlines(ctx, comparison)

    totals = Totals(
        mother_gross=_sum(ctx.periods, "mother", "total_gross"),
        father_gross=_sum(ctx.periods, "father", "total_gross"),
        family_gross=_sum(ctx.periods, None, "total_gross"),
        family_net_estimate=_sum(ctx.periods, None, "total_net_estimate"),
    )

    assumptions = [
        f"Użyto parametrów prawnych obowiązujących w dniu {params.on:%d.%m.%Y}.",
        "Zasiłek za pełny miesiąc kalendarzowy to kwota miesięczna, za niepełny – 1/30 za każdy dzień.",
        "Kwoty netto są szacunkowe (składka zdrowotna i zaliczka na podatek, bez ulg i dochodów z innych źródeł).",
        "Wynik ma charakter informacyjny – decyzję o prawie do zasiłku i jego wysokości wydaje ZUS lub płatnik.",
    ]
    if ctx.event_is_estimate:
        assumptions.append(f"Przyjęto przewidywaną datę porodu: {event:%d.%m.%Y}.")
    assumptions.extend(plan.notes_pl)
    assumptions.extend(ent.notes_pl)
    if ent.leave_blocked_reason_pl:
        assumptions.append(ent.leave_blocked_reason_pl)

    return EvaluationResult(
        params_date=params.on,
        situation=child.situation,
        event_date=event,
        event_is_estimate=ctx.event_is_estimate,
        bases=list(bases.values()),
        benefits=benefits,
        timeline=sorted(ctx.periods, key=lambda p: (p.start, p.person)),
        risks=risks,
        deadlines=deadlines,
        averaged_rate=comparison,
        totals=totals,
        situation_tags=ent.tags,
        assumptions_pl=assumptions,
    )
