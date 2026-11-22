"""Creates the history of the demo accounts: calculator answers, drafts and applications.

An account that does not exist yet is filled once; accounts are never touched again, so what a user
does with them survives restarts.
"""

from datetime import UTC, date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.applications import STATUS_NOTE_PL, harvest_contacts
from app.api.parameters import parameters_valid_on
from app.api.rules import run_evaluation
from app.engine.store import rules_version
from app.forms import FORMS, missing_fields
from app.forms.prefill import suggest
from app.mocks.personas import PERSONAS
from app.models import Application, ApplicationDraft, Family
from app.rules import FamilyProfile

FILING_KEYS = (
    "first_name",
    "last_name",
    "pesel",
    "address",
    "employer_name",
    "employer_address",
    "place",
)


def _at(day: str, hour: int = 9) -> datetime:
    return datetime.combine(date.fromisoformat(day), time(hour), tzinfo=UTC)


def _suggestion(persona: dict, action: dict, db: Session, today: date):
    profile = persona["profile"]
    result = run_evaluation(db, FamilyProfile.model_validate(profile), today)
    people = persona["people"]
    suggestions = suggest(result, profile, None, people)
    for s in suggestions:
        if s.form_code == action["form"] and s.person == action["person"]:
            return s
    raise ValueError(f"{persona['id']}: no suggestion {action['form']} for {action['person']}")


def _form_data(persona: dict, action: dict, db: Session, today: date) -> dict:
    s = _suggestion(persona, action, db, today)
    data = {**persona["people"][action["person"]], **s.prefill}
    if action["form"] == "zus_zam":
        first, last, place = persona.get("child_name", ("", "", ""))
        data |= {
            "child_first_name": first, "child_last_name": last, "birth_place": place,
            "other_benefit": "no", "employer_event": "none", "address": data.get("address"),
        }  # fmt: skip
        kind = action.get("only_kind")
        if kind:
            for key in (
                "for_maternity",
                "for_taken_in",
                "for_supplementary",
                "for_parental",
                "for_paternity",
            ):
                data[key] = key == f"for_{kind}"
            periods = [
                p for p in run_evaluation(db, FamilyProfile.model_validate(persona["profile"]), today).timeline
                if p.person == action["person"] and p.kind == kind
            ]  # fmt: skip
            data["benefit_start"], data["benefit_end"] = (
                periods[0].start.isoformat(),
                periods[-1].end.isoformat(),
            )
    return data


def seed_personas(db: Session, today: date | None = None) -> int:
    """Returns the number of accounts created."""
    today = today or date.today()
    created = 0
    params = {p.key: p.value for p in parameters_valid_on(db, today)}
    version = rules_version(db)
    for persona in PERSONAS:
        owner = f"mobywatel-{persona['id']}"
        if db.scalar(select(Family).where(Family.owner_id == owner)):
            continue
        family = Family(
            owner_id=owner,
            profile={
                "guide_state": {"form": None, "step": -1, "profile": persona["profile"]},
                "calculated_on": persona["calculated_on"],
            },
        )
        db.add(family)
        db.flush()
        for action in persona["actions"]:
            definition = FORMS[action["form"]]
            data = _form_data(persona, action, db, today)
            if action["kind"] == "draft":
                keep = action.get("only")
                if keep:
                    data = {k: v for k, v in data.items() if k in keep}
                key = (
                    f"{action['form']}:{action['person']}"
                    if len(definition.roles) > 1
                    else action["form"]
                )
                harvest_contacts(family, definition, data)
                db.add(
                    ApplicationDraft(
                        family_id=family.id, form_code=key, step=action["step"], data=data
                    )
                )
                continue
            data["declaration"] = True
            missing = missing_fields(definition, data)
            if missing:
                raise ValueError(f"{persona['id']} {action['form']}: missing {missing}")
            harvest_contacts(family, definition, data)
            history = [
                {
                    "at": _at(action["filed"]).isoformat(),
                    "status": "submitted",
                    "note": STATUS_NOTE_PL["submitted"],
                }
            ]
            status = "submitted"
            who = action.get("via", "pracodawcę")
            if "in_progress" in action:
                status = "in_progress"
                note = f"{STATUS_NOTE_PL['in_progress']} (przez {who})"
                history.append(
                    {"at": _at(action["in_progress"]).isoformat(), "status": status, "note": note}
                )
            if "decided" in action:
                status = "decided"
                step = action.get("in_progress") and action["decided"]
                history.append(
                    {
                        "at": _at(step or action["decided"], 14).isoformat(),
                        "status": status,
                        "note": STATUS_NOTE_PL["decided"],
                    }
                )
            db.add(
                Application(
                    family_id=family.id,
                    form_code=action["form"],
                    status=status,
                    data=data,
                    submitted_to=definition.submitted_to,
                    history=history,
                    params_snapshot=params,
                    rules_version=version,
                    created_at=_at(action["filed"]),
                )
            )
        created += 1
    db.commit()
    return created
