from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.parameters import parameters_valid_on
from app.core.db import DbSession
from app.rules import (
    EvaluationResult,
    FamilyProfile,
    MissingParameterError,
    Params,
    PlanError,
    evaluate,
)

router = APIRouter(prefix="/rules", tags=["rules"])

OnDate = Annotated[
    date | None,
    Query(
        alias="date",
        description="Date the legal parameters are taken from (YYYY-MM-DD), defaults to today",
    ),
]


@router.post("/evaluate", response_model=EvaluationResult)
def evaluate_family(profile: FamilyProfile, db: DbSession, on: OnDate = None) -> EvaluationResult:
    """Entitlements, amounts, timeline and risks for a family profile.

    Legal parameters are read from the database for the given date, so a past case is computed
    with the law that applied then.
    """
    on = on or date.today()
    params = Params.from_rows(parameters_valid_on(db, on), on)
    try:
        return evaluate(profile, params)
    except PlanError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except MissingParameterError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
