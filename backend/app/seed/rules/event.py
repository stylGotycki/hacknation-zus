"""Rules: Zdarzenie i dziecko."""

from __future__ import annotations

from app.seed.rules.helpers import (
    G_EVENT,
    KP,
    PR,
    UZ,
    V,
)

RULES: list[dict] = [
    # ======================================================================================
    # Zdarzenie i dziecko
    # ======================================================================================
    V(
        "porod",
        "dziecko.zdarzenie == 'porod'",
        "Zdarzeniem jest poród",
        "UZ art. 29 ust. 1 pkt 1",
        UZ,
        G_EVENT,
    ),
    V(
        "przyjecie",
        "dziecko.zdarzenie in ['przysposobienie', 'rodzina_zastepcza']",
        "Zdarzeniem jest przyjęcie dziecka na wychowanie",
        "UZ art. 29 ust. 1 pkt 2–3",
        UZ,
        G_EVENT,
    ),
    V(
        "data_zdarzenia",
        "dziecko.data",
        "Data zdarzenia (porodu / przewidywanego porodu / przyjęcia)",
        "KP art. 183¹ § 2; UZ art. 29",
        UZ,
        G_EVENT,
    ),
    V(
        "przed_zdarzeniem",
        "data_zdarzenia > dzis()",
        "Zdarzenie jeszcze nie nastąpiło (planowanie)",
        "",
        PR,
        G_EVENT,
    ),
    V(
        "dzieci_zywe",
        "dziecko.liczba_zywych",
        "Liczba dzieci pozostałych przy życiu",
        "KP art. 180¹",
        KP,
        G_EVENT,
    ),
    V(
        "dziecko_zyje",
        "dzieci_zywe > 0",
        "Co najmniej jedno dziecko żyje",
        "KP art. 180¹",
        KP,
        G_EVENT,
    ),
    V(
        "klucz_liczby_dzieci",
        "klucz_dzieci(dziecko.liczba)",
        "Klucz tabel wg liczby dzieci",
        "KP art. 180 § 1",
        KP,
        G_EVENT,
    ),
    V(
        "wiek_przy_zgonie_tyg",
        "dni_miedzy(dziecko.data_porodu, dziecko.data_zgonu) / 7",
        "Wiek dziecka przy zgonie (tygodnie życia)",
        "KP art. 180¹",
        KP,
        G_EVENT,
        condition="jest(dziecko.data_zgonu)",
    ),
    V(
        "zgon_wczesny",
        "dziecko.martwe_urodzenie or wiek_przy_zgonie_tyg < param('stillbirth_child_death_weeks_limit')",
        "Martwe urodzenie albo zgon przed upływem 8 tygodni życia",
        "KP art. 180¹ § 1",
        KP,
        G_EVENT,
    ),
    V(
        "dni_do_zgonu_plus",
        "dni_miedzy(dziecko.data_porodu, dziecko.data_zgonu) + param('child_death_min_days')",
        "Dni od porodu do upływu 7 dni od zgonu",
        "KP art. 180¹ § 1–2",
        KP,
        G_EVENT,
        condition="jest(dziecko.data_zgonu)",
        description="Okres 7 dni liczony łącznie z dniem zgonu.",
    ),
    V(
        "limit_wieku_przyjecia",
        "jesli(dziecko.zdarzenie == 'przysposobienie', tabela('adoption_leave_max_child_age_years', 'adoption'), "
        "jesli(dziecko.odroczony_obowiazek, tabela('adoption_leave_max_child_age_years', 'foster_school_deferred'), "
        "tabela('adoption_leave_max_child_age_years', 'foster')))",
        "Wiek dziecka, do którego przysługuje urlop na warunkach urlopu macierzyńskiego",
        "UZ art. 29 ust. 1 pkt 2–3; KP art. 183 § 1 i § 1¹",
        UZ,
        G_EVENT,
        condition="przyjecie",
    ),
    V(
        "przyjecie_w_limicie",
        "przyjecie and dziecko.wiek_lat < limit_wieku_przyjecia",
        "Dziecko przyjęte przed ukończeniem wymaganego wieku",
        "UZ art. 29 ust. 1 pkt 2–3",
        UZ,
        G_EVENT,
    ),
    V(
        "zdarzenie_uprawnia",
        "porod or przyjecie_w_limicie",
        "Zdarzenie daje prawo do zasiłku macierzyńskiego",
        "UZ art. 29 ust. 1",
        UZ,
        G_EVENT,
    ),
    V(
        "dni_do_limitu_wieku",
        "zaokr((limit_wieku_przyjecia - dziecko.wiek_lat) * 365.25, 0)",
        "Dni do osiągnięcia przez dziecko granicy wieku",
        "KP art. 183 § 1 i § 1¹",
        KP,
        G_EVENT,
        condition="przyjecie_w_limicie",
    ),
]
