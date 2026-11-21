"""Input and output types of the rules engine.

Input = `FamilyProfile` (also the shape stored in `family.profile` JSONB).
Output = `EvaluationResult`. Field names are English; strings meant for the user (`*_pl`)
are Polish.
"""

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

# --------------------------------------------------------------------------------------------
# Input
# --------------------------------------------------------------------------------------------


class Situation(StrEnum):
    BIRTH = "birth"
    ADOPTION = "adoption"  # child taken in, court proceedings for adoption started
    FOSTER = "foster"  # non-professional foster family


class EmploymentType(StrEnum):
    EMPLOYEE = "employee"  # umowa o pracę
    CONTRACT = "contract"  # umowa zlecenie
    SELF_EMPLOYED = "self_employed"  # działalność gospodarcza
    COOPERATING = "cooperating"  # osoba współpracująca
    UNEMPLOYED = "unemployed"
    OTHER = "other"


class InsuranceKind(StrEnum):
    NONE = "none"
    MANDATORY = "mandatory"
    VOLUNTARY = "voluntary"


class JobLossReason(StrEnum):
    EMPLOYER_BANKRUPTCY = "employer_bankruptcy"  # also liquidation or death of the employer
    UNLAWFUL_DISMISSAL = "unlawful_dismissal"  # confirmed by a final court judgment
    OTHER = "other"


class MotherCannotCare(StrEnum):
    HOSPITAL = "hospital"
    DISABLED = "disabled"  # unable to live independently
    DEATH = "death"
    ABANDONED = "abandoned"


class ParentProfile(BaseModel):
    employment: EmploymentType
    # None = derive from `employment` (employees are insured by law, others only voluntarily).
    sickness_insurance: InsuranceKind | None = None
    # Days of uninterrupted sickness insurance at the planned start of sick leave.
    insured_days: int | None = Field(default=None, ge=0)
    insurance_ended_on: date | None = None
    job_loss_reason: JobLossReason | None = None
    # Average monthly GROSS base of the last 12 months (salary, or base of sickness contribution).
    average_monthly_base: float | None = Field(default=None, ge=0)
    working_time_fraction: float = Field(default=1.0, gt=0, le=1)
    fixed_term_contract: bool = False
    employer_insured_count: int | None = Field(default=None, ge=0)
    # Contribution debt (self-employed, cooperating persons, "ulga na start").
    start_relief: bool = False
    contribution_debt: float = Field(default=0, ge=0)
    debt_paid_on: date | None = None
    debt_in_installments: bool = False  # installment plan paid on time = no debt
    base_raised_in_pregnancy: bool = False
    # Share of full-time work kept while on parental leave (0 – 0.5, same employer only).
    planned_work_fraction: float = Field(default=0, ge=0, le=1)
    on_pregnancy_sick_leave: bool = False  # e-ZLA with code B

    @model_validator(mode="after")
    def _derive_insurance(self) -> "ParentProfile":
        if self.sickness_insurance is None:
            self.sickness_insurance = (
                InsuranceKind.MANDATORY
                if self.employment == EmploymentType.EMPLOYEE
                else InsuranceKind.NONE
            )
        return self


class ChildProfile(BaseModel):
    situation: Situation = Situation.BIRTH
    birth_date: date | None = None  # actual date of birth
    due_date: date | None = None  # expected date of birth (used while birth_date is unknown)
    placement_date: date | None = None  # adoption / foster: date the child was taken in
    children_count: int = Field(default=1, ge=1, le=10)
    za_zyciem: bool = False
    stillborn: bool = False
    died_on: date | None = None
    children_surviving: int | None = Field(default=None, ge=0)
    gestation_weeks: int | None = Field(default=None, ge=20, le=45)
    birth_weight_g: int | None = Field(default=None, ge=200, le=8000)
    hospital_days: int = Field(default=0, ge=0)  # stay from day 5 up to week 8 / 15
    hospital_first_day: int | None = Field(default=None, ge=1)  # day after birth stay began
    age_years: float | None = Field(default=None, ge=0, le=18)  # adoption / foster
    school_deferred: bool = False

    @property
    def event_date(self) -> date | None:
        if self.situation == Situation.BIRTH:
            return self.birth_date or self.due_date
        return self.placement_date

    @property
    def is_born(self) -> bool:
        return self.situation == Situation.BIRTH and self.birth_date is not None


class Plan(BaseModel):
    """Choices the parents can make. Defaults give a sensible plan."""

    maternity_before_birth_weeks: int = Field(default=0, ge=0)
    maternity_weeks_to_father: int = Field(default=0, ge=0)
    parental_weeks_father: int | None = Field(default=None, ge=0)  # None = reserved minimum
    parental_parts_mother: int = Field(default=1, ge=1)
    parental_parts_father: int = Field(default=1, ge=1)
    paternity_parts: int = Field(default=1, ge=1)
    use_supplementary_leave: bool = True
    supplementary_taken_by: Literal["mother", "father"] = "mother"


class FamilyProfile(BaseModel):
    child: ChildProfile
    mother: ParentProfile | None = None
    father: ParentProfile | None = None
    mother_cannot_care: MotherCannotCare | None = None
    # Date the mother files (or filed) the application for the averaged 81.5% rate.
    averaged_rate_applied_on: date | None = None
    plan: Plan = Field(default_factory=Plan)

    @model_validator(mode="after")
    def _validate(self) -> "FamilyProfile":
        if self.mother is None and self.father is None:
            raise ValueError("At least one parent is required")
        if self.child.event_date is None:
            raise ValueError("Provide birth_date or due_date (or placement_date for adoption)")
        return self


# --------------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------------

Person = Literal["mother", "father", "family"]


class Status(StrEnum):
    ELIGIBLE = "eligible"
    CONDITIONAL = "conditional"  # depends on something the user still has to do or confirm
    NOT_ELIGIBLE = "not_eligible"
    INFO = "info"


class CalculationBase(BaseModel):
    person: Person
    gross_base: float | None  # average base before the 13.71% deduction
    net_base: float | None  # base of the benefit (gross base minus social contributions)
    minimum_wage_applied: bool = False
    note_pl: str


class LeavePeriod(BaseModel):
    id: str
    person: Person
    kind: Literal["pregnancy_sickness", "maternity", "supplementary", "parental", "paternity"]
    label_pl: str
    start: date
    end: date
    days: int
    weeks: float
    paid: bool  # False when the parent has the leave but no right to the allowance
    rate: float | None
    monthly_gross: float | None
    total_gross: float | None
    total_net_estimate: float | None
    work_fraction: float = 0


class BenefitResult(BaseModel):
    code: str
    person: Person
    title_pl: str
    status: Status
    summary_pl: str
    reasons_pl: list[str] = []
    legal_basis: list[str] = []
    weeks: float | None = None
    days: int | None = None
    rate: float | None = None
    monthly_gross: float | None = None
    monthly_net_estimate: float | None = None
    total_gross: float | None = None
    total_net_estimate: float | None = None
    raised_to_minimum: bool = False
    start: date | None = None
    end: date | None = None
    payer: Literal["employer", "zus", "municipality"] | None = None
    apply_to_pl: str | None = None
    documents_pl: list[str] = []
    deadline: date | None = None
    days_left: int | None = None
    deadline_note_pl: str | None = None


class Risk(BaseModel):
    code: str
    severity: Literal["high", "medium", "info"]
    person: Person
    title_pl: str
    text_pl: str
    legal_basis: str | None = None


class AveragedRateComparison(BaseModel):
    standard_total: float | None
    averaged_total: float | None
    better: Literal["standard", "averaged", "equal"] | None
    deadline: date
    still_possible: bool
    note_pl: str


class Deadline(BaseModel):
    """Something the user must do (or use up) by a given day."""

    code: str
    person: Person
    kind: Literal["apply", "use_by"]
    title_pl: str
    due: date
    days_left: int  # negative = the deadline has passed
    status: Literal["open", "soon", "overdue"]
    note_pl: str
    benefit_code: str | None = None


class Totals(BaseModel):
    mother_gross: float = 0
    father_gross: float = 0
    family_gross: float = 0
    family_net_estimate: float = 0


class EvaluationResult(BaseModel):
    params_date: date
    situation: Situation
    event_date: date
    event_is_estimate: bool
    bases: list[CalculationBase]
    benefits: list[BenefitResult]
    timeline: list[LeavePeriod]
    risks: list[Risk]
    deadlines: list[Deadline]
    averaged_rate: AveragedRateComparison | None
    totals: Totals
    situation_tags: list[str] = []
    assumptions_pl: list[str] = []
