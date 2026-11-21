"""Legal parameters valid in 2026.

Each entry becomes one `legal_parameter` row. Values are plain JSON: numbers, or objects
for tables (note: JSON object keys are always strings, e.g. {"1": 20} for one child).
`legal_basis` is cited at the level we are sure of; precise articles are verified in E1/E8.
"""

from datetime import date

BENEFITS_ACT = (
    "Ustawa z 25.06.1999 o świadczeniach pieniężnych z ubezpieczenia społecznego "
    "w razie choroby i macierzyństwa (ustawa zasiłkowa)"
)
LABOR_CODE = "Kodeks pracy"
MIN_WAGE_REG = "Rozporządzenie Rady Ministrów w sprawie minimalnego wynagrodzenia za pracę"
TO_VERIFY = "do weryfikacji artykułu"

Y2026 = date(2026, 1, 1)


def p(key: str, value, description_pl: str, legal_basis: str) -> dict:
    return {
        "key": key,
        "value": value,
        "description_pl": description_pl,
        "legal_basis": legal_basis,
    }


PARAMETERS: list[dict] = [
    # --- Maternity leave ----------------------------------------------------------------------
    p(
        "maternity_leave_weeks",
        {"1": 20, "2": 31, "3": 33, "4": 35, "5": 37},
        "Wymiar urlopu macierzyńskiego w tygodniach wg liczby dzieci urodzonych "
        "przy jednym porodzie (5 = pięcioro i więcej).",
        f"{LABOR_CODE}, art. 180",
    ),
    p(
        "maternity_before_birth_max_weeks",
        6,
        "Maksymalna część urlopu macierzyńskiego, którą można wykorzystać "
        "przed przewidywaną datą porodu.",
        f"{LABOR_CODE}, art. 180",
    ),
    p(
        "maternity_mother_mandatory_weeks",
        14,
        "Część urlopu macierzyńskiego, którą matka musi wykorzystać osobiście "
        "(po tym czasie może przekazać resztę ojcu).",
        f"{LABOR_CODE}, art. 180",
    ),
    p(
        "supplementary_maternity_max_weeks",
        {"short": 8, "long": 15},
        "Uzupełniający urlop macierzyński (wcześniaki / dziecko w szpitalu): "
        "do 8 lub do 15 tygodni zależnie od sytuacji dziecka.",
        f"{LABOR_CODE} (urlop uzupełniający, od 2025 r.) – {TO_VERIFY}",
    ),
    p(
        "stillbirth_maternity_weeks",
        8,
        "Urlop macierzyński po urodzeniu martwego dziecka lub zgonie dziecka "
        "przed ukończeniem 8 tygodni życia.",
        f"{LABOR_CODE}, art. 180",
    ),
    p(
        "child_death_min_days",
        7,
        "Minimalny okres urlopu macierzyńskiego przysługujący od dnia zgonu dziecka.",
        f"{LABOR_CODE}, art. 180",
    ),
    # --- Parental leave -----------------------------------------------------------------------
    p(
        "parental_leave_weeks",
        {"single": 41, "multiple": 43, "za_zyciem_single": 65, "za_zyciem_multiple": 67},
        "Wymiar urlopu rodzicielskiego (łącznie dla obojga rodziców); wyższe wartości "
        "dla dziecka z zaświadczeniem „Za życiem”.",
        f"{LABOR_CODE}, art. 182¹ᵃ",
    ),
    p(
        "parental_non_transferable_weeks",
        9,
        "Część urlopu rodzicielskiego zarezerwowana dla każdego z rodziców "
        "– nie można jej przenieść na drugiego.",
        f"{LABOR_CODE}, art. 182¹ᵃ",
    ),
    p(
        "parental_max_parts",
        5,
        "Maksymalna liczba części, na które można podzielić urlop rodzicielski.",
        f"{LABOR_CODE}, art. 182¹ᵃ",
    ),
    p(
        "parental_deadline_child_age_years",
        6,
        "Urlop rodzicielski trzeba wykorzystać do końca roku kalendarzowego, "
        "w którym dziecko kończy tyle lat.",
        f"{LABOR_CODE}, art. 182¹ᵃ",
    ),
    # --- Paternity leave ----------------------------------------------------------------------
    p(
        "paternity_leave_days",
        14,
        "Wymiar urlopu ojcowskiego w dniach.",
        f"{LABOR_CODE}, art. 182³",
    ),
    p(
        "paternity_max_parts",
        2,
        "Maksymalna liczba części urlopu ojcowskiego.",
        f"{LABOR_CODE}, art. 182³",
    ),
    p(
        "paternity_min_part_days",
        7,
        "Minimalna długość jednej części urlopu ojcowskiego (w dniach).",
        f"{LABOR_CODE}, art. 182³",
    ),
    p(
        "paternity_deadline_months",
        12,
        "Urlop ojcowski trzeba wykorzystać, zanim dziecko skończy tyle miesięcy.",
        f"{LABOR_CODE}, art. 182³",
    ),
    # --- Benefit rates ------------------------------------------------------------------------
    p(
        "rate_maternity",
        1.00,
        "Stawka zasiłku macierzyńskiego za okres urlopu macierzyńskiego, "
        "uzupełniającego i ojcowskiego (100% podstawy).",
        f"{BENEFITS_ACT}, art. 31",
    ),
    p(
        "rate_parental",
        0.70,
        "Stawka zasiłku za okres urlopu rodzicielskiego (70% podstawy).",
        f"{BENEFITS_ACT}, art. 31",
    ),
    p(
        "rate_averaged",
        0.815,
        "Uśredniona stawka (81,5%) za cały okres macierzyńskiego i rodzicielskiego, "
        "gdy wniosek złożono w terminie; 9 tygodni drugiego rodzica nadal po 70%.",
        f"{BENEFITS_ACT}, art. 31",
    ),
    p(
        "averaged_application_deadline_days",
        21,
        "Termin (dni od porodu) na złożenie wniosku o łączny urlop, "
        "aby otrzymać stawkę uśrednioną 81,5%.",
        f"{LABOR_CODE}, art. 180; {BENEFITS_ACT}, art. 31",
    ),
    p(
        "rate_sickness_pregnancy",
        1.00,
        "Stawka zasiłku chorobowego za niezdolność do pracy w okresie ciąży (kod B na zwolnieniu).",
        f"{BENEFITS_ACT}, art. 11",
    ),
    p(
        "rate_care_allowance",
        0.80,
        "Stawka zasiłku opiekuńczego (do potwierdzenia).",
        f"{BENEFITS_ACT} – {TO_VERIFY}",
    ),
    # --- Calculation base ---------------------------------------------------------------------
    p(
        "social_contribution_deduction",
        0.1371,
        "Potrącenie składek społecznych finansowanych przez ubezpieczonego (13,71%) "
        "przy liczeniu podstawy wymiaru.",
        BENEFITS_ACT,
    ),
    p(
        "minimum_wage",
        4806.00,
        "Minimalne wynagrodzenie za pracę (zł brutto) – dolna granica podstawy "
        "wymiaru dla pracowników.",
        f"{MIN_WAGE_REG} w 2026 r.",
    ),
    p(
        "minimum_maternity_benefit_net",
        1000.00,
        "Minimalna miesięczna kwota zasiłku macierzyńskiego netto.",
        f"{BENEFITS_ACT} – {TO_VERIFY}",
    ),
    # --- Payer and contribution debt ----------------------------------------------------------
    p(
        "payer_threshold_insured",
        20,
        "Płatnik zgłaszający więcej niż tylu ubezpieczonych wypłaca zasiłki sam; "
        "mniejsi płatnicy i JDG – wypłaca ZUS.",
        f"{BENEFITS_ACT}, art. 61",
    ),
    p(
        "contribution_debt_threshold_ratio",
        0.01,
        "Zadłużenie składkowe do 1% minimalnego wynagrodzenia nie blokuje wypłaty zasiłku.",
        f"{BENEFITS_ACT} – {TO_VERIFY}",
    ),
    p(
        "debt_repayment_window_months",
        6,
        "Spłata zadłużenia w tym terminie przywraca prawo do zasiłku za cały okres; "
        "po terminie – od dnia spłaty.",
        f"{BENEFITS_ACT} – {TO_VERIFY}",
    ),
    # --- Sickness benefit ---------------------------------------------------------------------
    p(
        "sickness_waiting_days",
        {"mandatory": 30, "voluntary": 90},
        "Okres wyczekiwania na zasiłek chorobowy: 30 dni przy ubezpieczeniu "
        "obowiązkowym, 90 przy dobrowolnym.",
        f"{BENEFITS_ACT}, art. 4",
    ),
    p(
        "sickness_employer_paid_days",
        33,
        "Liczba dni w roku, za które wynagrodzenie chorobowe płaci pracodawca "
        "(potem zasiłek z ZUS).",
        f"{LABOR_CODE}, art. 92",
    ),
    p(
        "sickness_benefit_period_days",
        270,
        "Maksymalny okres zasiłkowy przy niezdolności do pracy w czasie ciąży.",
        f"{BENEFITS_ACT}, art. 8",
    ),
    # --- Care allowance -----------------------------------------------------------------------
    p(
        "care_allowance_limits_days",
        {
            "child_under_8_or_sick_under_14": 60,
            "other": 14,
            "disabled_14_17": 30,
            "total_cap": 60,
        },
        "Roczne limity dni zasiłku opiekuńczego wg sytuacji; łącznie nie więcej niż 60 dni.",
        f"{BENEFITS_ACT}, art. 32–33",
    ),
]

# Older versions kept to show (and test) how validity periods work.
HISTORICAL: list[dict] = [
    {
        **p(
            "minimum_wage",
            4666.00,
            "Minimalne wynagrodzenie za pracę w 2025 r. (zł brutto).",
            f"{MIN_WAGE_REG} w 2025 r.",
        ),
        "valid_from": date(2025, 1, 1),
        "valid_to": date(2025, 12, 31),
    },
]


def all_rows() -> list[dict]:
    rows = [{**param, "valid_from": Y2026, "valid_to": None} for param in PARAMETERS]
    return rows + HISTORICAL
