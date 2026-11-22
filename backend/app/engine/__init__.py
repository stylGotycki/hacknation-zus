"""Generic, configurable rules engine.

expressions – safe expression language (parser, evaluator, references)
facts       – FamilyProfile -> Polish facts read by rules (+ data dictionary)
runtime     – rule definitions -> values, periods, benefits, messages (dependency graph)
service     – EvaluationResult for the API
store       – rules and parameters from the database
"""

from datetime import date
from typing import Any

from app.engine.runtime import PlanViolation, RuleDef
from app.engine.service import evaluate_profile
from app.rules.models import EvaluationResult, FamilyProfile


def seed_rule_defs() -> list[RuleDef]:
    from app.engine.store import to_def
    from app.seed.rules import all_rules

    return [to_def(r) for r in all_rules()]


def evaluate_with_seed(
    profile: FamilyProfile, today: date, overrides: dict[str, Any] | None = None
) -> EvaluationResult:
    """Evaluates with the seed rules and 2026 parameters (no database) – used by tests."""
    from app.seed.parameters_2026 import current_values

    params = {**current_values(), **(overrides or {})}
    result, _ = evaluate_profile(profile, seed_rule_defs(), params, today)
    return result


__all__ = ["PlanViolation", "RuleDef", "evaluate_profile", "evaluate_with_seed", "seed_rule_defs"]
