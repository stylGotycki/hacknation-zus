from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.db import DbSession
from app.models import LegalParameter

router = APIRouter(prefix="/parameters", tags=["parameters"])

# `?date=RRRR-MM-DD`; named `on` in Python so it does not shadow the `date` type.
OnDate = Annotated[
    date | None, Query(alias="date", description="Date (YYYY-MM-DD), defaults to today")
]


class ParameterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: Any
    valid_from: date
    valid_to: date | None
    description_pl: str
    legal_basis: str
    label_pl: str = ""
    group_pl: str = ""
    unit: str = "number"
    value_labels: dict[str, str] = {}


class ParametersResponse(BaseModel):
    date: date
    parameters: list[ParameterOut]


def parameters_valid_on(db: Session, on: date) -> list[LegalParameter]:
    """All parameters whose validity period contains `on`. Reused by the rules engine (E1)."""
    stmt = (
        select(LegalParameter)
        .where(LegalParameter.valid_from <= on)
        .where(or_(LegalParameter.valid_to.is_(None), LegalParameter.valid_to >= on))
        .order_by(LegalParameter.key)
    )
    return list(db.scalars(stmt))


@router.get("", response_model=ParametersResponse)
def list_parameters(db: DbSession, on: OnDate = None) -> ParametersResponse:
    """Legal parameters valid on the given date."""
    on = on or date.today()
    return ParametersResponse(date=on, parameters=parameters_valid_on(db, on))


@router.get("/{key}", response_model=ParameterOut)
def get_parameter(key: str, db: DbSession, on: OnDate = None) -> LegalParameter:
    """A single parameter valid on the given date."""
    on = on or date.today()
    for param in parameters_valid_on(db, on):
        if param.key == key:
            return param
    raise HTTPException(status_code=404, detail=f"No parameter '{key}' valid on {on}")
