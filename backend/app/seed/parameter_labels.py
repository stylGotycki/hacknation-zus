"""Polish names, groups and units of legal parameters, shown in the admin panel.

Stored in the database next to each parameter version (columns `label_pl`, `group_pl`, `unit`,
`value_labels`), so the panel never shows technical keys. Units:
  weeks, days, months, years – durations; pct – a fraction shown as a percentage (0.815 → 81,5%);
  pln – złoty; people, grams – counts; number – a plain number.
"""

U = dict  # short alias for readability


def _counts(unit: str = "weeks") -> dict:
    return {
        "items": {
            "1": "1 dziecko",
            "2": "2 dzieci",
            "3": "3 dzieci",
            "4": "4 dzieci",
            "5": "5 i więcej",
        },
        "unit": unit,
    }


LABELS: dict[str, dict] = {
    # --- Urlop macierzyński --------------------------------------------------------------------
    "maternity_leave_weeks": U(
        group="Urlop macierzyński", label="Wymiar urlopu macierzyńskiego", **_counts()
    ),
    "maternity_before_birth_max_weeks": U(
        group="Urlop macierzyński", label="Najwięcej przed porodem", unit="weeks"
    ),
    "maternity_mother_mandatory_weeks": U(
        group="Urlop macierzyński",
        label="Matka wykorzystuje osobiście (przed przekazaniem ojcu)",
        unit="weeks",
    ),
    "maternity_mother_min_weeks_disabled": U(
        group="Urlop macierzyński",
        label="Jw. przy niezdolności matki do samodzielnej egzystencji",
        unit="weeks",
    ),
    "maternity_min_weeks_before_transfer": U(
        group="Urlop macierzyński",
        label="Szpital matki / porzucenie – po tylu tygodniach",
        unit="weeks",
    ),
    "supplementary_maternity_max_weeks": U(
        group="Urlop macierzyński",
        label="Uzupełniający urlop macierzyński – najwięcej",
        unit="weeks",
        items={"short": "po 28. tyg. ciąży / w terminie", "long": "przed 28. tyg. lub do 1000 g"},
    ),
    "supplementary_criteria": U(
        group="Urlop macierzyński",
        label="Uzupełniający urlop – kryteria",
        unit="number",
        items={
            "long_gestation_below": "Skrajny wcześniak: urodzony przed tyg. ciąży",
            "long_weight_max_g": "Skrajny wcześniak: masa do (g)",
            "preterm_gestation_below": "Wcześniak: urodzony przed tyg. ciąży",
            "term_min_stay_days": "Dziecko w terminie: min. kolejnych dni w szpitalu",
            "term_first_day_from": "Dziecko w terminie: pierwszy dzień pobytu od dnia",
            "term_first_day_to": "Dziecko w terminie: pierwszy dzień pobytu do dnia",
        },
    ),
    "stillbirth_maternity_weeks": U(
        group="Urlop macierzyński", label="Martwe urodzenie / zgon do 8 tyg.", unit="weeks"
    ),
    "stillbirth_child_death_weeks_limit": U(
        group="Urlop macierzyński", label="Granica wieku dziecka przy zgonie", unit="weeks"
    ),
    "child_death_min_days": U(
        group="Urlop macierzyński", label="Co najmniej od dnia zgonu", unit="days"
    ),
    # --- Przyjęcie dziecka ---------------------------------------------------------------------
    "taken_in_min_maternity_weeks": U(
        group="Przyjęcie dziecka na wychowanie",
        label="Urlop na warunkach macierzyńskiego – co najmniej",
        unit="weeks",
    ),
    "adoption_leave_max_child_age_years": U(
        group="Przyjęcie dziecka na wychowanie",
        label="Wiek dziecka – najwięcej",
        unit="years",
        items={
            "adoption": "Przysposobienie",
            "foster": "Rodzina zastępcza",
            "foster_school_deferred": "Rodzina zastępcza, odroczony obowiązek szkolny",
        },
    ),
    # --- Urlop rodzicielski --------------------------------------------------------------------
    "parental_leave_weeks": U(
        group="Urlop rodzicielski",
        label="Wymiar urlopu rodzicielskiego",
        unit="weeks",
        items={
            "single": "1 dziecko",
            "multiple": "2 i więcej dzieci",
            "za_zyciem_single": "„Za życiem”, 1 dziecko",
            "za_zyciem_multiple": "„Za życiem”, 2 i więcej",
            "taken_in_short": "Przyjęcie – przypadek art. 183 § 3",
            "za_zyciem_taken_in_short": "Przyjęcie – art. 183 § 3, „Za życiem”",
        },
    ),
    "parental_non_transferable_weeks": U(
        group="Urlop rodzicielski", label="Nieprzenoszalna część każdego rodzica", unit="weeks"
    ),
    "parental_max_parts": U(group="Urlop rodzicielski", label="Najwięcej części", unit="number"),
    "parental_deadline_child_age_years": U(
        group="Urlop rodzicielski", label="Do końca roku, w którym dziecko kończy", unit="years"
    ),
    "parental_work_max_fraction": U(
        group="Urlop rodzicielski", label="Praca w trakcie urlopu – najwięcej etatu", unit="pct"
    ),
    "parental_with_work_max_weeks": U(
        group="Urlop rodzicielski",
        label="Urlop łączony z pracą – najdłużej",
        unit="weeks",
        items={
            "single": "1 dziecko",
            "multiple": "2 i więcej dzieci",
            "za_zyciem_single": "„Za życiem”, 1 dziecko",
            "za_zyciem_multiple": "„Za życiem”, 2 i więcej",
        },
    ),
    # --- Urlop ojcowski ------------------------------------------------------------------------
    "paternity_leave_weeks": U(
        group="Urlop ojcowski", label="Wymiar urlopu ojcowskiego", unit="weeks"
    ),
    "paternity_max_parts": U(group="Urlop ojcowski", label="Najwięcej części", unit="number"),
    "paternity_min_part_weeks": U(group="Urlop ojcowski", label="Najkrótsza część", unit="weeks"),
    "paternity_deadline_months": U(
        group="Urlop ojcowski", label="Do ukończenia przez dziecko", unit="months"
    ),
    # --- Stawki --------------------------------------------------------------------------------
    "rate_maternity": U(
        group="Stawki zasiłku",
        label="Macierzyński, na warunkach, uzupełniający, ojcowski",
        unit="pct",
    ),
    "rate_parental": U(
        group="Stawki zasiłku", label="Rodzicielski (i 9 tyg. drugiego rodzica)", unit="pct"
    ),
    "rate_averaged": U(
        group="Stawki zasiłku", label="Stawka uśredniona (wniosek z art. 30a)", unit="pct"
    ),
    "rate_sickness": U(group="Stawki zasiłku", label="Chorobowy – podstawowa", unit="pct"),
    "rate_sickness_pregnancy": U(
        group="Stawki zasiłku", label="Chorobowy w ciąży (kod B)", unit="pct"
    ),
    "rate_rehabilitation": U(
        group="Stawki zasiłku",
        label="Świadczenie rehabilitacyjne",
        unit="pct",
        items={
            "first_3_months": "Pierwsze 3 miesiące",
            "later": "Pozostały okres",
            "pregnancy": "W okresie ciąży",
        },
    ),
    "rate_care_allowance": U(group="Stawki zasiłku", label="Opiekuńczy", unit="pct"),
    # --- Podstawa i kwoty ----------------------------------------------------------------------
    "social_contribution_deduction": U(
        group="Podstawa i kwoty", label="Potrącenie składek z podstawy", unit="pct"
    ),
    "minimum_wage": U(group="Podstawa i kwoty", label="Minimalne wynagrodzenie", unit="pln"),
    "voluntary_sickness_base_max": U(
        group="Podstawa i kwoty",
        label="Najwyższa podstawa dobrowolnej składki chorobowej",
        unit="pln",
    ),
    "benefit_daily_divisor": U(
        group="Podstawa i kwoty", label="Dzielnik dzienny zasiłku", unit="days"
    ),
    "parental_benefit_amount": U(
        group="Podstawa i kwoty",
        label="Kwota świadczenia rodzicielskiego (podwyższenie)",
        unit="pln",
    ),
    # --- Uprawnienia i płatnik -----------------------------------------------------------------
    "payer_threshold_insured": U(
        group="Uprawnienia i płatnik",
        label="Płatnik wypłaca, gdy zgłasza więcej niż",
        unit="people",
    ),
    "contribution_debt_threshold_ratio": U(
        group="Uprawnienia i płatnik",
        label="Dopuszczalny dług składkowy (część płacy min.)",
        unit="pct",
    ),
    "debt_repayment_window_months": U(
        group="Uprawnienia i płatnik",
        label="Spłata długu – inaczej przedawnienie po",
        unit="months",
    ),
    "debt_payment_days_after_repayment": U(
        group="Uprawnienia i płatnik", label="Wypłata po spłacie długu – najpóźniej", unit="days"
    ),
    "gestation_months_for_contract_extension": U(
        group="Uprawnienia i płatnik",
        label="Umowa terminowa przedłużona do porodu – po miesiącu ciąży",
        unit="months",
    ),
    # --- Chorobowy w ciąży ---------------------------------------------------------------------
    "sickness_waiting_days": U(
        group="Zasiłek chorobowy w ciąży",
        label="Okres wyczekiwania",
        unit="days",
        items={"mandatory": "Ubezpieczenie obowiązkowe", "voluntary": "Ubezpieczenie dobrowolne"},
    ),
    "sickness_employer_paid_days": U(
        group="Zasiłek chorobowy w ciąży",
        label="Wynagrodzenie chorobowe od pracodawcy",
        unit="days",
    ),
    "employer_sickness_paid_days_over_50": U(
        group="Zasiłek chorobowy w ciąży",
        label="Wynagrodzenie chorobowe – po 50. roku życia",
        unit="days",
    ),
    "sickness_benefit_period_days": U(
        group="Zasiłek chorobowy w ciąży",
        label="Okres zasiłkowy",
        unit="days",
        items={
            "standard": "Zwykły",
            "pregnancy": "W ciąży",
            "after_insurance": "Po ustaniu ubezpieczenia",
        },
    ),
    "sickness_break_days": U(
        group="Zasiłek chorobowy w ciąży", label="Przerwa sumująca okresy niezdolności", unit="days"
    ),
    "rehabilitation_max_months": U(
        group="Zasiłek chorobowy w ciąży",
        label="Świadczenie rehabilitacyjne – najdłużej",
        unit="months",
    ),
    # --- Terminy -------------------------------------------------------------------------------
    "averaged_application_deadline_days": U(
        group="Terminy wniosków", label="Wniosek o stawkę uśrednioną – po porodzie", unit="days"
    ),
    "application_lead_days": U(
        group="Terminy wniosków",
        label="Wnioski pracownika",
        unit="days",
        items={
            "maternity_before_birth": "Urlop przed porodem – przed",
            "father_maternity_part": "Część macierzyńskiego dla ojca – przed",
            "mother_resignation": "Rezygnacja matki – przed powrotem",
            "supplementary": "Uzupełniający – przed końcem macierzyńskiego",
            "parental": "Rodzicielski – przed",
            "work_combination": "Praca w trakcie rodzicielskiego – przed",
            "paternity": "Ojcowski – przed",
            "taken_in_application": "Na warunkach macierzyńskiego – od przyjęcia",
            "taken_in_start_max": "Na warunkach macierzyńskiego – początek najpóźniej",
        },
    ),
    "claim_limitation_months": U(
        group="Terminy wniosków", label="Przedawnienie roszczenia o zasiłek", unit="months"
    ),
    "payment_deadline_days": U(
        group="Terminy wniosków", label="Wypłata zasiłku – najpóźniej", unit="days"
    ),
    "payout_day": U(
        group="Terminy wniosków", label="Dzień przelewu zasiłku w miesiącu", unit="number"
    ),
    # --- Inne -----------------------------------------------------------------------------------
    "care_allowance_limits_days": U(
        group="Inne świadczenia",
        label="Zasiłek opiekuńczy – limity w roku",
        unit="days",
        items={
            "child_under_14": "Dzieci do 14 lat",
            "disabled_child_14_18": "Chore dziecko z niepełnosprawnością 14–18",
            "other": "Dziecko pow. 14 lat / dorosły członek rodziny",
            "total_cap": "Łącznie w roku",
        },
    ),
    "funeral_allowance_stillbirth": U(
        group="Inne świadczenia", label="Zasiłek pogrzebowy – martwe urodzenie", unit="pln"
    ),
    "funeral_application_months": U(
        group="Inne świadczenia", label="Zasiłek pogrzebowy – wniosek w ciągu", unit="months"
    ),
    "birth_grant_amount": U(
        group="Inne świadczenia", label="Becikowe – kwota na jedno dziecko", unit="pln"
    ),
    "birth_grant_months": U(
        group="Inne świadczenia", label="Becikowe – wniosek w ciągu (od urodzenia)", unit="months"
    ),
}

GROUP_ORDER = [
    "Stawki zasiłku",
    "Urlop macierzyński",
    "Urlop rodzicielski",
    "Urlop ojcowski",
    "Przyjęcie dziecka na wychowanie",
    "Podstawa i kwoty",
    "Uprawnienia i płatnik",
    "Terminy wniosków",
    "Zasiłek chorobowy w ciąży",
    "Inne świadczenia",
]


def label_fields(key: str) -> dict:
    """Columns stored with each version of `key` (fallbacks keep unknown keys visible)."""
    meta = LABELS.get(key, {})
    return {
        "label_pl": meta.get("label", key),
        "group_pl": meta.get("group", "Inne"),
        "unit": meta.get("unit", "number"),
        "value_labels": meta.get("items", {}),
    }
