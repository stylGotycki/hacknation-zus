"""Calculation base and amounts of benefits."""

import calendar
from datetime import date, timedelta

from app.rules.models import CalculationBase, EmploymentType, ParentProfile, Person
from app.rules.params import Params


def calculation_base(person: Person, parent: ParentProfile, params: Params) -> CalculationBase:
    """Monthly base of the allowance = average gross base of 12 months minus 13.71%.

    Employees: not lower than the minimum wage (scaled by working time).
    Others (self-employed, contract, cooperating): average base of the sickness contribution.
    """
    deduction = params.number("social_contribution_deduction")
    average = parent.average_monthly_base

    if average is None:
        return CalculationBase(
            person=person,
            gross_base=None,
            net_base=None,
            note_pl="Podaj średnią miesięczną podstawę z ostatnich 12 miesięcy, aby policzyć kwoty.",
        )

    gross = average
    min_applied = False
    if parent.employment == EmploymentType.EMPLOYEE:
        floor = params.number("minimum_wage") * parent.working_time_fraction
        if gross < floor:
            gross, min_applied = floor, True
        note = (
            "Pracownik: średnie wynagrodzenie z 12 miesięcy pomniejszone o składki społeczne "
            f"({deduction * 100:.2f}%); podstawa nie może być niższa niż płaca minimalna"
            + (" (zastosowano płacę minimalną)." if min_applied else ".")
        )
    else:
        note = (
            "Średnia podstawa składki na ubezpieczenie chorobowe z ostatnich 12 miesięcy "
            f"pomniejszona o {deduction * 100:.2f}%."
        )
    return CalculationBase(
        person=person,
        gross_base=round(gross, 2),
        net_base=round(gross * (1 - deduction), 2),
        minimum_wage_applied=min_applied,
        note_pl=note,
    )


def monthly_amount(base: CalculationBase, rate: float, work_fraction: float = 0) -> float | None:
    if base.net_base is None:
        return None
    return round(base.net_base * rate * (1 - work_fraction), 2)


def amount_for_period(start: date, end: date, monthly: float, days_per_month: int = 30) -> float:
    """Allowance for a period: a full calendar month pays the monthly amount, a part of a month
    pays 1/30 of it for every day (ZUS convention)."""
    total = 0.0
    cursor = start
    while cursor <= end:
        days_in_month = calendar.monthrange(cursor.year, cursor.month)[1]
        month_end = date(cursor.year, cursor.month, days_in_month)
        chunk_end = min(end, month_end)
        covered = (chunk_end - cursor).days + 1
        if covered == days_in_month:
            total += monthly
        else:
            total += min(monthly, monthly * covered / days_per_month)
        cursor = chunk_end + timedelta(days=1)
    return round(total, 2)


def net_estimate(monthly_gross: float, params: Params) -> float:
    """Rough monthly net: minus health contribution and income tax advance (first bracket,
    with the monthly reducing amount). Informational only – real payouts depend on the payer."""
    health = monthly_gross * params.number("health_contribution_rate")
    tax = max(
        0.0,
        monthly_gross * params.number("income_tax_rate")
        - params.number("income_tax_monthly_reduction"),
    )
    return round(max(monthly_gross - health - tax, 0.0), 2)


def net_with_minimum(
    monthly_gross: float, params: Params, work_fraction: float = 0
) -> tuple[float, bool]:
    """Estimated net monthly amount and whether it was raised to the legal minimum
    (art. 31 ust. 3a – the allowance is topped up to the level of the parental benefit)."""
    net = net_estimate(monthly_gross, params)
    minimum = round(params.number("minimum_maternity_benefit_net") * (1 - work_fraction), 2)
    if net < minimum:
        return minimum, True
    return net, False
