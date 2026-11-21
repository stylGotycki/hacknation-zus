"""E1 – rules engine: pure functions (family profile + legal parameters -> entitlements).

Keep this package free of FastAPI and database code so rules are easy to unit-test.

    from app.rules import FamilyProfile, Params, evaluate
    result = evaluate(FamilyProfile(...), Params.from_rows(rows, on=date(2026, 11, 21)))
"""

from app.rules.engine import evaluate
from app.rules.leaves import PlanError
from app.rules.models import EvaluationResult, FamilyProfile
from app.rules.params import MissingParameterError, Params

__all__ = [
    "EvaluationResult",
    "FamilyProfile",
    "MissingParameterError",
    "Params",
    "PlanError",
    "evaluate",
]
