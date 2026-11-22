from datetime import UTC, date, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.parameters import parameters_valid_on
from app.core.db import DbSession
from app.engine.store import rules_version
from app.forms import FORMS, FormDefinition, missing_fields
from app.forms.definitions import role_of
from app.forms.prefill import Suggestion, suggest
from app.models import Application, ApplicationDraft, Family
from app.rules import FamilyProfile

router = APIRouter(tags=["applications"])

# Until the mObywatel mock (E7) provides real identities, the browser sends any stable id.
OwnerId = Annotated[str, Header(alias="X-Owner-Id")]
OptionalOwner = Annotated[str | None, Header(alias="X-Owner-Id")]

STATUS_FLOW = ["submitted", "in_progress", "decided"]
STATUS_NOTE_PL = {
    "submitted": "Wniosek złożony",
    "in_progress": "Wniosek przyjęty do rozpatrzenia",
    "decided": "Sprawa rozpatrzona – świadczenie przyznane",
}


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _family(db: DbSession, owner: str) -> Family:
    family = db.scalar(select(Family).where(Family.owner_id == owner))
    if family is None:
        family = Family(owner_id=owner, profile={})
        db.add(family)
        db.commit()
    return family


def _definition(code: str) -> FormDefinition:
    """Accepts a form code or a draft key `code:role` (one draft per form and parent)."""
    code = code.split(":", 1)[0]
    if code not in FORMS:
        raise HTTPException(404, f"Unknown form: {code}")
    return FORMS[code]


# --- Form definitions --------------------------------------------------------------------


@router.get("/forms", response_model=list[FormDefinition])
def list_forms() -> list[FormDefinition]:
    return list(FORMS.values())


@router.get("/forms/{code}", response_model=FormDefinition)
def get_form(code: str) -> FormDefinition:
    return _definition(code)


def identity_of(owner: str | None) -> dict | None:
    """The logged-in mObywatel citizen: name, PESEL and which parent they are (for prefilling)."""
    from app.mocks import data
    from app.seed.scenarios import load_scenarios

    if not owner or not owner.startswith("mobywatel-"):
        return None
    citizen_id = owner.removeprefix("mobywatel-")
    scenario = next((s for s in load_scenarios() if s["id"] == citizen_id), None)
    if scenario is None or citizen_id not in data.CITIZENS:
        return None
    role, _ = data.parent_data(scenario["profile"])
    return {**data.CITIZENS[citizen_id], "role": role}


@router.post("/applications/suggestions", response_model=list[Suggestion])
def suggestions(
    profile: FamilyProfile, db: DbSession, owner: OptionalOwner = None, on: date | None = None
) -> list[Suggestion]:
    """Applications the family should file, prefilled from the calculation (and the citizen's identity)."""
    from app.api.rules import run_evaluation

    result = run_evaluation(db, profile, on)
    return suggest(result, profile.model_dump(mode="json"), identity_of(owner))


# --- Drafts ------------------------------------------------------------------------------


class DraftIn(BaseModel):
    step: int = 0
    data: dict[str, Any] = {}


class DraftOut(DraftIn):
    id: int
    form_code: str
    updated_at: datetime | None = None


@router.get("/drafts", response_model=list[DraftOut])
def list_drafts(owner: OwnerId, db: DbSession) -> list[ApplicationDraft]:
    family = _family(db, owner)
    return list(
        db.scalars(
            select(ApplicationDraft)
            .where(ApplicationDraft.family_id == family.id)
            .order_by(ApplicationDraft.updated_at.desc())
        )
    )


@router.put("/drafts/{code}", response_model=DraftOut)
def save_draft(code: str, body: DraftIn, owner: OwnerId, db: DbSession) -> ApplicationDraft:
    """One draft per form and family: saving again overwrites it."""
    _definition(code)
    family = _family(db, owner)
    draft = db.scalar(
        select(ApplicationDraft).where(
            ApplicationDraft.family_id == family.id, ApplicationDraft.form_code == code
        )
    )
    if draft is None:
        draft = ApplicationDraft(family_id=family.id, form_code=code)
        db.add(draft)
    draft.step, draft.data = body.step, body.data
    db.commit()
    db.refresh(draft)
    return draft


@router.delete("/drafts/{code}", status_code=204)
def delete_draft(code: str, owner: OwnerId, db: DbSession) -> None:
    family = _family(db, owner)
    draft = db.scalar(
        select(ApplicationDraft).where(
            ApplicationDraft.family_id == family.id, ApplicationDraft.form_code == code
        )
    )
    if draft is not None:
        db.delete(draft)
        db.commit()


# --- Applications ------------------------------------------------------------------------


class ApplicationIn(BaseModel):
    form_code: str
    data: dict[str, Any]
    draft_key: str | None = None  # the draft to remove after sending


class HistoryEntry(BaseModel):
    at: str
    status: str
    note: str


class ApplicationOut(BaseModel):
    id: int
    form_code: str
    title_pl: str
    person: str | None = None  # which parent filed it
    fulfils: list[str] = []  # deadline rules it fulfils (the timeline replaces their points)
    status: str
    submitted_to: str | None
    data: dict[str, Any]
    history: list[HistoryEntry]
    created_at: datetime | None = None
    params_count: int = 0
    rules_version: str | None = None


def _out(app: Application) -> ApplicationOut:
    return ApplicationOut(
        id=app.id,
        form_code=app.form_code,
        title_pl=FORMS[app.form_code].title_pl if app.form_code in FORMS else app.form_code,
        person=role_of(FORMS[app.form_code], app.data) if app.form_code in FORMS else None,
        fulfils=FORMS[app.form_code].fulfils if app.form_code in FORMS else [],
        status=app.status,
        submitted_to=app.submitted_to,
        data=app.data,
        history=[HistoryEntry(**h) for h in app.history],
        created_at=app.created_at,
        params_count=len(app.params_snapshot or {}),
        rules_version=app.rules_version,
    )


@router.get("/applications", response_model=list[ApplicationOut])
def list_applications(owner: OwnerId, db: DbSession) -> list[ApplicationOut]:
    family = _family(db, owner)
    rows = db.scalars(
        select(Application)
        .where(Application.family_id == family.id)
        .order_by(Application.id.desc())
    )
    return [_out(a) for a in rows]


@router.post("/applications", response_model=ApplicationOut, status_code=201)
def submit_application(body: ApplicationIn, owner: OwnerId, db: DbSession) -> ApplicationOut:
    """Validates the required fields, stores the application and removes the draft."""
    definition = _definition(body.form_code)
    missing = missing_fields(definition, body.data)
    if missing:
        raise HTTPException(422, f"Uzupełnij wymagane pola: {', '.join(missing)}")
    family = _family(db, owner)
    application = Application(
        family_id=family.id,
        form_code=body.form_code,
        status="submitted",
        data=body.data,
        params_snapshot={p.key: p.value for p in parameters_valid_on(db, date.today())},
        rules_version=rules_version(db),
        submitted_to=definition.submitted_to,
        history=[{"at": _now(), "status": "submitted", "note": STATUS_NOTE_PL["submitted"]}],
    )
    db.add(application)
    draft = db.scalar(
        select(ApplicationDraft).where(
            ApplicationDraft.family_id == family.id,
            ApplicationDraft.form_code == (body.draft_key or body.form_code),
        )
    )
    if draft is not None:
        db.delete(draft)
    db.commit()
    return _out(application)


# --- Saved state of the guide (calculator answers and step) ------------------------------


class GuideState(BaseModel):
    form: dict[str, Any] | None = None  # calculator answers
    step: int = 0
    profile: dict[str, Any] | None = None  # family profile behind the last result
    updated_at: datetime | None = None


@router.get("/state", response_model=GuideState)
def get_state(owner: OwnerId, db: DbSession) -> GuideState:
    """What the user entered last time, so they continue where they stopped after logging in again."""
    family = _family(db, owner)
    saved = (family.profile or {}).get("guide_state") or {}
    return GuideState(**saved, updated_at=family.updated_at if saved else None)


@router.put("/state", response_model=GuideState)
def put_state(body: GuideState, owner: OwnerId, db: DbSession) -> GuideState:
    family = _family(db, owner)
    family.profile = {
        **(family.profile or {}),
        "guide_state": body.model_dump(mode="json", exclude={"updated_at"}),
    }
    db.commit()
    db.refresh(family)
    return GuideState(**family.profile["guide_state"], updated_at=family.updated_at)


def merge_owner(db: DbSession, source: str, target: str) -> None:
    """After logging in, the guest's work (state, drafts, applications) moves to the citizen's account.

    The account wins: a draft of the same form or a saved calculator state already there is kept.
    """
    if not source or source == target:
        return
    guest = db.scalar(select(Family).where(Family.owner_id == source))
    if guest is None:
        return
    account = _family(db, target)
    if not (account.profile or {}).get("guide_state") and (guest.profile or {}).get("guide_state"):
        account.profile = {**(account.profile or {}), "guide_state": guest.profile["guide_state"]}
    have = set(
        db.scalars(
            select(ApplicationDraft.form_code).where(ApplicationDraft.family_id == account.id)
        )
    )
    for draft in db.scalars(select(ApplicationDraft).where(ApplicationDraft.family_id == guest.id)):
        if draft.form_code not in have:
            draft.family_id = account.id
    for application in db.scalars(select(Application).where(Application.family_id == guest.id)):
        application.family_id = account.id
    db.flush()
    db.delete(guest)
    db.commit()


@router.post("/applications/{application_id}/advance", response_model=ApplicationOut)
def advance_application(application_id: int, owner: OwnerId, db: DbSession) -> ApplicationOut:
    """Demo helper: moves the application to the next stage as the payer would."""
    family = _family(db, owner)
    application = db.get(Application, application_id)
    if application is None or application.family_id != family.id:
        raise HTTPException(404, "Application not found")
    index = STATUS_FLOW.index(application.status) if application.status in STATUS_FLOW else -1
    if index + 1 >= len(STATUS_FLOW):
        raise HTTPException(409, "Application is already decided")
    nxt = STATUS_FLOW[index + 1]
    application.status = nxt
    who = {"zus": "ZUS", "registry": "urząd stanu cywilnego"}.get(
        application.submitted_to or "", "pracodawcę"
    )
    note = STATUS_NOTE_PL[nxt] + (f" (przez {who})" if nxt == "in_progress" else "")
    application.history = [*application.history, {"at": _now(), "status": nxt, "note": note}]
    db.commit()
    return _out(application)
