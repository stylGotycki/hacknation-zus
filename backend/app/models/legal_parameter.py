from datetime import date
from typing import Any

from sqlalchemy import Date, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, JSONType


class LegalParameter(Base):
    """A legal constant (weeks, rates, thresholds) with a validity period.

    The rules engine never hardcodes numbers: it asks for parameters valid on a given date.
    When the law changes, a new row is added with a new `valid_from` and the old row
    gets `valid_to` set – both versions stay, so past cases are still computed correctly.
    """

    __tablename__ = "legal_parameter"
    __table_args__ = (
        UniqueConstraint("key", "valid_from", name="uq_legal_parameter_key_valid_from"),
        Index("ix_legal_parameter_key", "key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100))
    value: Mapped[Any] = mapped_column(JSONType)
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    description_pl: Mapped[str] = mapped_column(Text, default="")
    legal_basis: Mapped[str] = mapped_column(Text, default="")
