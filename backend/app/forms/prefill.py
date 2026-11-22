"""Which applications a result needs, prefilled with data from the calculation.

Every suggestion is tied to the deadline rules (termin) it fulfils, so the timeline can replace
a deadline point with the filed application and show advice when the deadline has passed.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.forms.definitions import FORMS
from app.rules.models import Deadline, EvaluationResult, LeavePeriod

Person = Literal["mother", "father"]
PERSON_PL = {"mother": "Mama", "father": "Tata"}
# Kept for other modules: benefit (rule) code prefixes and leave kinds shown on the timeline.
BENEFIT_PREFIX = {"maternity": "macierzynski", "parental": "rodzicielski", "paternity": "ojcowski"}
LEAVE_KINDS = ("maternity", "supplementary", "parental", "paternity")
ROLE_SUFFIX = {"mother": "mama", "father": "tata"}


class Suggestion(BaseModel):
    form_code: str
    person: Person
    title_pl: str
    submitted_to: Literal["employer", "zus", "registry"]
    deadline: date | None = None
    days_left: int | None = None
    status: Literal["open", "soon", "overdue"] | None = None
    late_pl: str | None = None
    deadline_codes: list[str] = []
    prefill: dict


def _is_employee(parent: dict | None) -> bool:
    return bool(parent) and parent.get("employment") == "employee"


def _deadline(result: EvaluationResult, code: str) -> Deadline | None:
    return next((d for d in result.deadlines if d.code == code), None)


def _iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


def suggest(
    result: EvaluationResult,
    profile: dict,
    identity: dict | None = None,
    known: dict[str, dict] | None = None,
) -> list[Suggestion]:
    """`identity` = the logged-in citizen; `known` = data of both parents typed in earlier forms."""
    out: list[Suggestion] = []
    child = profile.get("child") or {}
    situation = child.get("situation") or "birth"
    birth = child.get("birth_date")

    def add(code: str, person: Person, deadline_code: str | None, data: dict) -> None:
        definition = FORMS[code]
        d = _deadline(result, deadline_code) if deadline_code else None
        data = {k: v for k, v in data.items() if v not in (None, "")}
        if len(definition.roles) > 1:
            data["applicant_role"] = person
        field_keys = {f.key for step in definition.steps for f in step.fields}
        for key, value in (known or {}).get(person, {}).items():
            if key in field_keys:
                data.setdefault(key, value)
        other = "father" if person == "mother" else "mother"
        for form_key, key in (
            ("other_first_name", "first_name"),
            ("other_last_name", "last_name"),
            ("other_pesel", "pesel"),
            ("other_address", "address"),
        ):
            if (known or {}).get(other, {}).get(key) and any(
                f.key == form_key for s in definition.steps for f in s.fields
            ):
                data.setdefault(form_key, known[other][key])
        title = definition.title_pl[0].lower() + definition.title_pl[1:]
        out.append(
            Suggestion(
                form_code=code,
                person=person,
                title_pl=f"{PERSON_PL[person]}: {title}",
                submitted_to=definition.submitted_to,
                deadline=d.due if d else None,
                days_left=d.days_left if d else None,
                status=d.status if d else None,
                late_pl=d.late_pl if d else None,
                deadline_codes=[deadline_code] if deadline_code else [],
                prefill=data,
            )
        )

    for person in ("mother", "father"):
        role = ROLE_SUFFIX[person]
        periods = sorted(
            (p for p in result.timeline if p.person == person and p.paid and p.kind in LEAVE_KINDS),
            key=lambda p: p.start,
        )
        if not periods:
            continue
        of = {k: [p for p in periods if p.kind == k] for k in LEAVE_KINDS}
        child_data = {
            "child_birth_date": birth,
            "situation": situation,
            "placement_date": child.get("placement_date"),
        }
        if not _is_employee(profile.get(person)):
            add(
                "zus_zam",
                person,
                f"t_rodzicielski_{role}"
                if of["parental"]
                else ("t_ojcowski" if of["paternity"] else None),
                {
                    **child_data,
                    "due_date": child.get("due_date") if not birth else None,
                    "for_maternity": bool(of["maternity"]) and situation == "birth",
                    "for_taken_in": bool(of["maternity"]) and situation != "birth",
                    "for_supplementary": bool(of["supplementary"]),
                    "for_parental": bool(of["parental"]),
                    "for_paternity": bool(of["paternity"]),
                    "benefit_start": periods[0].start.isoformat(),
                    "benefit_end": periods[-1].end.isoformat(),
                    "full_leave": bool((profile.get("plan") or {}).get("averaged_rate")),
                    "other_benefit": "no",
                    "employer_event": "none",
                },
            )
            continue

        maternity = of["maternity"]
        if maternity and situation != "birth":
            add("leave_taken_in", person, "t_na_warunkach", {**child_data, **_span(maternity)})
        elif maternity and person == "mother":
            if _deadline(result, "t_mac_przed"):
                first = maternity[0]
                add(
                    "leave_maternity_before",
                    person,
                    "t_mac_przed",
                    {"leave_start": first.start.isoformat(), "due_date": child.get("due_date")},
                )
            father_maternity = [
                p for p in result.timeline if p.person == "father" and p.kind == "maternity"
            ]
            if father_maternity:
                add(
                    "leave_maternity_resignation",
                    person,
                    "t_rezygnacja",
                    {"return_date": father_maternity[0].start.isoformat()},
                )
        elif maternity and person == "father":
            add(
                "leave_maternity_father",
                person,
                "t_tata_macierzynski",
                {**child_data, **_span(maternity)},
            )
        if of["supplementary"]:
            add(
                "leave_supplementary",
                person,
                "t_uzupelniajacy",
                {
                    **_span(of["supplementary"]),
                    "maternity_end": _iso(_last_end(result, "maternity")),
                },
            )
        if of["parental"]:
            parental = of["parental"]
            add(
                "leave_parental",
                person,
                f"t_rodzicielski_{role}",
                {
                    **child_data,
                    **_span(parental),
                    "used_parts": 0,
                    "used_so_far": "nie korzystałem/am",
                    "other_parent": "none",
                },
            )
            working = [p for p in parental if p.work_fraction > 0]
            if working:
                add(
                    "parental_work",
                    person,
                    f"t_praca_{role}",
                    {
                        "work_time": f"{round(working[0].work_fraction * 100)}% etatu",
                        "work_start": working[0].start.isoformat(),
                        "work_end": working[-1].end.isoformat(),
                        "extension_work": "no",
                    },
                )
        if of["paternity"]:
            add(
                "leave_paternity",
                person,
                "t_ojcowski",
                {**_span(of["paternity"]), "adopted": situation == "adoption", "used_before": "no"},
            )
    return out


def _span(periods: list[LeavePeriod]) -> dict:
    return {"leave_start": periods[0].start.isoformat(), "leave_end": periods[-1].end.isoformat()}


def _last_end(result: EvaluationResult, kind: str) -> date | None:
    ends = [p.end for p in result.timeline if p.kind == kind and p.person == "mother"]
    return max(ends) if ends else None
