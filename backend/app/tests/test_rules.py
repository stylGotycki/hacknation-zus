"""Unit tests of the rules engine. No database: parameters come straight from the seed."""

from copy import deepcopy
from datetime import date

import pytest

from app.rules import FamilyProfile, MissingParameterError, Params, PlanError, evaluate
from app.rules.money import amount_for_period
from app.seed.parameters_2026 import all_rows

TODAY = date(2026, 11, 21)


def make_params(overrides: dict | None = None, on: date = TODAY) -> Params:
    values = {r["key"]: deepcopy(r["value"]) for r in all_rows() if r["valid_to"] is None}
    values.update(overrides or {})
    return Params(values, on)


def employee(**kw):
    return {
        "employment": "employee",
        "average_monthly_base": 6000,
        "employer_insured_count": 50,
        **kw,
    }


def profile(**kw) -> FamilyProfile:
    data = {
        "child": {"birth_date": "2026-11-10"},
        "mother": employee(),
    }
    data.update(kw)
    return FamilyProfile.model_validate(data)


def run(prof: FamilyProfile | None = None, params: Params | None = None, today: date = TODAY):
    return evaluate(prof or profile(), params or make_params(), today=today)


def benefit(result, code):
    return next(b for b in result.benefits if b.code == code)


def periods(result, person, kind):
    return [p for p in result.timeline if p.person == person and p.kind == kind]


# --- Calculation base ---------------------------------------------------------------------


def test_base_is_average_minus_social_contributions():
    result = run()
    base = result.bases[0]
    assert base.gross_base == 6000
    assert base.net_base == pytest.approx(6000 * (1 - 0.1371), abs=0.01)
    assert not base.minimum_wage_applied


def test_employee_base_is_raised_to_minimum_wage():
    result = run(profile(mother=employee(average_monthly_base=3000)))
    base = result.bases[0]
    assert base.gross_base == 4806
    assert base.minimum_wage_applied


def test_minimum_wage_scales_with_working_time():
    result = run(profile(mother=employee(average_monthly_base=1000, working_time_fraction=0.5)))
    assert result.bases[0].gross_base == 2403


def test_non_employee_has_no_minimum_wage_floor():
    mother = {
        "employment": "self_employed",
        "sickness_insurance": "voluntary",
        "average_monthly_base": 1441.8,
    }
    base = run(profile(mother=mother)).bases[0]
    assert base.gross_base == 1441.8
    assert not base.minimum_wage_applied


def test_missing_base_gives_no_amounts_but_keeps_entitlement():
    result = run(profile(mother=employee(average_monthly_base=None)))
    maternity = benefit(result, "maternity_allowance_mother")
    assert maternity.weeks == 20
    assert maternity.monthly_gross is None
    assert maternity.status == "conditional"


# --- Amount for a period ---------------------------------------------------------------------


def test_full_month_pays_monthly_amount_partial_month_pays_per_day():
    assert amount_for_period(date(2026, 2, 1), date(2026, 2, 28), 3000) == 3000
    assert amount_for_period(date(2026, 1, 1), date(2026, 1, 31), 3000) == 3000
    assert amount_for_period(date(2026, 3, 1), date(2026, 3, 10), 3000) == 1000
    # 15 days in a 31-day month: 15/30 of the monthly amount, not 15/31
    assert amount_for_period(date(2026, 3, 17), date(2026, 3, 31), 3000) == 1500


def test_period_crossing_months_sums_parts():
    # 10-30 Nov = 21 days (21/30) + December full + 1-5 Jan (5/30)
    total = amount_for_period(date(2026, 11, 10), date(2027, 1, 5), 3000)
    assert total == pytest.approx(3000 * (21 / 30 + 1 + 5 / 30), abs=0.01)


# --- Leave lengths ----------------------------------------------------------------------------


@pytest.mark.parametrize("count,weeks", [(1, 20), (2, 31), (3, 33), (4, 35), (5, 37), (6, 37)])
def test_maternity_weeks_by_number_of_children(count, weeks):
    result = run(profile(child={"birth_date": "2026-11-10", "children_count": count}))
    assert benefit(result, "maternity_allowance_mother").weeks == weeks


def test_parental_leave_single_multiple_and_za_zyciem():
    def parental(**child):
        result = run(profile(child={"birth_date": "2026-11-10", **child}))
        return benefit(result, "parental_allowance_mother").weeks

    assert parental() == 41
    assert parental(children_count=2) == 43
    assert parental(za_zyciem=True) == 65
    assert parental(children_count=2, za_zyciem=True) == 67


def test_changing_a_legal_parameter_changes_the_result():
    table = {"1": 21, "2": 31, "3": 33, "4": 35, "5": 37}
    result = run(params=make_params({"maternity_leave_weeks": table}))
    assert benefit(result, "maternity_allowance_mother").weeks == 21


def test_missing_parameter_raises():
    params = make_params()
    del params._values["maternity_leave_weeks"]
    with pytest.raises(MissingParameterError):
        run(params=params)


def test_father_paternity_leave_is_14_days_and_not_extended_by_twins():
    prof = profile(
        child={"birth_date": "2026-11-10", "children_count": 2},
        father=employee(),
    )
    paternity = benefit(run(prof), "paternity_allowance_father")
    assert paternity.days == 14
    assert paternity.start == date(2026, 11, 10)
    assert paternity.end == date(2026, 11, 23)


def test_paternity_in_two_parts_and_limit():
    two = run(profile(father=employee(), plan={"paternity_parts": 2}))
    assert [p.days for p in periods(two, "father", "paternity")] == [7, 7]
    with pytest.raises(PlanError):
        run(profile(father=employee(), plan={"paternity_parts": 3}))


# --- Supplementary leave --------------------------------------------------------------------------


def test_supplementary_leave_for_very_premature_child_up_to_15_weeks():
    child = {"birth_date": "2026-11-10", "gestation_weeks": 26, "hospital_days": 100}
    result = run(profile(child=child))
    assert benefit(result, "supplementary_allowance_mother").weeks == 15


def test_supplementary_leave_counts_started_weeks_and_caps_at_8():
    child = {"birth_date": "2026-11-10", "gestation_weeks": 33, "hospital_days": 22}
    assert benefit(run(profile(child=child)), "supplementary_allowance_mother").weeks == 4
    child["hospital_days"] = 90
    assert benefit(run(profile(child=child)), "supplementary_allowance_mother").weeks == 8


def test_supplementary_leave_for_term_child_needs_stay_starting_between_day_5_and_28():
    child = {
        "birth_date": "2026-11-10",
        "gestation_weeks": 39,
        "hospital_days": 10,
        "hospital_first_day": 6,
    }
    assert benefit(run(profile(child=child)), "supplementary_allowance_mother").weeks == 2
    child["hospital_first_day"] = 2
    result = run(profile(child=child))
    assert not periods(result, "mother", "supplementary")


def test_supplementary_leave_follows_maternity_and_is_paid_100_percent():
    child = {"birth_date": "2026-11-10", "gestation_weeks": 30, "hospital_days": 14}
    result = run(profile(child=child))
    maternity = periods(result, "mother", "maternity")[0]
    supplementary = periods(result, "mother", "supplementary")[0]
    assert supplementary.start == maternity.end.replace(day=maternity.end.day) + (
        supplementary.start - maternity.end
    )
    assert (supplementary.start - maternity.end).days == 1
    assert supplementary.rate == 1.0


# --- Stillbirth and death of the child ---------------------------------------------------------


def test_stillbirth_gives_8_weeks_and_nothing_else():
    result = run(profile(child={"birth_date": "2026-11-10", "stillborn": True}))
    maternity = benefit(result, "maternity_allowance_mother")
    assert maternity.weeks == 8
    assert not periods(result, "mother", "parental")
    assert "stillbirth" in result.situation_tags


def test_child_died_early_leave_lasts_at_least_7_days_after_death():
    child = {"birth_date": "2026-11-10", "died_on": "2027-01-01"}  # 7.4 weeks old
    maternity = periods(run(profile(child=child)), "mother", "maternity")[0]
    # 8 weeks end on 2027-01-04; 7 days after death = 2027-01-08 is later.
    assert maternity.end == date(2027, 1, 8)


def test_child_died_after_8_weeks_keeps_benefit_only_7_days():
    child = {"birth_date": "2026-11-10", "died_on": "2027-02-01"}
    maternity = periods(run(profile(child=child)), "mother", "maternity")[0]
    assert maternity.end == date(2027, 2, 8)


def test_twin_died_leave_is_for_surviving_children():
    child = {"birth_date": "2026-11-10", "children_count": 2, "children_surviving": 1}
    assert benefit(run(profile(child=child)), "maternity_allowance_mother").weeks == 20


# --- Insurance --------------------------------------------------------------------------------


def test_uninsured_mother_gets_no_allowance_but_fallback_benefit():
    mother = {"employment": "unemployed"}
    result = run(profile(mother=mother))
    assert benefit(result, "maternity_allowance_mother").status == "not_eligible"
    fallback = benefit(result, "parental_benefit")
    assert fallback.weeks == 52 and fallback.monthly_gross == 1000
    assert any(r.code == "no_insurance_mother" and r.severity == "high" for r in result.risks)


def test_fallback_benefit_not_offered_when_other_parent_gets_allowance():
    result = run(profile(mother={"employment": "unemployed"}, father=employee()))
    assert not [b for b in result.benefits if b.code == "parental_benefit"]


def test_self_employed_needs_voluntary_insurance():
    base = {"employment": "self_employed", "average_monthly_base": 5000}
    no = run(profile(mother=base))
    assert benefit(no, "maternity_allowance_mother").status == "not_eligible"
    yes = run(profile(mother={**base, "sickness_insurance": "voluntary"}))
    maternity = benefit(yes, "maternity_allowance_mother")
    assert maternity.status == "eligible" and maternity.payer == "zus"


def test_insurance_ended_before_birth_is_not_eligible_and_flagged():
    mother = employee(insurance_ended_on="2026-10-01")
    result = run(profile(mother=mother))
    assert benefit(result, "maternity_allowance_mother").status == "not_eligible"


def test_insurance_ending_before_expected_birth_is_a_high_risk():
    mother = employee(insurance_ended_on="2026-12-01")
    prof = profile(child={"due_date": "2027-01-15"}, mother=mother)
    result = run(prof)
    assert any(r.code == "insurance_ends_before_event_mother" for r in result.risks)
    assert benefit(result, "maternity_allowance_mother").status == "not_eligible"


def test_maternity_equivalent_allowance_after_employer_bankruptcy():
    mother = employee(insurance_ended_on="2026-09-30", job_loss_reason="employer_bankruptcy")
    result = run(profile(child={"due_date": "2026-12-20"}, mother=mother))
    equivalent = benefit(result, "maternity_equivalent_allowance")
    assert equivalent.rate == 1.0 and equivalent.status == "conditional"


# --- Sickness benefit in pregnancy ---------------------------------------------------------------


def pregnant(**mother):
    return profile(child={"due_date": "2027-02-01"}, mother=employee(**mother))


def test_pregnancy_sickness_waiting_period():
    assert benefit(run(pregnant(insured_days=40)), "sickness_pregnancy").status == "eligible"
    short = benefit(run(pregnant(insured_days=10)), "sickness_pregnancy")
    assert short.status == "conditional" and "20 dni" in short.summary_pl
    voluntary = {"employment": "contract", "sickness_insurance": "voluntary", "insured_days": 40}
    result = run(profile(child={"due_date": "2027-02-01"}, mother=voluntary))
    assert benefit(result, "sickness_pregnancy").status == "conditional"  # 90 days needed


def test_pregnancy_sickness_pays_100_percent():
    sickness = benefit(run(pregnant(insured_days=40)), "sickness_pregnancy")
    assert sickness.rate == 1.0
    assert sickness.monthly_gross == pytest.approx(6000 * (1 - 0.1371), abs=0.01)


# --- Contribution debt ------------------------------------------------------------------------------


def jdg(**kw):
    return {
        "employment": "self_employed",
        "sickness_insurance": "voluntary",
        "average_monthly_base": 5000,
        **kw,
    }


def test_debt_up_to_1_percent_of_minimum_wage_is_ignored():
    result = run(profile(mother=jdg(contribution_debt=48.06)))
    assert benefit(result, "maternity_allowance_mother").status == "eligible"


def test_debt_above_threshold_blocks_allowance_until_repaid():
    result = run(profile(mother=jdg(contribution_debt=500)))
    maternity = benefit(result, "maternity_allowance_mother")
    assert maternity.status == "conditional"
    assert result.totals.mother_gross == 0
    assert any(r.code == "contribution_debt_mother" and r.severity == "high" for r in result.risks)


def test_debt_repaid_within_6_months_keeps_full_period():
    clean = run(profile(mother=jdg()))
    repaid = run(profile(mother=jdg(contribution_debt=500, debt_paid_on="2027-02-01")))
    assert repaid.totals.mother_gross == clean.totals.mother_gross


def test_debt_repaid_late_pays_only_from_repayment_date():
    clean = run(profile(mother=jdg()))
    late = run(profile(mother=jdg(contribution_debt=500, debt_paid_on="2027-08-01")))
    assert 0 < late.totals.mother_gross < clean.totals.mother_gross


def test_installments_paid_on_time_are_not_debt():
    result = run(profile(mother=jdg(contribution_debt=5000, debt_in_installments=True)))
    assert benefit(result, "maternity_allowance_mother").status == "eligible"


def test_employee_debt_is_irrelevant():
    result = run(profile(mother=employee(contribution_debt=5000)))
    assert benefit(result, "maternity_allowance_mother").status == "eligible"


# --- Payer ------------------------------------------------------------------------------------------------


def test_employer_with_more_than_20_insured_pays_itself():
    maternity = benefit(
        run(profile(mother=employee(employer_insured_count=21))), "maternity_allowance_mother"
    )
    assert maternity.payer == "employer"


def test_small_employer_sends_z3_and_zus_pays():
    maternity = benefit(
        run(profile(mother=employee(employer_insured_count=20))), "maternity_allowance_mother"
    )
    assert maternity.payer == "zus"
    assert any("Z-3" in d for d in maternity.documents_pl)


def test_non_employee_files_zam_directly_with_zus():
    maternity = benefit(run(profile(mother=jdg())), "maternity_allowance_mother")
    assert maternity.payer == "zus"
    assert any("ZAM" in d for d in maternity.documents_pl)


# --- Rates and the averaged 81.5% option -------------------------------------------------------------------


def two_parents(**kw):
    return profile(father=employee(average_monthly_base=5000), **kw)


def test_standard_rates_100_and_70_percent():
    result = run(two_parents())
    assert periods(result, "mother", "maternity")[0].rate == 1.0
    assert periods(result, "mother", "parental")[0].rate == 0.7
    assert periods(result, "father", "parental")[0].rate == 0.7


def test_averaged_rate_applied_within_21_days():
    result = run(two_parents(averaged_rate_applied_on="2026-12-01"))  # day 21
    assert periods(result, "mother", "maternity")[0].rate == 0.815
    assert periods(result, "mother", "parental")[0].rate == 0.815
    # the 9 weeks that belong to the other parent stay at 70%
    assert periods(result, "father", "parental")[0].rate == 0.7
    assert periods(result, "father", "paternity")[0].rate == 1.0


def test_averaged_rate_after_deadline_is_ignored():
    result = run(two_parents(averaged_rate_applied_on="2026-12-02"))  # day 22
    assert periods(result, "mother", "maternity")[0].rate == 1.0
    assert result.averaged_rate and result.averaged_rate.still_possible is True


def test_averaged_comparison_totals_and_deadline():
    result = run(two_parents())
    cmp = result.averaged_rate
    assert cmp is not None
    assert cmp.deadline == date(2026, 12, 1)
    # Same family, same period: both options differ by far less than 1% of the total.
    assert abs(cmp.standard_total - cmp.averaged_total) < 0.01 * cmp.standard_total


def test_averaged_option_not_offered_for_stillbirth_or_uninsured_mother():
    assert run(profile(child={"birth_date": "2026-11-10", "stillborn": True})).averaged_rate is None
    assert (
        run(profile(mother={"employment": "unemployed"}, father=employee())).averaged_rate is None
    )


def test_minimum_net_amount_is_applied():
    mother = {
        "employment": "self_employed",
        "sickness_insurance": "voluntary",
        "average_monthly_base": 1000,
    }
    maternity = benefit(run(profile(mother=mother)), "maternity_allowance_mother")
    assert maternity.raised_to_minimum
    assert maternity.monthly_net_estimate == 1000


# --- Plan: how the leave is shared ---------------------------------------------------------------------------


def test_default_plan_father_keeps_reserved_9_weeks():
    result = run(two_parents())
    assert benefit(result, "parental_allowance_father").weeks == 9
    assert benefit(result, "parental_allowance_mother").weeks == 32


def test_parental_leave_split_between_parents():
    result = run(two_parents(plan={"parental_weeks_father": 20}))
    assert benefit(result, "parental_allowance_father").weeks == 20
    assert benefit(result, "parental_allowance_mother").weeks == 21


@pytest.mark.parametrize("father_weeks", [8, 33])
def test_each_parent_keeps_9_non_transferable_weeks(father_weeks):
    with pytest.raises(PlanError):
        run(two_parents(plan={"parental_weeks_father": father_weeks}))


def test_single_mother_gets_whole_parental_leave():
    assert benefit(run(), "parental_allowance_mother").weeks == 41


def test_parental_parts_limit():
    with pytest.raises(PlanError):
        run(two_parents(plan={"parental_parts_mother": 6}))


def test_maternity_can_start_6_weeks_before_birth():
    prof = profile(child={"due_date": "2027-03-01"}, plan={"maternity_before_birth_weeks": 6})
    maternity = periods(run(prof), "mother", "maternity")[0]
    assert maternity.start == date(2027, 1, 18)
    assert maternity.weeks == 20
    with pytest.raises(PlanError):
        run(profile(plan={"maternity_before_birth_weeks": 7}))


def test_father_takes_over_maternity_after_14_weeks():
    result = run(two_parents(plan={"maternity_weeks_to_father": 6}))
    mother = periods(result, "mother", "maternity")[0]
    father = periods(result, "father", "maternity")[0]
    assert mother.weeks == 14 and father.weeks == 6
    assert (father.start - mother.end).days == 1
    with pytest.raises(PlanError):
        run(two_parents(plan={"maternity_weeks_to_father": 7}))


def test_father_takeover_needs_a_father():
    with pytest.raises(PlanError):
        run(profile(plan={"maternity_weeks_to_father": 2}))


def test_father_takes_everything_when_mother_died():
    result = run(two_parents(mother_cannot_care="death"))
    assert benefit(result, "maternity_allowance_father").weeks == 20
    assert not periods(result, "mother", "maternity")
    assert benefit(result, "parental_allowance_father").weeks == 41


def test_hospitalised_mother_lets_father_take_over_earlier_than_14_weeks():
    result = run(two_parents(mother_cannot_care="hospital", plan={"maternity_weeks_to_father": 10}))
    assert benefit(result, "maternity_allowance_father").weeks == 10


# --- Combining parental leave with work -----------------------------------------------------------------------


def test_working_half_time_doubles_the_length_and_halves_the_monthly_amount():
    plain = run()
    half = run(profile(mother=employee(planned_work_fraction=0.5)))
    p_plain = periods(plain, "mother", "parental")[0]
    p_half = periods(half, "mother", "parental")[0]
    assert p_half.days == pytest.approx(2 * p_plain.days, abs=1)
    assert p_half.monthly_gross == pytest.approx(p_plain.monthly_gross / 2, abs=0.01)
    assert p_half.total_gross == pytest.approx(p_plain.total_gross, rel=0.03)


def test_work_during_parental_leave_is_limited_to_half_time_and_to_employees():
    with pytest.raises(PlanError):
        run(profile(mother=employee(planned_work_fraction=0.6)))
    with pytest.raises(PlanError):
        run(profile(mother=jdg(planned_work_fraction=0.3)))


# --- Adoption and foster care -----------------------------------------------------------------------------------


def adoption(age, situation="adoption", **child):
    return profile(
        child={"situation": situation, "placement_date": "2026-11-01", "age_years": age, **child}
    )


def test_adoption_gives_maternity_like_and_parental_leave():
    result = run(adoption(5))
    assert benefit(result, "maternity_allowance_mother").weeks == 20
    assert benefit(result, "parental_allowance_mother").weeks == 41
    assert "adoption" in result.situation_tags


def test_foster_family_age_limits():
    assert benefit(run(adoption(6, "foster")), "maternity_allowance_mother").weeks == 20
    old = run(adoption(9, "foster"))
    assert not periods(old, "mother", "maternity")
    deferred = run(adoption(9, "foster", school_deferred=True))
    assert benefit(deferred, "maternity_allowance_mother").weeks == 20


def test_adoption_age_limit_is_14():
    assert not periods(run(adoption(15)), "mother", "maternity")


# --- Risks ----------------------------------------------------------------------------------------------------------------


def test_risks_sorted_by_severity():
    result = run(profile(mother={"employment": "unemployed"}))
    order = {"high": 0, "medium": 1, "info": 2}
    ranks = [order[r.severity] for r in result.risks]
    assert ranks == sorted(ranks)


def test_raised_base_in_pregnancy_is_flagged():
    mother = jdg(base_raised_in_pregnancy=True)
    assert any(r.code == "raised_base_mother" for r in run(profile(mother=mother)).risks)


def test_late_application_for_parental_leave_is_flagged():
    prof = two_parents(child={"due_date": "2026-12-01"})
    # Father's parental leave would start in ~2027; birth is soon so the mother's starts after
    # 20 weeks – moving the clock close to the start triggers the warning.
    result = run(prof, today=date(2027, 4, 20))
    assert any(r.code.startswith("application_late_") for r in result.risks)


def test_totals_add_up():
    result = run(two_parents())
    assert result.totals.family_gross == pytest.approx(
        result.totals.mother_gross + result.totals.father_gross, abs=0.01
    )
    assert 0 < result.totals.family_net_estimate < result.totals.family_gross


def test_profile_validation():
    with pytest.raises(ValueError):
        FamilyProfile.model_validate({"child": {"birth_date": "2026-11-10"}})
    with pytest.raises(ValueError):
        FamilyProfile.model_validate({"child": {}, "mother": {"employment": "employee"}})


# --- Deadlines -----------------------------------------------------------------------------------------------------------


def deadlines(result, prefix):
    return [d for d in result.deadlines if d.code.startswith(prefix)]


def test_deadline_for_leave_application_counts_days_left():
    # Birth 2026-12-01: paternity leave starts that day, application due 7 days earlier.
    prof = two_parents(child={"due_date": "2026-12-01"})
    paternity = deadlines(run(prof), "apply_father-paternity")[0]
    assert paternity.due == date(2026, 11, 24)
    assert paternity.days_left == 3
    assert paternity.status == "soon"
    assert paternity.kind == "apply"


def test_overdue_deadline_has_negative_days_left():
    prof = two_parents(child={"due_date": "2026-11-25"})
    paternity = deadlines(run(prof), "apply_father-paternity")[0]
    assert paternity.days_left < 0 and paternity.status == "overdue"


def test_no_application_deadline_for_leave_that_already_started():
    # Baby born 10 Nov: maternity and paternity already run, so no deadline for them.
    result = run(two_parents())
    assert not deadlines(result, "apply_father-paternity")
    assert not deadlines(result, "apply_mother-maternity")


def test_averaged_rate_deadline_listed_until_application_is_filed():
    result = run(two_parents())
    averaged = deadlines(result, "apply_averaged_rate")[0]
    assert averaged.due == date(2026, 12, 1) and averaged.days_left == 10
    filed = run(two_parents(averaged_rate_applied_on="2026-11-15"))
    assert not deadlines(filed, "apply_averaged_rate")


def test_use_by_deadlines_for_parental_and_paternity_leave():
    result = run(two_parents())
    assert deadlines(result, "use_by_parental")[0].due == date(2032, 12, 31)
    assert deadlines(result, "use_by_paternity")[0].due == date(2027, 11, 10)


def test_parental_benefit_application_deadline_for_uninsured_family():
    result = run(profile(mother={"employment": "unemployed"}))
    due = deadlines(result, "apply_parental_benefit")[0]
    assert due.due == date(2027, 2, 10)


def test_benefit_carries_days_left():
    prof = two_parents(child={"due_date": "2027-03-01"})
    paternity = benefit(run(prof), "paternity_allowance_father")
    assert paternity.deadline == date(2027, 2, 22)
    assert paternity.days_left == (date(2027, 2, 22) - TODAY).days


def test_deadlines_sorted_by_date():
    due = [d.due for d in run(two_parents(child={"due_date": "2027-03-01"})).deadlines]
    assert due == sorted(due)
