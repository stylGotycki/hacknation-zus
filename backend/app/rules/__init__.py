"""API types of the rules engine (input `FamilyProfile`, output `EvaluationResult`).

The engine itself is generic and lives in `app.engine`: rules are data stored in the database
(seed: `app/seed/rules/`), evaluated by `app.engine.service.evaluate_profile`.
"""

from app.rules.models import EvaluationResult, FamilyProfile

__all__ = ["EvaluationResult", "FamilyProfile"]
