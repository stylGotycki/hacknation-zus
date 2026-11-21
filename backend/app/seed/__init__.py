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
    rows = all_rows()
    seed_versions = {(r["key"], r["valid_from"]) for r in rows}
    # A key with a version that is not in the seed was edited in the admin panel: the seed must
    # not overwrite (or reopen) what an administrator changed.
    admin_keys = {
        key
        for key, valid_from in db.execute(select(LegalParameter.key, LegalParameter.valid_from))
        if (key, valid_from) not in seed_versions
    }
    for row in rows:
        if row["key"] in admin_keys:
            continue
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
