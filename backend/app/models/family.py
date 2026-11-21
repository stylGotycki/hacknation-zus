from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, JSONType


class Family(Base):
    """A family profile. `profile` holds parents, children, employment etc. as JSON;
    its shape is validated by a Pydantic model in the rules engine (E1)."""

    __tablename__ = "family"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Identifier of the (mocked) mObywatel user who owns this profile.
    owner_id: Mapped[str] = mapped_column(String(100), index=True)
    profile: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
