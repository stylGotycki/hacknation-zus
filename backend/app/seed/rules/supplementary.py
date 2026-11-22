"""Rules: Uzupełniający urlop macierzyński."""

from __future__ import annotations

from app.seed.rules.helpers import (
    G_SUP,
    KP,
    P,
    V,
)

RULES: list[dict] = [
    # ======================================================================================
    # Uzupełniający urlop macierzyński
    # ======================================================================================
    V(
        "uzup_przypadek",
        "jesli(not dziecko_zyje or not (porod or przyjecie_w_limicie), 0, "
        "jesli(dziecko.tydzien_ciazy < tabela('supplementary_criteria', 'long_gestation_below') or "
        "dziecko.masa_g <= tabela('supplementary_criteria', 'long_weight_max_g'), 1, "
        "jesli(dziecko.tydzien_ciazy < tabela('supplementary_criteria', 'preterm_gestation_below'), 2, "
        "jesli(dziecko.dni_szpitala >= tabela('supplementary_criteria', 'term_min_stay_days') and "
        "dziecko.pierwszy_dzien_szpitala >= tabela('supplementary_criteria', 'term_first_day_from') and "
        "dziecko.pierwszy_dzien_szpitala <= tabela('supplementary_criteria', 'term_first_day_to'), 3, 0))))",
        "Przypadek uzupełniającego urlopu (1: < 28 tyg. lub ≤ 1000 g; 2: 28–36 tyg.; 3: w terminie, szpital od 5.–28. dnia)",
        "KP art. 180² § 1–2, art. 183 § 3¹",
        KP,
        G_SUP,
    ),
    V(
        "uzup_limit_tyg",
        "jesli(uzup_przypadek == 1, tabela('supplementary_maternity_max_weeks', 'long'), "
        "jesli(uzup_przypadek in [2, 3], tabela('supplementary_maternity_max_weeks', 'short'), 0))",
        "Najwięcej tygodni uzupełniającego urlopu",
        "KP art. 180² § 1",
        KP,
        G_SUP,
    ),
    V(
        "uzup_tyg",
        "jesli(dziecko.dni_szpitala > 0, min(uzup_limit_tyg, zaokr_gora(dziecko.dni_szpitala / 7)), 0)",
        "Wymiar uzupełniającego urlopu (tydzień za każdy rozpoczęty tydzień pobytu w szpitalu)",
        "KP art. 180² § 1 i § 3",
        KP,
        G_SUP,
    ),
    V(
        "uzup_bierze",
        "jesli(plan.uzupelniajacy_bierze == 'tata' and tata_uprawniony, 'tata', jesli(mama_uprawniona, 'mama', "
        "jesli(tata_uprawniony, 'tata', None)))",
        "Kto korzysta z uzupełniającego urlopu (tylko jedno z rodziców)",
        "KP art. 180² § 1; RW § 14",
        KP,
        G_SUP,
    ),
    P(
        "okres_uzupelniajacy",
        "uzup_bierze",
        "supplementary",
        "Uzupełniający urlop macierzyński",
        "dodaj_dni(koniec_macierzynskiego, 1)",
        "tygodnie(uzup_tyg)",
        "param('rate_maternity')",
        "KP art. 180²; UZ art. 29a ust. 1, art. 31 ust. 1",
        KP,
        G_SUP,
        condition="plan.uzupelniajacy and jest(uzup_bierze)",
        payer="jesli(uzup_bierze == 'tata', tata_platnik, mama_platnik)",
    ),
    V(
        "koniec_ciaglosci",
        "najpozniej(koniec_macierzynskiego, okres_uzupelniajacy.koniec)",
        "Koniec urlopu macierzyńskiego i uzupełniającego",
        "KP art. 180²",
        KP,
        G_SUP,
    ),
]
