"""Legal parameters valid in 2026 – only values found in the six source documents.

Sources (field `legal_basis` cites the exact place):
  KP  – Kodeks pracy, wyciąg (t.j. Dz.U. 2026 poz. 1245)
  UZ  – ustawa zasiłkowa, wyciąg (t.j. Dz.U. 2026 poz. 854)
  RZ  – rozporządzenie z 27.09.2026 w sprawie dokumentów do zasiłków (Dz.U. 2026 poz. 1316)
  RW  – rozporządzenie z 11.03.2025 w sprawie wniosków pracowniczych (Dz.U. 2025 poz. 322)
  PR  – Poradnik dla rodziców i opiekunów dzieci, ZUS 2026 (stan prawny 1.04.2026)
  ZAL – Załącznik do wyzwania HackNation 2026 (wymiary, wysokość, podstawa wymiaru)
A value that none of the sources gives is stored as null and must be entered in the admin panel.
"""

from datetime import date

from app.seed.parameter_labels import label_fields

KP = "Kodeks pracy"
UZ = "Ustawa zasiłkowa"
PR = "Poradnik ZUS dla rodziców 2026"
ZAL = "Załącznik do wyzwania"

Y2026 = date(2026, 1, 1)


def p(key: str, value, description_pl: str, legal_basis: str) -> dict:
    return {
        "key": key,
        "value": value,
        "description_pl": description_pl,
        "legal_basis": legal_basis,
    }


COUNT = lambda a, b, c, d, e: {"1": a, "2": b, "3": c, "4": d, "5": e}  # noqa: E731

PARAMETERS: list[dict] = [
    # --- Urlop macierzyński / na warunkach urlopu macierzyńskiego ------------------------------
    p(
        "maternity_leave_weeks",
        COUNT(20, 31, 33, 35, 37),
        "Wymiar urlopu macierzyńskiego (i urlopu na warunkach urlopu macierzyńskiego) wg liczby "
        "dzieci urodzonych przy jednym porodzie / przyjętych jednocześnie (5 = pięcioro i więcej).",
        f"{KP}, art. 180 § 1, art. 183 § 1 i § 1¹; {ZAL}",
    ),
    p(
        "maternity_before_birth_max_weeks",
        6,
        "Najwięcej urlopu macierzyńskiego przed przewidywaną datą porodu.",
        f"{KP}, art. 180 § 2",
    ),
    p(
        "maternity_mother_mandatory_weeks",
        14,
        "Matka może zrezygnować z reszty urlopu (zasiłku) na rzecz ojca po wykorzystaniu tylu tygodni po porodzie.",
        f"{KP}, art. 180 § 4; {UZ}, art. 29 ust. 3",
    ),
    p(
        "maternity_mother_min_weeks_disabled",
        8,
        "Jak wyżej, gdy matka ma orzeczenie o niezdolności do samodzielnej egzystencji.",
        f"{KP}, art. 180 § 6; {UZ}, art. 29 ust. 5",
    ),
    p(
        "maternity_min_weeks_before_transfer",
        8,
        "Po tylu tygodniach po porodzie część urlopu może przejść na ojca przy pobycie matki w szpitalu "
        "albo porzuceniu dziecka; przy porzuceniu urlop matki po porodzie nie może być krótszy.",
        f"{KP}, art. 180 § 10 i § 13, art. 182; {UZ}, art. 29 ust. 6 i 7",
    ),
    p(
        "supplementary_maternity_max_weeks",
        {"short": 8, "long": 15},
        "Uzupełniający urlop macierzyński: tydzień za każdy tydzień pobytu dziecka w szpitalu, do 15. tygodnia "
        "po porodzie (przed 28. tyg. ciąży lub ≤ 1000 g) albo do 8. tygodnia (pozostałe przypadki).",
        f"{KP}, art. 180² § 1; {ZAL}",
    ),
    p(
        "supplementary_criteria",
        {
            "long_gestation_below": 28,
            "long_weight_max_g": 1000,
            "preterm_gestation_below": 37,
            "term_min_stay_days": 2,
            "term_first_day_from": 5,
            "term_first_day_to": 28,
        },
        "Kryteria uzupełniającego urlopu macierzyńskiego.",
        f"{KP}, art. 180² § 1",
    ),
    p(
        "stillbirth_maternity_weeks",
        8,
        "Urlop macierzyński po urodzeniu martwego dziecka lub zgonie dziecka przed upływem 8 tygodni życia.",
        f"{KP}, art. 180¹ § 1",
    ),
    p(
        "stillbirth_child_death_weeks_limit",
        8,
        "Granica wieku dziecka (w tygodniach życia) przy zgonie dziecka.",
        f"{KP}, art. 180¹ § 1–2",
    ),
    p(
        "child_death_min_days",
        7,
        "Urlop macierzyński trwa co najmniej tyle dni od dnia zgonu dziecka.",
        f"{KP}, art. 180¹ § 1–2",
    ),
    p(
        "taken_in_min_maternity_weeks",
        9,
        "Urlop (zasiłek) na warunkach urlopu macierzyńskiego nie może trwać krócej niż 9 tygodni.",
        f"{KP}, art. 183 § 3; {ZAL}",
    ),
    p(
        "adoption_leave_max_child_age_years",
        {"adoption": 14, "foster": 7, "foster_school_deferred": 10},
        "Wiek dziecka przyjętego na wychowanie, do którego przysługuje urlop i zasiłek.",
        f"{UZ}, art. 29 ust. 1 pkt 2–3; {KP}, art. 183 § 1 i § 1¹",
    ),
    # --- Urlop rodzicielski --------------------------------------------------------------------
    p(
        "parental_leave_weeks",
        {
            "single": 41,
            "multiple": 43,
            "za_zyciem_single": 65,
            "za_zyciem_multiple": 67,
            "taken_in_short": 38,
            "za_zyciem_taken_in_short": 62,
        },
        "Wymiar urlopu rodzicielskiego dla obojga rodziców łącznie. „taken_in_short” – przy przyjęciu dziecka "
        "w przypadku z art. 183 § 3 KP (urlop na warunkach urlopu macierzyńskiego ograniczony do 9 tygodni).",
        f"{KP}, art. 182¹ᵃ § 1–3, art. 183 § 4–4⁵; {ZAL}",
    ),
    p(
        "parental_non_transferable_weeks",
        9,
        "Wyłączna, nieprzenoszalna część urlopu rodzicielskiego każdego z rodziców.",
        f"{KP}, art. 182¹ᵃ § 4–5; {UZ}, art. 31 ust. 3f",
    ),
    p(
        "parental_max_parts",
        5,
        "Urlop rodzicielski: jednorazowo albo najwyżej w tylu częściach.",
        f"{KP}, art. 182¹ᶜ, art. 183 § 4⁶",
    ),
    p(
        "parental_deadline_child_age_years",
        6,
        "Urlop rodzicielski najpóźniej do końca roku kalendarzowego, w którym dziecko kończy tyle lat.",
        f"{KP}, art. 182¹ᶜ",
    ),
    p(
        "parental_work_max_fraction",
        0.5,
        "Praca u pracodawcy udzielającego urlopu rodzicielskiego – najwyżej połowa pełnego wymiaru.",
        f"{KP}, art. 182¹ᵉ § 1",
    ),
    p(
        "parental_with_work_max_weeks",
        {"single": 82, "multiple": 86, "za_zyciem_single": 130, "za_zyciem_multiple": 134},
        "Urlop rodzicielski łączony z pracą wydłuża się proporcjonalnie, najdłużej do tylu tygodni.",
        f"{KP}, art. 182¹ᶠ § 1 i § 1¹",
    ),
    # --- Urlop ojcowski ------------------------------------------------------------------------
    p("paternity_leave_weeks", 2, "Wymiar urlopu ojcowskiego.", f"{KP}, art. 182³ § 1; {ZAL}"),
    p(
        "paternity_max_parts",
        2,
        "Urlop ojcowski jednorazowo albo najwyżej w tylu częściach.",
        f"{KP}, art. 182³ § 1¹",
    ),
    p(
        "paternity_min_part_weeks",
        1,
        "Najkrótsza część urlopu ojcowskiego.",
        f"{KP}, art. 182³ § 1¹",
    ),
    p(
        "paternity_deadline_months",
        12,
        "Urlop ojcowski do ukończenia przez dziecko 12 miesięcy (przysposobienie: 12 miesięcy od "
        "uprawomocnienia się postanowienia, nie dłużej niż do 14 lat).",
        f"{KP}, art. 182³ § 1",
    ),
    # --- Stawki --------------------------------------------------------------------------------
    p(
        "rate_maternity",
        1.0,
        "Zasiłek macierzyński za urlop macierzyński, na warunkach urlopu macierzyńskiego, uzupełniający i ojcowski.",
        f"{UZ}, art. 31 ust. 1",
    ),
    p(
        "rate_parental",
        0.7,
        "Zasiłek macierzyński za urlop rodzicielski.",
        f"{UZ}, art. 31 ust. 2 i 3f",
    ),
    p(
        "rate_averaged",
        0.815,
        "Stawka przy wniosku z art. 30a (cały urlop macierzyński i rodzicielski, poza 9 tygodniami drugiego rodzica).",
        f"{UZ}, art. 31 ust. 3",
    ),
    p(
        "averaged_application_deadline_days",
        21,
        "Wniosek o stawkę z art. 30a – najpóźniej tyle dni po porodzie (przyjęciu dziecka).",
        f"{UZ}, art. 30a ust. 1–2",
    ),
    p("rate_sickness", 0.8, "Zasiłek chorobowy – stawka podstawowa.", f"{UZ}, art. 11 ust. 1"),
    p(
        "rate_sickness_pregnancy",
        1.0,
        "Zasiłek chorobowy i wynagrodzenie chorobowe w okresie ciąży.",
        f"{UZ}, art. 11 ust. 2 pkt 1; {KP}, art. 92 § 1 pkt 2",
    ),
    p(
        "rate_rehabilitation",
        {"first_3_months": 0.9, "later": 0.75, "pregnancy": 1.0},
        "Świadczenie rehabilitacyjne.",
        f"{UZ}, art. 19 ust. 1",
    ),
    p("rate_care_allowance", 0.8, "Zasiłek opiekuńczy.", f"{PR}, rozdz. Zasiłek opiekuńczy"),
    # --- Podstawa wymiaru ----------------------------------------------------------------------
    p(
        "social_contribution_deduction",
        0.1371,
        "Potrącenie składek na ubezpieczenia społeczne przy ustalaniu podstawy wymiaru zasiłku.",
        f"{UZ}, art. 3 pkt 4, art. 45; {ZAL}",
    ),
    p(
        "minimum_wage",
        4806.0,
        "Minimalne wynagrodzenie w 2026 r. (zł brutto).",
        f"{ZAL}; {UZ}, art. 45",
    ),
    p(
        "voluntary_sickness_base_max",
        23550.0,
        "Najwyższa miesięczna podstawa dobrowolnej składki chorobowej w 2026 r. (po potrąceniu 13,71%: 20 321,30 zł).",
        f"{ZAL}; {PR} (250% prognozowanego przeciętnego wynagrodzenia)",
    ),
    p(
        "benefit_daily_divisor",
        30,
        "Zasiłek za jeden dzień = 1/30 miesięcznej podstawy; za miesiąc uważa się 30 dni.",
        f"{UZ}, art. 11 ust. 5, art. 36 ust. 3",
    ),
    p(
        "parental_benefit_amount",
        1000.0,
        "Kwota świadczenia rodzicielskiego, do której podwyższa się zasiłek macierzyński (art. 31 ust. 3a). "
        "Kwota (1000 zł) pochodzi z ustawy o świadczeniach rodzinnych, spoza sześciu źródeł – do potwierdzenia; "
        "silnik podwyższa do niej miesięczny zasiłek (porównanie brutto, bez zaliczki na podatek).",
        f"{UZ}, art. 31 ust. 3a–3c (kwota: ustawa o świadczeniach rodzinnych)",
    ),
    # --- Uprawnienia i płatnik -----------------------------------------------------------------
    p(
        "payer_threshold_insured",
        20,
        "Płatnik składek zgłaszający więcej ubezpieczonych sam wypłaca zasiłki; pozostałym wypłaca ZUS.",
        f"{UZ}, art. 61 ust. 1–2",
    ),
    p(
        "contribution_debt_threshold_ratio",
        0.01,
        "Zadłużenie składkowe ponad tę część minimalnego wynagrodzenia wstrzymuje świadczenia do spłaty.",
        f"{UZ}, art. 2a ust. 1",
    ),
    p(
        "debt_repayment_window_months",
        6,
        "Brak spłaty zadłużenia w tym czasie od dnia powstania prawa = przedawnienie prawa do świadczenia.",
        f"{UZ}, art. 2a ust. 2",
    ),
    p(
        "debt_payment_days_after_repayment",
        60,
        "Po spłacie zadłużenia zasiłek wypłaca się najpóźniej w tym terminie.",
        f"{UZ}, art. 64 ust. 3",
    ),
    p(
        "gestation_months_for_contract_extension",
        3,
        "Umowa terminowa (> 1 miesiąca), która rozwiązałaby się po upływie tego miesiąca ciąży, przedłuża się do porodu.",
        f"{KP}, art. 177 § 3",
    ),
    # --- Zasiłek chorobowy w ciąży --------------------------------------------------------------
    p(
        "sickness_waiting_days",
        {"mandatory": 30, "voluntary": 90},
        "Okres wyczekiwania na zasiłek chorobowy (ubezpieczenie obowiązkowe / dobrowolne).",
        f"{UZ}, art. 4 ust. 1",
    ),
    p(
        "sickness_employer_paid_days",
        33,
        "Dni niezdolności w roku, za które pracodawca płaci wynagrodzenie chorobowe.",
        f"{KP}, art. 92 § 1; {ZAL}",
    ),
    p(
        "employer_sickness_paid_days_over_50",
        14,
        "Jak wyżej, dla pracownika po roku, w którym ukończył 50 lat.",
        f"{KP}, art. 92 § 1 i § 5; {ZAL}",
    ),
    p(
        "sickness_benefit_period_days",
        {"standard": 182, "pregnancy": 270, "after_insurance": 91},
        "Okres zasiłkowy: zwykły, w ciąży, po ustaniu tytułu ubezpieczenia (nie dotyczy ciąży).",
        f"{UZ}, art. 8 ust. 1–2; {ZAL}",
    ),
    p(
        "sickness_break_days",
        60,
        "Przerwa między niezdolnościami, przy której okresy wlicza się do jednego okresu zasiłkowego "
        "(nie dotyczy nowej niezdolności w ciąży).",
        f"{UZ}, art. 9 ust. 2; {ZAL}",
    ),
    p(
        "rehabilitation_max_months",
        12,
        "Świadczenie rehabilitacyjne – najdłużej.",
        f"{UZ}, art. 18 ust. 2",
    ),
    # --- Terminy wniosków ----------------------------------------------------------------------
    p(
        "application_lead_days",
        {
            "maternity_before_birth": 14,
            "father_maternity_part": 14,
            "mother_resignation": 7,
            "supplementary": 21,
            "parental": 21,
            "work_combination": 21,
            "paternity": 7,
            "taken_in_application": 7,
            "taken_in_start_max": 21,
        },
        "Terminy wniosków pracownika (w dniach): przed rozpoczęciem urlopu, przed powrotem do pracy, "
        "przed końcem urlopu macierzyńskiego (uzupełniający) albo od przyjęcia dziecka.",
        f"{KP}, art. 177 § 1¹, 180 § 8–9, 180² § 4, 182¹ᵈ § 1, 182¹ᵉ § 2, 182³ § 2, 183 § 6; {PR}",
    ),
    p(
        "claim_limitation_months",
        6,
        "Roszczenie o wypłatę zasiłku przedawnia się po tylu miesiącach od ostatniego dnia okresu.",
        f"{UZ}, art. 67 ust. 1",
    ),
    p(
        "payment_deadline_days",
        30,
        "Zasiłek wypłaca się najpóźniej w tym terminie od wyjaśnienia ostatniej okoliczności.",
        f"{UZ}, art. 64 ust. 1",
    ),
    p(
        "payout_day",
        10,
        "Dzień miesiąca, w którym przychodzi przelew zasiłku za poprzedni miesiąc. Założenie planera – "
        "przepisy wskazują termin wypłaty wynagrodzeń (płatnik) albo „na bieżąco” (ZUS).",
        f"{UZ}, art. 64 ust. 1",
    ),
    # --- Inne świadczenia (Poradnik) -----------------------------------------------------------
    p(
        "care_allowance_limits_days",
        {"child_under_14": 60, "disabled_child_14_18": 30, "other": 14, "total_cap": 60},
        "Zasiłek opiekuńczy – limity w roku kalendarzowym.",
        f"{PR}, rozdz. Okres wypłaty zasiłku opiekuńczego",
    ),
    p(
        "funeral_allowance_stillbirth",
        7000.0,
        "Zasiłek pogrzebowy, gdy dziecko urodzi się martwe (pełna kwota niezależnie od kosztów).",
        f"{PR}, rozdz. Zasiłek pogrzebowy",
    ),
    p(
        "funeral_application_months",
        12,
        "Wniosek o zasiłek pogrzebowy – w ciągu tylu miesięcy od pochówku.",
        f"{PR}, rozdz. Zasiłek pogrzebowy",
    ),
    # Becikowe is NOT in the six sources: values from the Act on family benefits (art. 15b) and
    # gov.pl/web/gov/uzyskaj-becikowe. Editable in the admin panel.
    p(
        "birth_grant_amount",
        1000.0,
        "Becikowe – jednorazowa zapomoga z tytułu urodzenia dziecka, zł na jedno dziecko (niezależnie od dochodu).",
        "SR: ustawa o świadczeniach rodzinnych art. 15b (spoza sześciu źródeł; gov.pl – Uzyskaj becikowe)",
    ),
    p(
        "birth_grant_months",
        12,
        "Becikowe – wniosek do gminy w ciągu tylu miesięcy od urodzenia dziecka (po terminie – bez rozpoznania).",
        "SR: ustawa o świadczeniach rodzinnych art. 15b (spoza sześciu źródeł; gov.pl – Uzyskaj becikowe)",
    ),
]

# Older versions kept to show (and test) how validity periods work.
HISTORICAL: list[dict] = [
    {
        **p(
            "minimum_wage",
            4666.00,
            "Minimalne wynagrodzenie za pracę w 2025 r. (zł brutto).",
            "Rozporządzenie w sprawie minimalnego wynagrodzenia w 2025 r.",
        ),
        "valid_from": date(2025, 1, 1),
        "valid_to": date(2025, 12, 31),
    },
]


def all_rows() -> list[dict]:
    rows = [{**param, "valid_from": Y2026, "valid_to": None} for param in PARAMETERS]
    return [{**row, **label_fields(row["key"])} for row in rows + HISTORICAL]


def current_values() -> dict:
    """key -> value of the 2026 parameters (for tests and the seed check)."""
    return {row["key"]: row["value"] for row in PARAMETERS}
