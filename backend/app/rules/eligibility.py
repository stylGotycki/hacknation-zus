"""Who can get an allowance: insurance on the day of the event, contribution debt, payer."""

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from app.rules.dates import add_months
from app.rules.models import (
    EmploymentType,
    InsuranceKind,
    JobLossReason,
    ParentProfile,
)
from app.rules.params import Params

DEBT_EMPLOYMENT = {EmploymentType.SELF_EMPLOYED, EmploymentType.COOPERATING}


@dataclass
class Insurance:
    insured: bool
    reasons_pl: list[str] = field(default_factory=list)
    # Insurance ended in a way that still gives the "allowance equal to maternity allowance".
    pregnancy_equivalent: bool = False


def insurance_on(parent: ParentProfile, event_date: date) -> Insurance:
    """Is the parent covered by sickness insurance on the day of birth / taking in the child?

    Maternity-type allowances need insurance on that day; no minimum insurance period.
    """
    if parent.sickness_insurance == InsuranceKind.NONE:
        reason = {
            EmploymentType.UNEMPLOYED: "Nie podlegasz ubezpieczeniu chorobowemu (brak pracy).",
            EmploymentType.CONTRACT: "Umowa zlecenie nie daje ubezpieczenia chorobowego, "
            "jeśli nie zgłosisz się do niego dobrowolnie.",
            EmploymentType.SELF_EMPLOYED: "Prowadzisz działalność bez dobrowolnego ubezpieczenia "
            "chorobowego – zasiłek nie przysługuje.",
            EmploymentType.COOPERATING: "Osoba współpracująca jest ubezpieczona chorobowo "
            "tylko dobrowolnie – brak zgłoszenia oznacza brak zasiłku.",
        }.get(parent.employment, "Brak ubezpieczenia chorobowego w dniu porodu.")
        return Insurance(False, [reason])

    if parent.on_childcare_leave:
        return Insurance(
            True,
            ["Urodzenie w czasie urlopu wychowawczego daje prawo do zasiłku macierzyńskiego (art. 29 ust. 1)."],
        )
    if (
        parent.fixed_term_contract
        and parent.insurance_ended_on is not None
        and parent.insurance_ended_on < event_date
        and parent.insurance_ended_on >= add_months(event_date, -6)
    ):
        return Insurance(
            True,
            ["Umowa na czas określony przedłuża się do dnia porodu, jeśli skończyłaby się po "
             "3. miesiącu ciąży (Kodeks pracy, art. 177 § 3)."],
        )

    if parent.insurance_ended_on is not None and parent.insurance_ended_on < event_date:
        reasons = [
            f"Ubezpieczenie chorobowe ustało {parent.insurance_ended_on:%d.%m.%Y}, "
            "czyli przed dniem porodu."
        ]
        equivalent = parent.job_loss_reason in (
            JobLossReason.EMPLOYER_BANKRUPTCY,
            JobLossReason.UNLAWFUL_DISMISSAL,
        )
        return Insurance(False, reasons, pregnancy_equivalent=equivalent)

    return Insurance(True)


@dataclass
class DebtState:
    kind: Literal["none", "blocked", "paid_in_time", "paid_late"]
    effective_start: date
    amount: float = 0
    threshold: float = 0
    note_pl: str | None = None


def debt_state(parent: ParentProfile, benefit_start: date, params: Params) -> DebtState:
    """Contribution debt blocks the allowance of self-employed persons, cooperating persons
    and people on the "ulga na start" when it exceeds 1% of the minimum wage."""
    threshold = round(
        params.number("contribution_debt_threshold_ratio") * params.number("minimum_wage"), 2
    )
    applies = parent.employment in DEBT_EMPLOYMENT or parent.start_relief
    if not applies or parent.debt_in_installments or parent.contribution_debt <= threshold:
        return DebtState("none", benefit_start, parent.contribution_debt, threshold)

    window = params.integer("debt_repayment_window_months")
    amount = parent.contribution_debt
    if parent.debt_paid_on is None:
        return DebtState(
            "blocked",
            benefit_start,
            amount,
            threshold,
            f"Zadłużenie z tytułu składek ({amount:.2f} zł) przekracza próg {threshold:.2f} zł. "
            "Zasiłek zostanie wypłacony dopiero po spłacie zadłużenia.",
        )
    if parent.debt_paid_on <= add_months(benefit_start, window):
        return DebtState(
            "paid_in_time",
            benefit_start,
            amount,
            threshold,
            f"Zadłużenie spłacone w ciągu {window} miesięcy – zasiłek przysługuje za cały okres.",
        )
    return DebtState(
        "paid_late",
        max(parent.debt_paid_on, benefit_start),
        amount,
        threshold,
        f"Zadłużenie spłacone po {window} miesiącach – zasiłek przysługuje dopiero "
        f"od dnia spłaty ({parent.debt_paid_on:%d.%m.%Y}).",
    )


@dataclass
class Payer:
    who: Literal["employer", "zus"]
    apply_to_pl: str


def payer_for(parent: ParentProfile, params: Params) -> Payer:
    """Employers (and contract-givers) reporting more than 20 insured persons pay allowances
    themselves; everyone else is paid by ZUS."""
    threshold = params.integer("payer_threshold_insured")
    count = parent.employer_insured_count
    pays_itself = count is not None and count > threshold

    if parent.employment == EmploymentType.EMPLOYEE:
        if pays_itself:
            return Payer(
                "employer",
                "Złóż wniosek o urlop u pracodawcy – zasiłek wypłaci pracodawca "
                f"(zgłasza powyżej {threshold} ubezpieczonych).",
            )
        return Payer(
            "zus",
            "Złóż wniosek o urlop u pracodawcy. Zasiłek wypłaci ZUS – pracodawca prześle do ZUS "
            f"zaświadczenie Z-3 (zgłasza nie więcej niż {threshold} ubezpieczonych).",
        )
    if parent.employment == EmploymentType.CONTRACT and pays_itself:
        return Payer(
            "employer",
            "Złóż wniosek ZAM u zleceniodawcy, który wypłaca zasiłki "
            f"(zgłasza powyżej {threshold} ubezpieczonych); zleceniodawca przekaże Z-3a do ZUS, "
            "jeśli wypłaca ZUS.",
        )
    return Payer("zus", "Złóż wniosek ZAM bezpośrednio w ZUS (przez PUE/eZUS lub papierowo).")
