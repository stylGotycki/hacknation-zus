"""Deadlines: how much time is left to file each application or to use each leave."""

from datetime import date, timedelta

from app.rules.context import Context
from app.rules.dates import add_months
from app.rules.models import AveragedRateComparison, Deadline

SOON_DAYS = 14


def _status(days_left: int) -> str:
    if days_left < 0:
        return "overdue"
    return "soon" if days_left <= SOON_DAYS else "open"


def _deadline(
    code: str,
    person: str,
    kind: str,
    title: str,
    due: date,
    today: date,
    note: str,
    benefit_code: str | None = None,
) -> Deadline:
    left = (due - today).days
    return Deadline(
        code=code,
        person=person,  # type: ignore[arg-type]
        kind=kind,  # type: ignore[arg-type]
        title_pl=title,
        due=due,
        days_left=left,
        status=_status(left),  # type: ignore[arg-type]
        note_pl=note,
        benefit_code=benefit_code,
    )


def build_deadlines(ctx: Context, averaged: AveragedRateComparison | None) -> list[Deadline]:
    out: list[Deadline] = []
    today = ctx.today
    params = ctx.params
    leads = params.table("application_lead_days")

    # --- Leave applications (to the employer / payer) ----------------------------------------
    for period in ctx.periods:
        if period.kind not in leads or period.start <= today:
            continue
        lead = int(leads[period.kind])
        due = period.start - timedelta(days=lead)
        late = " Termin już minął – złóż wniosek jak najszybciej i ustal z pracodawcą późniejszy początek urlopu."
        out.append(
            _deadline(
                f"apply_{period.id}",
                period.person,
                "apply",
                f"Wniosek: {period.label_pl.lower()}",
                due,
                today,
                f"Wniosek trzeba złożyć co najmniej {lead} dni przed rozpoczęciem urlopu "
                f"({period.start:%d.%m.%Y})." + (late if due < today else ""),
                f"{period.kind}_allowance_{period.person}",
            )
        )

    # --- Averaged 81.5% rate ------------------------------------------------------------------
    already = ctx.averaged_applied
    if averaged is not None and not already:
        note = (
            f"Wniosek o wypłatę zasiłku za cały okres macierzyńskiego i rodzicielskiego po stałej stawce "
            f"81,5% – {params.integer('averaged_application_deadline_days')} dni od porodu."
        )
        if not averaged.still_possible:
            note += " Termin minął – zostają stawki 100% i 70%."
        out.append(
            _deadline(
                "apply_averaged_rate",
                "mother",
                "apply",
                "Wniosek o stałą stawkę 81,5%",
                averaged.deadline,
                today,
                note,
                "maternity_allowance_mother",
            )
        )

    # --- Last day to use the leave ---------------------------------------------------------------
    if ctx.ent.parental_deadline is not None and (
        ctx.plan.mother_parental or ctx.plan.father_parental
    ):
        out.append(
            _deadline(
                "use_by_parental",
                "family",
                "use_by",
                "Ostatni dzień na wykorzystanie urlopu rodzicielskiego",
                ctx.ent.parental_deadline,
                today,
                "Do końca roku kalendarzowego, w którym dziecko skończy 6 lat.",
            )
        )
    if (
        ctx.ent.paternity_deadline is not None
        and ctx.ent.paternity_days
        and ctx.insured("father")
        and "father" in ctx.parents
    ):
        out.append(
            _deadline(
                "use_by_paternity",
                "father",
                "use_by",
                "Ostatni dzień na wykorzystanie urlopu ojcowskiego",
                ctx.ent.paternity_deadline,
                today,
                "Po tym terminie prawo do urlopu ojcowskiego wygasa.",
            )
        )

    # --- Parental benefit ("kosiniakowe") ------------------------------------------------------
    if not any(ctx.insured(p) for p in ctx.parents) and ctx.ent.surviving_children > 0:
        months = params.integer("parental_benefit_application_months")
        due = add_months(ctx.event, months)
        out.append(
            _deadline(
                "apply_parental_benefit",
                "family",
                "apply",
                "Wniosek o świadczenie rodzicielskie",
                due,
                today,
                f"Wniosek złożony w ciągu {months} miesięcy od porodu daje świadczenie od dnia porodu; "
                "później – dopiero od miesiąca złożenia wniosku.",
                "parental_benefit",
            )
        )

    out.sort(key=lambda d: d.due)
    return out
