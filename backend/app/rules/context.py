"""Values computed once per evaluation and shared by the engine modules."""

from dataclasses import dataclass, field
from datetime import date

from app.rules.eligibility import DebtState, Insurance, Payer
from app.rules.leaves import Entitlement
from app.rules.models import (
    CalculationBase,
    FamilyProfile,
    LeavePeriod,
    ParentProfile,
    Person,
)
from app.rules.params import Params


@dataclass
class ResolvedPlan:
    """The plan after defaults and validation; all numbers are weeks unless noted."""

    before_birth: int
    mother_maternity_total: int  # includes the weeks before birth
    father_maternity: int
    supplementary: int
    supplementary_taker: Person | None
    mother_parental: int
    father_parental: int
    father_reserved: int
    mother_work_fraction: float
    father_work_fraction: float
    paternity_parts: int
    notes_pl: list[str] = field(default_factory=list)


@dataclass
class Context:
    profile: FamilyProfile
    params: Params
    today: date
    event: date
    event_is_estimate: bool
    ent: Entitlement
    parents: dict[Person, ParentProfile]
    insurance: dict[Person, Insurance]
    bases: dict[Person, CalculationBase]
    payers: dict[Person, Payer]
    plan: ResolvedPlan
    debts: dict[Person, DebtState] = field(default_factory=dict)
    periods: list[LeavePeriod] = field(default_factory=list)
    averaged_applied: bool = False
    averaged_deadline: date | None = None

    def insured(self, person: Person) -> bool:
        return person in self.insurance and self.insurance[person].insured
