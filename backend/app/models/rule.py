from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, JSONType


class Rule(Base):
    """A rule of the guide (value, period, benefit, message or plan check) – see app/engine/runtime.py.

    Expressions are plain text in the rule language; dependencies between rules are read from
    them, so admins can add or change rules without touching code.
    """

    __tablename__ = "rule"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(20))
    title_pl: Mapped[str] = mapped_column(Text, default="")
    group_pl: Mapped[str] = mapped_column(String(100), default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
    condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    expression: Mapped[str | None] = mapped_column(Text, nullable=True)
    start: Mapped[str | None] = mapped_column(Text, nullable=True)
    rate: Mapped[str | None] = mapped_column(Text, nullable=True)
    work: Mapped[str | None] = mapped_column(Text, nullable=True)
    person: Mapped[str | None] = mapped_column(String(200), nullable=True)
    period_kind: Mapped[str | None] = mapped_column(String(40), nullable=True)
    text_pl: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str | None] = mapped_column(String(10), nullable=True)
    benefit: Mapped[str | None] = mapped_column(String(80), nullable=True)
    periods: Mapped[list[str]] = mapped_column(JSONType, default=list)
    status: Mapped[str | None] = mapped_column(Text, nullable=True)
    payer: Mapped[str | None] = mapped_column(Text, nullable=True)
    apply_to_pl: Mapped[str] = mapped_column(Text, default="")
    deadline_kind: Mapped[str | None] = mapped_column(String(10), nullable=True)
    legal_basis: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(20), default="")
    description_pl: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    # True once an administrator changed the rule: the seed no longer overwrites it.
    modified: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RuleHistory(Base):
    """Previous versions of a rule (audit trail of admin changes)."""

    __tablename__ = "rule_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    note: Mapped[str] = mapped_column(Text, default="")
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
