"""Rules of the guide checked against the six sources (KP, UZ, RZ, RW, Poradnik ZUS 2026, Załącznik).

Every test names the provision it checks. The engine runs with the seed rules and 2026 parameters
(no database), the same data the database is seeded with.
"""

from datetime import date, timedelta

import pytest

from app.engine import PlanViolation, evaluate_with_seed, seed_rule_defs
from app.engine.expressions import Evaluator, ExpressionError, parse, references
from app.engine.runtime import RuleDef, Runtime, analyse
from app.rules.models import FamilyProfile
from app.seed.parameters_2026 import current_values

TODAY = date(2026, 11, 22)


def run(profile: dict, today: date = TODAY, **overrides):
    return evaluate_with_seed(FamilyProfile.model_validate(profile), today, overrides or None)


def employee(base=6000, **extra):
    return {
        "employment": "employee",
        "average_monthly_base": base,
        "employer_insured_count": 50,
        **extra,
    }


def periods(result, person=None, kind=None):
    return [
        p
        for p in result.timeline
        if (person is None or p.person == person) and (kind is None or p.kind == kind)
    ]


def days(result, person=None, kind=None):
    return sum(p.days for p in periods(result, person, kind))


def benefit(result, code):
    return next(b for b in result.benefits if b.code == code)


def codes(items):
    return {i.code for i in items}


# --- Rule set as data ---------------------------------------------------------------------------


def test_seed_rules_are_consistent():
    """No syntax errors, unknown names, missing parameters or cycles."""
    assert analyse(seed_rule_defs(), current_values().keys()) == []


def test_every_rule_cites_a_source():
    for rule in seed_rule_defs():
        assert rule.source in {"KP", "UZ", "RZ", "RW", "PR", "ZAL"}, rule.code


@pytest.mark.parametrize(
    "profile",
    [
        {"child": {"birth_date": "2026-10-01"}, "mother": employee()},
        {"child": {"due_date": "2027-03-01"}, "mother": employee(), "father": employee()},
        {
            "child": {"situation": "adoption", "placement_date": "2026-11-01", "age_years": 3},
            "father": employee(),
        },
        {"child": {"birth_date": "2026-11-01", "stillborn": True}, "mother": employee()},
        {"child": {"birth_date": "2026-11-01"}, "mother": {"employment": "unemployed"}},
    ],
)
def test_no_rule_fails_at_runtime(profile):
    assert run(profile).rule_errors == {}


# --- Urlop i zasiłek macierzyński ------------------------------------------------------------------


def test_maternity_20_weeks_at_100_percent_with_base_minus_13_71():
    """KP art. 180 § 1 pkt 1; UZ art. 31 ust. 1; UZ art. 36 i 47 (13,71%)."""
    r = run({"child": {"birth_date": "2026-11-10"}, "mother": employee(6000)})
    mat = periods(r, "mother", "maternity")
    assert sum(p.days for p in mat) == 140 and mat[0].start == date(2026, 11, 10)
    assert mat[0].rate == 1.0 and mat[0].monthly_gross == 5177.4  # 6000 × (1 − 0,1371)
    assert benefit(r, "macierzynski_mama").status == "eligible"


@pytest.mark.parametrize(
    "count,weeks,parental", [(1, 20, 41), (2, 31, 43), (3, 33, 43), (5, 37, 43)]
)
def test_maternity_and_parental_by_number_of_children(count, weeks, parental):
    """KP art. 180 § 1, art. 182¹ᵃ § 1."""
    r = run({"child": {"birth_date": "2026-11-10", "children_count": count}, "mother": employee()})
    assert days(r, "mother", "maternity") == weeks * 7
    assert days(r, "mother", "parental") == parental * 7


def test_part_of_maternity_before_birth_up_to_6_weeks():
    """KP art. 180 § 2."""
    r = run(
        {
            "child": {"due_date": "2027-03-01"},
            "mother": employee(),
            "plan": {"maternity_before_birth_weeks": 6},
        }
    )
    mat = periods(r, "mother", "maternity")
    assert mat[0].start == date(2027, 3, 1) - timedelta(days=42)
    assert days(r, "mother", "maternity") == 140
    with pytest.raises(PlanViolation, match="6 tygodni"):
        run(
            {
                "child": {"due_date": "2027-03-01"},
                "mother": employee(),
                "plan": {"maternity_before_birth_weeks": 7},
            }
        )


def test_father_takes_over_after_14_weeks():
    """KP art. 180 § 4; UZ art. 29 ust. 3."""
    family = {"child": {"birth_date": "2026-11-10"}, "mother": employee(), "father": employee(7000)}
    r = run({**family, "plan": {"maternity_weeks_to_father": 6}})
    assert days(r, "mother", "maternity") == 14 * 7
    taken = periods(r, "father", "maternity")
    assert sum(p.days for p in taken) == 42 and taken[0].start == date(2026, 11, 10) + timedelta(
        days=98
    )
    assert "t_rezygnacja" in codes(r.deadlines) and "t_tata_macierzynski" in codes(r.deadlines)
    with pytest.raises(PlanViolation, match="co najmniej 14 tygodni"):
        run({**family, "plan": {"maternity_weeks_to_father": 7}})


def test_mother_in_hospital_father_uses_the_leave_meanwhile():
    """KP art. 180 § 10–11; UZ art. 29 ust. 6 (po co najmniej 8 tygodniach)."""
    r = run(
        {
            "child": {"birth_date": "2026-09-01"},
            "mother_cannot_care": "hospital",
            "mother_situation_from": "2026-11-02",
            "mother_situation_to": "2026-11-20",
            "mother": employee(),
            "father": employee(),
        }
    )
    father = periods(r, "father", "maternity")
    assert father[0].start == date(2026, 11, 2) and father[0].days == 19
    assert days(r, "mother", "maternity") + days(r, "father", "maternity") == 140


def test_stillbirth_8_weeks_no_parental_and_funeral_allowance():
    """KP art. 180¹ § 1; UZ art. 31 ust. 1; Poradnik – zasiłek pogrzebowy 7000 zł."""
    r = run(
        {
            "child": {"birth_date": "2026-11-01", "stillborn": True},
            "mother": employee(),
            "father": employee(),
        }
    )
    assert days(r, "mother", "maternity") == 56
    assert not periods(r, kind="parental") and not periods(r, kind="paternity")
    assert "pogrzebowy" in codes(r.benefits) and "7 000 zł" in benefit(r, "pogrzebowy").summary_pl
    assert "stillbirth" in r.situation_tags and r.averaged_rate is None


def test_stillbirth_cannot_be_planned():
    """Martwe urodzenie dopiero po porodzie (RZ § 13 ust. 1 pkt 2 – dokument po porodzie)."""
    with pytest.raises(PlanViolation, match="dopiero po porodzie"):
        run({"child": {"due_date": "2027-02-01", "stillborn": True}, "mother": employee()})


def test_child_death_after_8_weeks_leave_ends_7_days_after_death():
    """KP art. 180¹ § 1."""
    r = run({"child": {"birth_date": "2026-08-01", "died_on": "2026-10-15"}, "mother": employee()})
    mat = periods(r, "mother", "maternity")
    assert mat[-1].end == date(2026, 10, 21)
    with pytest.raises(PlanViolation, match="Data zgonu"):
        run({"child": {"birth_date": "2026-08-01", "died_on": "2026-07-15"}, "mother": employee()})


# --- Przyjęcie dziecka -------------------------------------------------------------------------


def test_adoption_and_foster_family_leave():
    """KP art. 183 § 1, § 1¹, § 3, § 4 pkt 3; UZ art. 29 ust. 1 pkt 2–3."""
    adoption = run(
        {
            "child": {"situation": "adoption", "placement_date": "2026-11-01", "age_years": 5},
            "mother": employee(),
        }
    )
    assert (
        days(adoption, "mother", "maternity") == 140
        and days(adoption, "mother", "parental") == 41 * 7
    )
    foster = run(
        {
            "child": {"situation": "foster", "placement_date": "2026-11-01", "age_years": 6.9},
            "mother": employee(),
        }
    )
    assert (
        days(foster, "mother", "maternity") == 63
    )  # 9 weeks: age limit of 7 years is reached earlier
    assert days(foster, "mother", "parental") == 38 * 7
    too_old = run(
        {
            "child": {"situation": "foster", "placement_date": "2026-11-01", "age_years": 8},
            "mother": employee(),
        }
    )
    assert benefit(too_old, "macierzynski_mama").status == "not_eligible"


def test_adoption_by_father_alone():
    """UZ art. 29 ust. 2; KP art. 183."""
    r = run(
        {
            "child": {"situation": "adoption", "placement_date": "2026-11-01", "age_years": 3},
            "father": employee(),
        }
    )
    assert days(r, "father", "maternity") == 140
    paternity = periods(r, "father", "paternity")[0]
    assert paternity.start > periods(r, "father", "maternity")[0].end  # no overlap


# --- Uzupełniający urlop macierzyński -----------------------------------------------------------


@pytest.mark.parametrize(
    "child,weeks",
    [
        ({"gestation_weeks": 26, "hospital_days": 120, "hospital_first_day": 1}, 15),  # < 28 tyg.
        (
            {
                "gestation_weeks": 30,
                "birth_weight_g": 900,
                "hospital_days": 40,
                "hospital_first_day": 1,
            },
            6,
        ),
        (
            {"gestation_weeks": 31, "hospital_days": 80, "hospital_first_day": 1},
            8,
        ),  # 28–36 tyg.: max 8
        (
            {"gestation_weeks": 39, "hospital_days": 10, "hospital_first_day": 6},
            2,
        ),  # w terminie, od 5. dnia
        (
            {"gestation_weeks": 39, "hospital_days": 10, "hospital_first_day": 2},
            0,
        ),  # pobyt za wcześnie
        (
            {"gestation_weeks": 39, "hospital_days": 1, "hospital_first_day": 6},
            0,
        ),  # krócej niż 2 dni
    ],
)
def test_supplementary_maternity_leave(child, weeks):
    """KP art. 180² § 1–3; UZ art. 29a ust. 1, art. 31 ust. 1 (100%)."""
    r = run({"child": {"birth_date": "2026-11-01", **child}, "mother": employee()})
    sup = periods(r, "mother", "supplementary")
    assert sum(p.days for p in sup) == weeks * 7
    if weeks:
        assert sup[0].rate == 1.0 and sup[0].start == periods(r, "mother", "maternity")[
            -1
        ].end + timedelta(days=1)


# --- Urlop rodzicielski i ojcowski -----------------------------------------------------------------


def test_parental_split_with_9_weeks_for_each_parent():
    """KP art. 182¹ᵃ § 4; UZ art. 31 ust. 2."""
    family = {"child": {"birth_date": "2026-11-10"}, "mother": employee(), "father": employee()}
    r = run(family)
    assert days(r, "mother", "parental") == 32 * 7 and days(r, "father", "parental") == 9 * 7
    with pytest.raises(PlanViolation, match="najwyżej 32"):
        run({**family, "plan": {"parental_weeks_father": 33}})
    r = run({**family, "plan": {"parental_weeks_father": 0}})
    assert "r_9_tygodni" in codes(r.risks)


def test_father_gets_whole_parental_when_mother_is_not_insured():
    """UZ art. 31 ust. 3h; urlop ojcowski – samodzielne prawo taty (Poradnik)."""
    r = run(
        {
            "child": {"birth_date": "2026-11-10"},
            "mother": {"employment": "unemployed"},
            "father": employee(),
        }
    )
    assert days(r, "father", "parental") == 41 * 7 and days(r, "father", "paternity") == 14
    assert benefit(r, "macierzynski_mama").status == "not_eligible"
    assert "swiadczenie_rodzicielskie_info" not in codes(r.benefits)


def test_nobody_insured_gets_parental_benefit_information():
    """Poradnik – świadczenie rodzicielskie dla osób bez prawa do zasiłku."""
    r = run({"child": {"due_date": "2027-01-10"}, "mother": {"employment": "unemployed"}})
    assert "swiadczenie_rodzicielskie_info" in codes(r.benefits) and not r.timeline


def test_work_during_parental_leave():
    """KP art. 182¹ᵉ § 1, art. 182¹ᶠ § 1; UZ art. 31 ust. 4a."""
    r = run(
        {"child": {"birth_date": "2026-11-10"}, "mother": employee(6000, planned_work_fraction=0.5)}
    )
    par = periods(r, "mother", "parental")
    assert sum(p.days for p in par) == 82 * 7  # 41 tyg. × 2, limit 82 tygodni
    assert par[0].monthly_gross == round(5177.4 * 0.7 * 0.5, 2)
    with pytest.raises(PlanViolation, match="50% etatu"):
        run({"child": {"birth_date": "2026-11-10"}, "mother": employee(planned_work_fraction=0.6)})
    with pytest.raises(PlanViolation, match="tylko pracownik"):
        run(
            {
                "child": {"birth_date": "2026-11-10"},
                "mother": {
                    "employment": "self_employed",
                    "sickness_insurance": "voluntary",
                    "average_monthly_base": 5000,
                    "planned_work_fraction": 0.5,
                },
            }
        )


def test_paternity_two_weeks_until_12_months_and_parts():
    """KP art. 182³ § 1 i § 1¹."""
    family = {"child": {"birth_date": "2026-11-10"}, "mother": employee(), "father": employee()}
    r = run(family)
    assert days(r, "father", "paternity") == 14
    use_by = next(d for d in r.deadlines if d.code == "t_ojcowski_do")
    assert use_by.due == date(2027, 11, 9)
    with pytest.raises(PlanViolation, match="2 częściach"):
        run({**family, "plan": {"paternity_parts": 3}})


def test_parental_deadline_end_of_year_child_turns_6():
    """KP art. 182¹ᶜ."""
    r = run({"child": {"birth_date": "2026-11-10"}, "mother": employee()})
    assert next(d for d in r.deadlines if d.code == "t_rodzicielski_do").due == date(2032, 12, 31)


# --- Stawka 81,5% ------------------------------------------------------------------------------


def test_averaged_rate_except_9_weeks_of_the_other_parent():
    """UZ art. 30a, art. 31 ust. 3 i 3f."""
    r = run(
        {
            "child": {"birth_date": "2026-11-10"},
            "mother": employee(),
            "father": employee(),
            "plan": {"averaged_rate": True},
        }
    )
    assert {p.rate for p in periods(r, "mother")} == {0.815}
    assert {p.rate for p in periods(r, "father", "parental")} == {0.7}
    assert periods(r, "father", "paternity")[0].rate == 1.0
    assert r.averaged_rate and r.averaged_rate.still_possible


def test_averaged_rate_after_21_days_is_not_possible():
    """UZ art. 30a ust. 2."""
    r = run(
        {
            "child": {"birth_date": "2026-10-01"},
            "mother": employee(),
            "plan": {"averaged_rate": True},
        }
    )
    assert {p.rate for p in periods(r, "mother", "maternity")} == {1.0}
    assert "r_usredniona_po_terminie" in codes(r.risks)


def test_parental_not_started_in_first_year_is_70_percent():
    """UZ art. 31 ust. 3g i 4."""
    r = run(
        {
            "child": {"birth_date": "2026-11-10"},
            "mother": employee(),
            "plan": {"averaged_rate": True, "parental_mother_start": "2027-12-01"},
        }
    )
    assert {p.rate for p in periods(r, "mother", "parental")} == {0.7}
    assert "r_pierwszy_rok" in codes(r.risks)


# --- Podstawa, płatnik, zadłużenie ---------------------------------------------------------------


def test_minimum_base_only_for_full_time_employees_and_cap_for_others():
    """UZ art. 45 ust. 1–2 (płaca minimalna), art. 47–48 (23 550 zł); Załącznik."""
    low = run({"child": {"birth_date": "2026-11-10"}, "mother": employee(3000)})
    assert low.bases[0].net_base == 4147.1 and low.bases[0].minimum_wage_applied
    part = run(
        {"child": {"birth_date": "2026-11-10"}, "mother": employee(2000, working_time_fraction=0.5)}
    )
    assert part.bases[0].net_base == 1725.8
    jdg = {
        "employment": "self_employed",
        "sickness_insurance": "voluntary",
        "average_monthly_base": 30000,
    }
    high = run({"child": {"birth_date": "2026-11-10"}, "mother": jdg})
    assert high.bases[0].net_base == pytest.approx(20321.3, abs=0.01)


@pytest.mark.parametrize("count,payer", [(50, "employer"), (20, "zus"), (5, "zus")])
def test_payer_depends_on_number_of_insured(count, payer):
    """UZ art. 61 ust. 1–2 (ponad 20 ubezpieczonych)."""
    r = run(
        {"child": {"birth_date": "2026-11-10"}, "mother": employee(employer_insured_count=count)}
    )
    assert benefit(r, "macierzynski_mama").payer == payer


def test_contribution_debt_suspends_and_then_expires():
    """UZ art. 2a ust. 1–2."""
    jdg = {
        "employment": "self_employed",
        "sickness_insurance": "voluntary",
        "average_monthly_base": 5000,
        "contribution_debt": 300,
    }
    recent = run({"child": {"birth_date": "2026-10-01"}, "mother": jdg})
    assert benefit(recent, "macierzynski_mama").status == "conditional" and "t_dlug_mama" in codes(
        recent.deadlines
    )
    old = run({"child": {"birth_date": "2026-03-01"}, "mother": jdg})
    assert benefit(old, "macierzynski_mama").status == "not_eligible"
    small = run({"child": {"birth_date": "2026-10-01"}, "mother": {**jdg, "contribution_debt": 40}})
    assert (
        benefit(small, "macierzynski_mama").status == "eligible"
    )  # ≤ 1% płacy minimalnej (48,06 zł)


def test_start_relief_means_no_sickness_insurance():
    """Poradnik – ulga na start."""
    r = run(
        {
            "child": {"birth_date": "2026-11-10"},
            "mother": {
                "employment": "self_employed",
                "start_relief": True,
                "average_monthly_base": 5000,
            },
        }
    )
    assert benefit(
        r, "macierzynski_mama"
    ).status == "not_eligible" and "r_ulga_na_start_mama" in codes(r.risks)


def test_birth_after_insurance_ended_due_to_bankruptcy():
    """UZ art. 30 ust. 1 i 3 – zasiłek w wysokości zasiłku macierzyńskiego, potem macierzyński."""
    r = run(
        {
            "child": {"due_date": "2026-12-15"},
            "mother": employee(
                5800, insurance_ended_on="2026-09-30", job_loss_reason="employer_bankruptcy"
            ),
        }
    )
    eq = periods(r, "mother", "maternity_equivalent")
    assert eq[0].start == date(2026, 10, 1) and eq[0].end == date(2026, 12, 14)
    assert benefit(r, "macierzynski_mama").status == "eligible"


# --- Ciąża -----------------------------------------------------------------------------------------


def test_sick_leave_in_pregnancy_employer_then_zus():
    """KP art. 92 § 1 pkt 2 (100%, 33 dni / 14 dni po 50 r.ż.); UZ art. 11 ust. 2 pkt 1."""
    profile = {
        "child": {"due_date": "2027-04-01"},
        "mother": employee(6000, sick_leave_start="2026-10-01", sick_leave_end="2026-12-31"),
    }
    r = run(profile)
    employer, zus = periods(r, "mother", "pregnancy_sickness")
    assert employer.days == 33 and employer.payer == "employer" and employer.rate == 1.0
    assert zus.days == 92 - 33
    profile["mother"]["age_over_50"] = True
    assert periods(run(profile), "mother", "pregnancy_sickness")[0].days == 14


# --- Konfigurowalność --------------------------------------------------------------------------


def test_parameter_change_changes_the_result():
    r = run({"child": {"birth_date": "2026-11-10"}, "mother": employee()}, rate_parental=0.6)
    assert {p.rate for p in periods(r, "mother", "parental")} == {0.6}


def test_rule_with_dependency_on_other_rule():
    rules = [
        RuleDef(code="podwojona", kind="wartosc", expression="baza * 2"),
        RuleDef(code="baza", kind="wartosc", expression="param('x') + 1"),
    ]
    run_ = Runtime(rules, {"x": 4}, TODAY).run({})
    assert run_.scope["podwojona"] == 10


def test_cycle_is_reported():
    rules = [
        RuleDef(code="a", kind="wartosc", expression="b + 1"),
        RuleDef(code="b", kind="wartosc", expression="a"),
    ]
    assert any("cykliczna" in e for e in analyse(rules, set()))


@pytest.mark.parametrize(
    "source",
    ["__import__('os')", "mama.__class__", "(lambda: 1)()", "open('x')", "[x for x in a]", "a.b()"],
)
def test_expression_language_rejects_unsafe_constructs(source):
    with pytest.raises(ExpressionError):
        parse(source)


def test_expression_language_basics():
    ev = Evaluator({"mama": {"podstawa": None, "dni": 10}}, {"p": 2}, TODAY)
    assert ev.eval("mama.podstawa * 2") is None  # brak danych nie psuje obliczeń
    assert ev.eval("jesli(mama.dni > 5, 'tak', 'nie')") == "tak"
    assert ev.eval("dodaj_dni(dzis(), 1)") == TODAY + timedelta(days=1)
    assert ev.eval("param('p') * tygodnie(1)") == 14
    assert references("mama.dni + inna_regula") == {"mama", "inna_regula"}
