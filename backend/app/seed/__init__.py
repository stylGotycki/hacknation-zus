"""Seed data. Run manually with `python -m app.seed` (or `make seed`)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LegalParameter
from app.seed.parameters_2026 import all_rows


def seed_parameters(db: Session) -> int:
    """Insert or update legal parameters. Idempotent: matched by (key, valid_from).

    Returns the number of rows inserted or changed.
    """
    changed = 0
    for row in all_rows():
        existing = db.scalar(
            select(LegalParameter).where(
                LegalParameter.key == row["key"], LegalParameter.valid_from == row["valid_from"]
            )
        )
        if existing is None:
            db.add(LegalParameter(**row))
            changed += 1
            continue
        for field, value in row.items():
            if getattr(existing, field) != value:
                setattr(existing, field, value)
                changed += 1
    db.commit()
    return changed
