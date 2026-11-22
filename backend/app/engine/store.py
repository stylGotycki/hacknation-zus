"""Rules and parameters from the database, in the shape the runtime needs."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.engine.runtime import RuleDef
from app.models import Rule

RULE_FIELDS = (
    "code",
    "kind",
    "title_pl",
    "group_pl",
    "order",
    "condition",
    "expression",
    "start",
    "rate",
    "work",
    "person",
    "period_kind",
    "text_pl",
    "severity",
    "benefit",
    "periods",
    "status",
    "payer",
    "apply_to_pl",
    "deadline_kind",
    "legal_basis",
    "source",
    "description_pl",
    "active",
)


def to_def(row: Rule | dict[str, Any]) -> RuleDef:
    get = row.get if isinstance(row, dict) else (lambda k, d=None: getattr(row, k, d))
    data = {f: get(f) for f in RULE_FIELDS}
    data = {k: v for k, v in data.items() if v is not None}
    data["periods"] = list(data.get("periods") or [])
    data["active"] = bool(get("active", True) if get("active", True) is not None else True)
    return RuleDef(**data)


def rule_dict(row: Rule) -> dict[str, Any]:
    return {f: getattr(row, f) for f in RULE_FIELDS}


def load_rules(db: Session) -> list[RuleDef]:
    return [to_def(r) for r in db.scalars(select(Rule).order_by(Rule.order, Rule.code))]


def rules_version(db: Session) -> str | None:
    latest = db.scalar(select(func.max(Rule.updated_at)))
    return latest.isoformat(timespec="seconds") if latest else None


def load_params(db: Session, on: date) -> dict[str, Any]:
    from app.api.parameters import parameters_valid_on

    return {row.key: row.value for row in parameters_valid_on(db, on)}
