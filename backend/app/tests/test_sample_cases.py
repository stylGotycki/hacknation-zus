"""Categories of the sample cases supplied by ZUS (sprawy_wzory*.zip) run through the engine.

The case files are scans: their names give the kind of case and the outcome (granted / refused), their forms the
dates. Each test names the sample case it mirrors and checks the outcome and the dates the ZUS documents show
(the data in the scans is anonymised, so the profiles use the dates and amounts read from them or typical ones).
"""

from datetime import date

import pytest

from app.engine import PlanViolation
from app.tests.test_rules import benefit, employee, periods, run


def kinds(result, person=None):
    return [(p.person, p.kind, p.days) for p in periods(result, person)]


def test_still_birth_gives_8_weeks_from_the_birth():
    """'Jolanta Ko_2 – martwe urodzenie': birth 12.04.2026, leave 12.04–06.06.2026 (8 weeks), granted."""
    r = run({"child": {"birth_date": "2026-04-12", "stillborn": True}, "mother": employee(4600)})
    (leave,) = periods(r, "mother")
    assert (leave.start, leave.end, leave.days) == (date(2026, 4, 12), date(2026, 6, 6), 56)
    assert benefit(r, "macierzynski_mama").status == "eligible"


def test_maternity_and_parental_dates_match_the_zam_of_a_self_employed_mother():
    """'Janina Poz_2 – podwyższenie kwoty zasiłku': birth 23.01.2024, maternity to 10.06.2024 (140 days)."""
    r = run(
        {
            "child": {"birth_date": "2024-01-23"},
            "mother": {
                "employment": "self_employed",
                "sickness_insurance": "voluntary",
                "average_monthly_base": 1000,
                "insured_days": 600,
            },
        }
    )
    maternity, parental = periods(r, "mother")
    assert (maternity.start, maternity.end, maternity.days) == (
        date(2024, 1, 23),
        date(2024, 6, 10),
        140,
    )
    assert parental.start == date(2024, 6, 11)
    assert maternity.raised_to_minimum and parental.raised_to_minimum  # request: raise to 1000 zł


@pytest.mark.parametrize(
    "mother",
    [
        {"employment": "contract", "sickness_insurance": "none", "average_monthly_base": 4000},
        employee(sickness_insurance="mandatory", insurance_ended_on="2026-08-31"),
    ],
    ids=["contract_without_sickness_insurance", "insurance_ended_before_birth"],
)
def test_refusal_when_not_insured_on_the_birth_day(mother):
    """'Małgorzata Rze_3 – umowa zlecenie bez chorobowego – odmowa', 'Ewa Łód_5 – nie podlega ubezp. na dzień porodu'."""
    r = run({"child": {"birth_date": "2026-10-05"}, "mother": mother})
    assert benefit(r, "macierzynski_mama").status == "not_eligible"
    assert not periods(r, "mother")


def test_debt_blocks_the_self_employed_father():
    """'Piotr Cho_5 – urlop ojcowski, odmowa z powodu zadłużenia, osoba prowadząca działalność'."""
    father = {
        "employment": "self_employed",
        "sickness_insurance": "voluntary",
        "average_monthly_base": 5000,
        "contribution_debt": 3000,
    }
    r = run({"child": {"birth_date": "2026-10-05"}, "mother": employee(), "father": father})
    assert benefit(r, "ojcowski").status != "eligible"
    assert any("zadłuż" in risk.title_pl.lower() for risk in r.risks)


def test_parental_leave_cannot_be_split_into_a_sixth_part():
    """'Tomasz Po_11 – ojciec – za okres rodz. – 6ta część – decyzja odmowna' (at most 5 parts)."""
    with pytest.raises(PlanViolation):
        run(
            {
                "child": {"birth_date": "2026-10-05"},
                "mother": employee(),
                "father": employee(),
                "plan": {"parental_parts_father": 6},
            }
        )


def test_mother_resigns_after_14_weeks_and_the_father_takes_the_rest():
    """'Barbara Ra_4 – rezygnacja po 14 tyg.': the mother keeps 14 weeks, the father continues right after."""
    r = run(
        {
            "child": {"birth_date": "2026-10-05"},
            "mother": employee(),
            "father": employee(),
            "plan": {"maternity_weeks_to_father": 6},
        }
    )
    mother = next(p for p in periods(r, "mother", "maternity"))
    father = next(p for p in periods(r, "father", "maternity"))
    assert mother.days == 98
    assert father.start == date(2027, 1, 11) and father.days == 42


def test_insurance_ended_but_fixed_term_contract_extended_to_the_birth():
    """'Zofia Zi_4 – zasiłek po ustaniu ubezp., zatrudnienie do dnia porodu' – granted."""
    r = run(
        {
            "child": {"birth_date": "2026-10-05"},
            "mother": employee(
                fixed_term_contract=True,
                sickness_insurance="mandatory",
                insurance_ended_on="2026-10-04",
            ),
        }
    )
    assert benefit(r, "macierzynski_mama").status == "eligible"


def test_twins_with_za_zyciem_certificate_have_the_extended_parental_leave():
    """'Justyna Toruńska_5 – bliźnięta, wcześniaki, zaśw. za życiem': 31 weeks maternity, 67 weeks parental pool."""
    r = run(
        {
            "child": {"birth_date": "2026-10-05", "children_count": 2, "za_zyciem": True},
            "mother": employee(),
            "father": employee(),
        }
    )
    assert next(p for p in periods(r, "mother", "maternity")).days == 217
    mother_parental = next(p for p in periods(r, "mother", "parental"))
    assert mother_parental.days == (67 - 9) * 7


def test_one_of_triplets_stillborn_leaves_the_leave_for_the_surviving_children():
    """'Jolanta Poz_9 – 3 dzieci, 1 martwourodzone, 1 za życiem': leave by the number of surviving children."""
    r = run(
        {
            "child": {
                "birth_date": "2026-10-05",
                "children_count": 3,
                "stillborn": True,
                "children_surviving": 2,
                "za_zyciem": True,
            },
            "mother": employee(planned_work_fraction=0.5),
        }
    )
    assert next(p for p in periods(r, "mother", "maternity")).days == 31 * 7


def test_child_dying_before_8_weeks_keeps_leave_for_the_surviving_twin():
    """Task text: a child dying before 8 weeks of life – leave by the number of children left alive."""
    r = run(
        {
            "child": {
                "birth_date": "2026-10-05",
                "children_count": 2,
                "died_on": "2026-10-26",
                "children_surviving": 1,
            },
            "mother": employee(),
        }
    )
    assert next(p for p in periods(r, "mother", "maternity")).days == 20 * 7


def test_maternity_can_start_before_the_due_date():
    """'Natalia Ko_5 – zas. mac. w tym przed przewidywaną datą porodu'."""
    r = run(
        {
            "child": {"due_date": "2027-01-20"},
            "mother": employee(),
            "plan": {"maternity_before_birth_weeks": 4},
        }
    )
    before = next(p for p in periods(r, "mother") if p.start < date(2027, 1, 20))
    assert before.days == 28 and before.end == date(2027, 1, 19)
