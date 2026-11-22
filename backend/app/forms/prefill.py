"""Suggests which applications a result needs and fills them with data from the calculation."""

from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.rules.models import EvaluationResult, LeavePeriod

Person = Literal["mother", "father"]

LEAVE_FORM = {
    "maternity": "leave_maternity",
    "parental": "leave_parental",
    "paternity": "leave_paternity",
}
# Benefit (rule) codes of the deadlines that belong to each leave form.
BENEFIT_PREFIX = {"maternity": "macierzynski", "parental": "rodzicielski", "paternity": "ojcowski"}
LEAVE_KINDS = ("maternity", "supplementary", "parental", "paternity")


class Suggestion(BaseModel):
    form_code: str
    person: Person
    title_pl: str
    submitted_to: Literal["employer", "zus"]
    deadline: date | None = None
    days_left: int | None = None
    prefill: dict


def _is_employee(profile_person: dict | None) -> bool:
    return bool(profile_person) and profile_person.get("employment") == "employee"


def _deadline_for(
    result: EvaluationResult, person: str, kind: str
) -> tuple[date | None, int | None]:
    for d in result.deadlines:
        if (
            d.person == person
            and d.kind == "apply"
            and d.benefit_code
            and d.benefit_code.startswith(BENEFIT_PREFIX[kind])
            and d.days_left >= 0
        ):
            return d.due, d.days_left
    return None, None


def suggest(result: EvaluationResult, profile: dict) -> list[Suggestion]:
    """One suggestion per leave request of an employee and one ZAM for every other insured parent."""
    out: list[Suggestion] = []
    for person in ("mother", "father"):
        periods = sorted(
            (p for p in result.timeline if p.person == person and p.paid and p.kind in LEAVE_KINDS),
            key=lambda p: p.start,
        )
        if not periods:
            continue
        parent = profile.get(person)
        if _is_employee(parent):
            for kind in ("maternity", "parental", "paternity"):
                of_kind = [p for p in periods if p.kind == kind]
                if not of_kind:
                    continue
                first, last = of_kind[0], of_kind[-1]
                due, left = _deadline_for(result, person, kind)
                out.append(
                    Suggestion(
                        form_code=LEAVE_FORM[kind],
                        person=person,
                        title_pl=_title(kind, person),
                        submitted_to="employer",
                        deadline=due,
                        days_left=left,
                        prefill=_leave_data(result, kind, first, last, parent),
                    )
                )
        else:
            out.append(
                Suggestion(
                    form_code="zus_zam",
                    person=person,
                    title_pl=f"{'Mama' if person == 'mother' else 'Tata'}: wniosek o zasiłek macierzyński (ZAM)",
                    submitted_to="zus",
                    prefill={
                        "child_date": result.event_date.isoformat(),
                        "children_count": (profile.get("child") or {}).get("children_count", 1),
                        "for_maternity": any(p.kind == "maternity" for p in periods),
                        "for_parental": any(p.kind == "parental" for p in periods),
                        "for_paternity": any(p.kind == "paternity" for p in periods),
                        "benefit_start": periods[0].start.isoformat(),
                        "benefit_end": periods[-1].end.isoformat(),
                    },
                )
            )
    return out


def _title(kind: str, person: str) -> str:
    name = "Mama" if person == "mother" else "Tata"
    label = {
        "maternity": "wniosek o urlop macierzyński",
        "parental": "wniosek o urlop rodzicielski",
        "paternity": "wniosek o urlop ojcowski",
    }[kind]
    return f"{name}: {label}"


def _leave_data(
    result: EvaluationResult, kind: str, first: LeavePeriod, last: LeavePeriod, parent: dict | None
) -> dict:
    data: dict = {
        "child_date": result.event_date.isoformat(),
        "leave_start": first.start.isoformat(),
        "leave_end": last.end.isoformat(),
    }
    if kind == "maternity":
        data["with_parental"] = any(
            p.person == first.person and p.kind == "parental" for p in result.timeline
        )
    if kind == "parental":
        data["part_number"] = 1
        data["work_percent"] = round(first.work_fraction * 100)
    return data
