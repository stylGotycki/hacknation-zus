from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, JSONType


class Application(Base):
    """A submitted application (e.g. ZAM, parental leave request). Logic in E6/E8."""

    __tablename__ = "application"

    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("family.id", ondelete="CASCADE"), index=True)
    form_code: Mapped[str] = mapped_column(String(50))  # e.g. "ZUS_ZAM"
    status: Mapped[str] = mapped_column(String(30), default="submitted")
    data: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    # Who handles it: "ZUS" or "employer".
    submitted_to: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # List of {"at": ..., "status": ..., "note": ...} entries – the workflow trail.
    history: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
