from datetime import date, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.applications import STATUS_FLOW, STATUS_NOTE_PL, _now, _out
from app.api.parameters import ParameterOut
from app.core.config import get_settings
from app.core.db import DbSession
from app.forms import FORMS
from app.models import Application, Family, LegalParameter
from app.seed.parameters_2026 import all_rows


def require_admin(x_admin_token: Annotated[str | None, Header()] = None) -> None:
    if x_admin_token != get_settings().admin_token:
        raise HTTPException(401, "Invalid admin token")


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/check")
def check() -> dict[str, bool]:
    """Lets the panel verify the password."""
    return {"ok": True}


# --- Legal parameters --------------------------------------------------------------------


class ParameterRow(ParameterOut):
    from_seed: bool
    current: bool


@router.get("/parameters", response_model=list[ParameterRow])
def all_versions(db: DbSession) -> list[ParameterRow]:
    """Every version of every parameter, newest first within a key."""
    seed_versions = {(r["key"], r["valid_from"]) for r in all_rows()}
    today = date.today()
    rows = db.scalars(
        select(LegalParameter).order_by(LegalParameter.key, LegalParameter.valid_from.desc())
    )
    return [
        ParameterRow(
            **ParameterOut.model_validate(r).model_dump(),
            from_seed=(r.key, r.valid_from) in seed_versions,
            current=r.valid_from <= today and (r.valid_to is None or r.valid_to >= today),
        )
        for r in rows
    ]


class VersionIn(BaseModel):
    value: Any
    valid_from: date
    description_pl: str | None = None
    legal_basis: str | None = None


def same_shape(old: Any, new: Any) -> bool:
    """A new value must keep the type of the old one (and the keys of a table)."""
    if isinstance(old, bool) or isinstance(new, bool):
        return isinstance(old, bool) and isinstance(new, bool)
    if isinstance(old, int | float):
        return isinstance(new, int | float)
    if isinstance(old, dict):
        return (
            isinstance(new, dict)
            and old.keys() == new.keys()
            and all(same_shape(old[k], new[k]) for k in old)
        )
    if isinstance(old, list):
        return isinstance(new, list)
    return type(old) is type(new)


@router.post("/parameters/{key}/versions", response_model=ParameterOut, status_code=201)
def add_version(key: str, body: VersionIn, db: DbSession) -> LegalParameter:
    """Adds a new version valid from a later date; the previous version ends the day before."""
    versions = list(
        db.scalars(
            select(LegalParameter)
            .where(LegalParameter.key == key)
            .order_by(LegalParameter.valid_from.desc())
        )
    )
    if not versions:
        raise HTTPException(404, f"Unknown parameter: {key}")
    latest = versions[0]
    if body.valid_from <= latest.valid_from:
        raise HTTPException(
            409,
            f"The new version must start after {latest.valid_from} (the latest existing version)",
        )
    if not same_shape(latest.value, body.value):
        raise HTTPException(422, "The new value must have the same type and keys as the current one")
    latest.valid_to = body.valid_from - timedelta(days=1)
    new = LegalParameter(
        key=key,
        value=body.value,
        valid_from=body.valid_from,
        valid_to=None,
        description_pl=body.description_pl or latest.description_pl,
        legal_basis=body.legal_basis or latest.legal_basis,
    )
    db.add(new)
    db.commit()
    return new


@router.delete("/parameters/{key}/versions/{valid_from}", status_code=204)
def delete_version(key: str, valid_from: date, db: DbSession) -> None:
    """Removes an admin-made version and reopens the previous one. Seed versions stay."""
    if (key, valid_from) in {(r["key"], r["valid_from"]) for r in all_rows()}:
        raise HTTPException(409, "Versions from the seed cannot be deleted")
    row = db.scalar(
        select(LegalParameter).where(
            LegalParameter.key == key, LegalParameter.valid_from == valid_from
        )
    )
    if row is None:
        raise HTTPException(404, "Version not found")
    previous = db.scalar(
        select(LegalParameter)
        .where(LegalParameter.key == key, LegalParameter.valid_from < valid_from)
        .order_by(LegalParameter.valid_from.desc())
    )
    db.delete(row)
    if previous is not None:
        previous.valid_to = row.valid_to
    db.commit()


# --- Applications workflow ---------------------------------------------------------------


class AdminApplication(BaseModel):
    id: int
    owner_id: str
    form_code: str
    title_pl: str
    status: str
    submitted_to: str | None
    created_at: str | None
    last_note: str | None


@router.get("/applications", response_model=list[AdminApplication])
def all_applications(db: DbSession) -> list[AdminApplication]:
    rows = db.execute(
        select(Application, Family.owner_id)
        .join(Family, Family.id == Application.family_id)
        .order_by(Application.id.desc())
    )
    out = []
    for app, owner in rows:
        record = _out(app)
        out.append(
            AdminApplication(
                id=app.id,
                owner_id=owner,
                form_code=app.form_code,
                title_pl=FORMS[app.form_code].title_pl if app.form_code in FORMS else app.form_code,
                status=app.status,
                submitted_to=app.submitted_to,
                created_at=record.created_at.isoformat() if record.created_at else None,
                last_note=record.history[-1].note if record.history else None,
            )
        )
    return out


class StatusIn(BaseModel):
    status: str
    note: str | None = None


@router.post("/applications/{application_id}/status")
def set_status(application_id: int, body: StatusIn, db: DbSession) -> dict[str, str]:
    """The payer's decision: moves an application to any stage of the flow, with a note."""
    if body.status not in STATUS_FLOW:
        raise HTTPException(422, f"Status must be one of: {', '.join(STATUS_FLOW)}")
    app = db.get(Application, application_id)
    if app is None:
        raise HTTPException(404, "Application not found")
    app.status = body.status
    app.history = [
        *app.history,
        {"at": _now(), "status": body.status, "note": body.note or STATUS_NOTE_PL[body.status]},
    ]
    db.commit()
    return {"status": app.status}
