"""Seed data. Run manually with `python -m app.seed` (or `make seed`)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LegalParameter
from app.seed.parameters_2026 import all_rows

# Parameters of the previous iteration that are not in the six sources: removed on seed.
OBSOLETE_KEYS = {
    "additional_care_allowance_weeks",
    "benefit_days_per_month",
    "care_allowance_age_limits_years",
    "health_contribution_rate",
    "income_tax_monthly_reduction",
    "income_tax_rate",
    "minimum_maternity_benefit_net",
    "parental_benefit_application_months",
    "parental_benefit_monthly",
    "parental_benefit_weeks",
    "paternity_leave_days",
    "paternity_min_part_days",
    "supplementary_leave_criteria",
}


def seed_parameters(db: Session) -> int:
    """Insert or update legal parameters. Idempotent: matched by (key, valid_from).

    Returns the number of rows inserted or changed.
    """
    changed = 0
    for old in db.scalars(select(LegalParameter).where(LegalParameter.key.in_(OBSOLETE_KEYS))):
        db.delete(old)
        changed += 1
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


def seed_rules(db: Session) -> int:
    """Insert or update rules from app/seed/rules/.

    Rules changed in the admin panel (`modified`) and rules added there are left alone.
    """
    from app.engine.store import RULE_FIELDS
    from app.models import Rule
    from app.seed.rules import all_rules

    changed = 0
    existing = {r.code: r for r in db.scalars(select(Rule))}
    for data in all_rules():
        row = existing.get(data["code"])
        values = {f: data.get(f) for f in RULE_FIELDS if f != "code"}
        values = {
            **values,
            "periods": values.get("periods") or [],
            "active": True if values.get("active") is None else values["active"],
            "text_pl": values.get("text_pl") or "",
            "title_pl": values.get("title_pl") or "",
            "group_pl": values.get("group_pl") or "",
            "apply_to_pl": values.get("apply_to_pl") or "",
            "legal_basis": values.get("legal_basis") or "",
            "source": values.get("source") or "",
            "description_pl": values.get("description_pl") or "",
            "late_text_pl": values.get("late_text_pl") or "",
            "order": values.get("order") or 0,
        }
        if row is None:
            db.add(Rule(code=data["code"], **values))
            changed += 1
            continue
        if row.modified:
            continue
        diff = {k: v for k, v in values.items() if getattr(row, k) != v}
        for k, v in diff.items():
            setattr(row, k, v)
        changed += bool(diff)
    db.commit()
    return changed
