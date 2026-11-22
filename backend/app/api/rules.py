from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.core.db import DbSession
from app.engine import PlanViolation, evaluate_profile
from app.engine.runtime import required_parameters
from app.engine.store import load_params, load_rules, rules_version
from app.rules import EvaluationResult, FamilyProfile

router = APIRouter(prefix="/rules", tags=["rules"])

OnDate = Annotated[
    date | None,
    Query(
        alias="date",
        description="Date the legal parameters are taken from (YYYY-MM-DD), defaults to today",
    ),
]


def run_evaluation(
    db: DbSession, profile: FamilyProfile, on: date | None = None
) -> EvaluationResult:
    """Rules and parameters from the database; a broken plan -> 422 with the reasons in Polish."""
    today = date.today()
    on = on or today
    params = load_params(db, on)
    rules = load_rules(db)
    missing = sorted(required_parameters(rules) - params.keys())
    if missing:
        raise HTTPException(
            409,
            f"Brak parametrów prawnych obowiązujących w dniu {on.isoformat()}: {', '.join(missing)}",
        )
    try:
        result, _ = evaluate_profile(
            profile, rules, params, today, params_date=on, rules_version=rules_version(db)
        )
    except PlanViolation as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result


@router.post("/evaluate", response_model=EvaluationResult)
def evaluate_family(profile: FamilyProfile, db: DbSession, on: OnDate = None) -> EvaluationResult:
    """Entitlements, amounts, timeline and risks for a family profile.

    Rules and legal parameters are read from the database (both editable in the admin panel).
    """
    return run_evaluation(db, profile, on)
