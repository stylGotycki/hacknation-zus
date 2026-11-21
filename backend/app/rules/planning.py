"""Turns entitlements + the parents' choices into a validated plan and a dated timeline."""

from datetime import date, timedelta

from app.rules.context import Context, ResolvedPlan
from app.rules.dates import end_of_period, weeks_to_days
from app.rules.eligibility import DebtState, Insurance
from app.rules.leaves import Entitlement, PlanError
from app.rules.models import (
    EmploymentType,
    FamilyProfile,
    LeavePeriod,
    MotherCannotCare,
    Person,
    Situation,
)
from app.rules.money import amount_for_period, monthly_amount, net_with_minimum
from app.rules.params import Params


def resolve_plan(
    profile: FamilyProfile,
    ent: Entitlement,
    insurance: dict[Person, Insurance],
    params: Params,
) -> ResolvedPlan:
    plan = profile.plan
    child = profile.child
    notes: list[str] = []
    both = profile.mother is not None and profile.father is not None

    # --- Maternity leave ---------------------------------------------------------------------
    maternity = ent.maternity_weeks
    before = plan.maternity_before_birth_weeks if child.situation == Situation.BIRTH else 0
    if before > params.integer("maternity_before_birth_max_weeks"):
        raise PlanError(
            f"Maternity leave may start at most "
            f"{params.integer('maternity_before_birth_max_weeks')} weeks before birth"
        )

    to_father = plan.maternity_weeks_to_father
    cannot_care = profile.mother_cannot_care
    mother_present = profile.mother is not None
    if ent.surviving_children == 0:
        to_father = 0  # stillbirth: the whole leave belongs to the mother
    if cannot_care in (MotherCannotCare.DEATH, MotherCannotCare.ABANDONED):
        to_father = maternity - before if profile.father is not None else 0
        before = 0
        if profile.father is not None:
            notes.append(
                "Ojciec przejmuje cały urlop macierzyński (matka zmarła lub porzuciła dziecko)."
            )
    elif to_father > 0:
        if profile.father is None:
            raise PlanError("maternity_weeks_to_father needs a father in the profile")
        if mother_present and not insurance["mother"].insured:
            raise PlanError("Father cannot take over maternity leave of a mother who has no leave")
        mandatory = (
            0
            if cannot_care in (MotherCannotCare.HOSPITAL, MotherCannotCare.DISABLED)
            else params.integer("maternity_mother_mandatory_weeks")
        )
        if maternity - before - to_father < mandatory:
            raise PlanError(
                f"Mother must use at least {mandatory} weeks of maternity leave after birth; "
                f"father can take at most {max(maternity - before - mandatory, 0)} weeks"
            )
    mother_total = maternity - to_father

    # --- Supplementary leave -----------------------------------------------------------------
    supplementary = ent.supplementary_weeks if plan.use_supplementary_leave else 0
    taker: Person | None = None
    if supplementary:
        taker = plan.supplementary_taken_by
        if taker not in (p for p in ("mother", "father") if getattr(profile, p) is not None):
            taker = "mother" if profile.mother is not None else "father"

    # --- Parental leave ----------------------------------------------------------------------
    total = ent.parental_weeks
    reserved = params.integer("parental_non_transferable_weeks")
    mother_parental = father_parental = 0
    if total:
        if both and cannot_care in (MotherCannotCare.DEATH, MotherCannotCare.ABANDONED):
            father_parental = total
            reserved = 0
        elif both:
            father_parental = (
                plan.parental_weeks_father if plan.parental_weeks_father is not None else reserved
            )
            if not reserved <= father_parental <= total - reserved:
                raise PlanError(
                    f"Father's parental leave must be between {reserved} and {total - reserved} "
                    f"weeks (each parent keeps {reserved} weeks that cannot be transferred)"
                )
            mother_parental = total - father_parental
        elif profile.mother is not None:
            if plan.parental_weeks_father:
                raise PlanError("parental_weeks_father needs a father in the profile")
            mother_parental, reserved = total, 0
        else:
            father_parental, reserved = total, 0

        max_parts = params.integer("parental_max_parts")
        for parts in (plan.parental_parts_mother, plan.parental_parts_father):
            if parts > max_parts:
                raise PlanError(f"Parental leave can be split into at most {max_parts} parts")

    # --- Working while on parental leave ----------------------------------------------------
    max_fraction = params.number("parental_work_max_fraction")
    fractions: dict[Person, float] = {}
    for person in ("mother", "father"):
        parent = getattr(profile, person)
        fraction = parent.planned_work_fraction if parent is not None else 0
        if fraction > max_fraction:
            raise PlanError(f"Work during parental leave is limited to {max_fraction} of full time")
        if fraction > 0 and parent.employment != EmploymentType.EMPLOYEE:
            raise PlanError("Only employees can combine parental leave with work")
        fractions[person] = fraction

    # --- Paternity ---------------------------------------------------------------------------
    max_paternity_parts = params.integer("paternity_max_parts")
    if plan.paternity_parts > max_paternity_parts:
        raise PlanError(f"Paternity leave can be split into at most {max_paternity_parts} parts")
    min_part = params.integer("paternity_min_part_days")
    if plan.paternity_parts > 1 and ent.paternity_days // plan.paternity_parts < min_part:
        raise PlanError(f"Each part of paternity leave must last at least {min_part} days")

    return ResolvedPlan(
        before_birth=before,
        mother_maternity_total=mother_total,
        father_maternity=to_father,
        supplementary=supplementary,
        supplementary_taker=taker,
        mother_parental=mother_parental,
        father_parental=father_parental,
        father_reserved=reserved if both else 0,
        mother_work_fraction=fractions["mother"],
        father_work_fraction=fractions["father"],
        paternity_parts=plan.paternity_parts,
        notes_pl=notes,
    )


def _rate_for(kind: str, reserved_for_other: bool, averaged: bool, params: Params) -> float:
    """Allowance rate. The averaged 81.5% covers maternity and parental leave of both parents,
    except the 9 weeks of parental leave that belong to the parent who did not apply (70%)."""
    if kind in ("supplementary", "paternity", "pregnancy_sickness"):
        return params.number("rate_maternity")
    if kind == "maternity":
        return params.number("rate_averaged") if averaged else params.number("rate_maternity")
    if averaged and not reserved_for_other:
        return params.number("rate_averaged")
    return params.number("rate_parental")


class _Builder:
    def __init__(self, ctx: Context, averaged: bool):
        self.ctx = ctx
        self.averaged = averaged
        self.periods: list[LeavePeriod] = []

    def add(
        self,
        person: Person,
        kind: str,
        label: str,
        start: date,
        days: int,
        *,
        reserved_for_other: bool = False,
        work_fraction: float = 0,
        end_cap: date | None = None,
        end_floor: date | None = None,
    ) -> date:
        """Append a period; returns the day after it ends (start of the next block)."""
        ctx = self.ctx
        end = end_of_period(start, days)
        if end_cap is not None:
            end = min(end, max(end_cap, start))
        if end_floor is not None:
            end = max(end, end_floor)
        days = (end - start).days + 1

        rate = _rate_for(kind, reserved_for_other, self.averaged, ctx.params)
        base = ctx.bases[person]
        monthly = monthly_amount(base, rate, work_fraction)
        debt: DebtState | None = ctx.debts.get(person)
        paid = ctx.insured(person) and not (debt is not None and debt.kind == "blocked")

        total = net_total = None
        if monthly is not None:
            net_monthly, _ = net_with_minimum(monthly, ctx.params, work_fraction)
            pay_from = debt.effective_start if debt and debt.kind == "paid_late" else start
            pay_from = max(pay_from, start)
            total = (
                amount_for_period(
                    pay_from, end, monthly, ctx.params.integer("benefit_days_per_month")
                )
                if paid and pay_from <= end
                else 0.0
            )
            net_total = round(total * (net_monthly / monthly), 2) if monthly else 0.0

        self.periods.append(
            LeavePeriod(
                id=f"{person}-{kind}-{len(self.periods) + 1}",
                person=person,
                kind=kind,  # type: ignore[arg-type]
                label_pl=label,
                start=start,
                end=end,
                days=days,
                weeks=round(days / 7, 2),
                paid=paid,
                rate=rate,
                monthly_gross=monthly,
                total_gross=total,
                total_net_estimate=net_total,
                work_fraction=work_fraction,
            )
        )
        return end + timedelta(days=1)


def build_periods(ctx: Context, averaged: bool) -> list[LeavePeriod]:
    """Default timeline: maternity (mother, then the part taken over by the father),
    supplementary leave, parental leave (mother, then father), paternity leave at birth."""
    b = _Builder(ctx, averaged)
    plan = ctx.plan
    ent = ctx.ent
    child = ctx.profile.child
    params = ctx.params
    event = ctx.event
    birth_case = child.situation == Situation.BIRTH
    cursor = event  # first day after the maternity-type blocks so far

    # --- Maternity ---------------------------------------------------------------------------
    if plan.mother_maternity_total > 0 and ctx.insured("mother"):
        start = weeks_to_days(plan.before_birth)
        start_date = event - timedelta(days=start)
        end_floor = None
        if ent.surviving_children == 0 and child.died_on is not None:
            end_floor = child.died_on + timedelta(days=params.integer("child_death_min_days"))
        label = "Urlop macierzyński" if birth_case else "Urlop na warunkach urlopu macierzyńskiego"
        cursor = b.add(
            "mother",
            "maternity",
            label,
            start_date,
            weeks_to_days(plan.mother_maternity_total),
            end_cap=ent.maternity_end_cap,
            end_floor=end_floor,
        )
    if plan.father_maternity > 0 and ctx.insured("father"):
        cursor = b.add(
            "father",
            "maternity",
            "Urlop macierzyński przejęty od matki",
            cursor,
            weeks_to_days(plan.father_maternity),
        )

    # --- Supplementary ------------------------------------------------------------------------
    if plan.supplementary and plan.supplementary_taker and ctx.insured(plan.supplementary_taker):
        cursor = b.add(
            plan.supplementary_taker,
            "supplementary",
            "Uzupełniający urlop macierzyński",
            cursor,
            weeks_to_days(plan.supplementary),
        )

    # --- Parental ----------------------------------------------------------------------------
    for person, weeks, fraction in (
        ("mother", plan.mother_parental, plan.mother_work_fraction),
        ("father", plan.father_parental, plan.father_work_fraction),
    ):
        if weeks <= 0 or not ctx.insured(person):  # type: ignore[arg-type]
            continue
        # Working part-time stretches the leave: it is granted for the remaining part of the
        # working time, so the same number of "full" weeks lasts longer.
        days = round(weeks_to_days(weeks) / (1 - fraction))
        label = "Urlop rodzicielski" + (
            f" (praca w {fraction * 100:.0f}% etatu)" if fraction else ""
        )
        if averaged and person == "father" and plan.father_reserved:
            reserved_days = round(weeks_to_days(plan.father_reserved) / (1 - fraction))
            reserved_days = min(reserved_days, days)
            cursor = b.add(
                "father",
                "parental",
                "Urlop rodzicielski – część nieprzenoszalna",
                cursor,
                reserved_days,
                reserved_for_other=True,
                work_fraction=fraction,
            )
            days -= reserved_days
            label = "Urlop rodzicielski – pozostała część"
            if days <= 0:
                continue
        cursor = b.add(
            person,  # type: ignore[arg-type]
            "parental",
            label,
            cursor,
            days,
            work_fraction=fraction,
        )

    # --- Paternity ---------------------------------------------------------------------------
    if ent.paternity_days and ctx.insured("father") and "father" in ctx.parents:
        days = ent.paternity_days
        if plan.paternity_parts == 1:
            b.add("father", "paternity", "Urlop ojcowski", event, days)
        else:
            first = days // 2
            b.add("father", "paternity", "Urlop ojcowski – część 1", event, first)
            b.add(
                "father",
                "paternity",
                "Urlop ojcowski – część 2",
                event + timedelta(days=28),
                days - first,
            )
    return b.periods
