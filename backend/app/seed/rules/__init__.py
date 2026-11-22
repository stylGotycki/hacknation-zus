"""Rules of the guide, one module per area; `all_rules()` returns them in the order they are loaded."""

from __future__ import annotations

from app.seed.rules import (
    averaged,
    benefits,
    deadlines,
    documents,
    event,
    info,
    maternity,
    parental,
    paternity,
    plan_validation,
    pregnancy_sick,
    right,
    risks,
    supplementary,
)

# The order matters: inside a kind the position in this list is the display order.
MODULES = (
    event,
    right,
    maternity,
    averaged,
    supplementary,
    parental,
    paternity,
    pregnancy_sick,
    plan_validation,
    benefits,
    documents,
    deadlines,
    risks,
    info,
)
RULES: list[dict] = [rule for module in MODULES for rule in module.RULES]


def all_rules() -> list[dict]:
    """Rules with defaults filled in (order inside a kind follows the list)."""
    out = []
    for i, r in enumerate(RULES):
        out.append({"order": r.get("order") or i, **{k: v for k, v in r.items() if k != "order"}})
    return out
