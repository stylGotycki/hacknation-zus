"""Rules: Urlop macierzyński / na warunkach urlopu macierzyńskiego."""

from __future__ import annotations

from app.seed.rules.helpers import (
    G_MAT,
    KP,
    P,
    V,
)

RULES: list[dict] = [
    # ======================================================================================
    # Urlop macierzyński / na warunkach urlopu macierzyńskiego
    # ======================================================================================
    V(
        "wymiar_macierzynski_pelny_dni",
        "tygodnie(tabela('maternity_leave_weeks', klucz_liczby_dzieci))",
        "Pełny wymiar urlopu macierzyńskiego (dni)",
        "KP art. 180 § 1, art. 183 § 1 i § 1¹, art. 183¹ § 1",
        KP,
        G_MAT,
    ),
    V(
        "wymiar_macierzynski_zywe_dni",
        "jesli(dziecko_zyje, tygodnie(tabela('maternity_leave_weeks', klucz_dzieci(dzieci_zywe))), 0)",
        "Wymiar stosowny do liczby dzieci pozostałych przy życiu (dni)",
        "KP art. 180¹ § 1–2",
        KP,
        G_MAT,
    ),
    V(
        "przyjecie_okres_minimalny",
        "przyjecie_w_limicie and dni_do_limitu_wieku < wymiar_macierzynski_pelny_dni",
        "Przyjęcie: urlop ograniczony wiekiem dziecka (przypadek z art. 183 § 3 KP)",
        "KP art. 183 § 3, § 4 pkt 3, § 4²",
        KP,
        G_MAT,
        description="Interpretacja: art. 183 § 3 dotyczy sytuacji, gdy granica wieku skraca urlop – wtedy "
        "przysługuje co najmniej 9 tygodni urlopu, a urlop rodzicielski wynosi 38 (62) tygodni.",
    ),
    V(
        "wymiar_na_warunkach_dni",
        "jesli(przyjecie_w_limicie, max(min(wymiar_macierzynski_pelny_dni, dni_do_limitu_wieku), "
        "tygodnie(param('taken_in_min_maternity_weeks'))), 0)",
        "Wymiar urlopu na warunkach urlopu macierzyńskiego (dni)",
        "KP art. 183 § 1, § 1¹, § 3; ZAL",
        KP,
        G_MAT,
    ),
    V(
        "wymiar_macierzynski_dni",
        "jesli(przyjecie, wymiar_na_warunkach_dni, "
        "jesli(brak(dziecko.data_zgonu), wymiar_macierzynski_pelny_dni, "
        "jesli(dziecko_zyje, jesli(zgon_wczesny, wymiar_macierzynski_zywe_dni, "
        "min(wymiar_macierzynski_pelny_dni, max(wymiar_macierzynski_zywe_dni, dni_do_zgonu_plus))), "
        "jesli(zgon_wczesny, max(tygodnie(param('stillbirth_maternity_weeks')), dni_do_zgonu_plus), "
        "min(wymiar_macierzynski_pelny_dni, dni_do_zgonu_plus)))))",
        "Wymiar urlopu macierzyńskiego w tej sytuacji (dni)",
        "KP art. 180 § 1, art. 180¹, art. 183",
        KP,
        G_MAT,
        description="Martwe urodzenie / zgon przed 8 tyg.: 8 tygodni, nie krócej niż 7 dni od zgonu; zgon później: "
        "7 dni od zgonu; poród mnogi: wymiar wg dzieci żyjących.",
    ),
    V(
        "przed_porodem_dni",
        "jesli(porod and mama_uprawniona, tygodnie(plan.przed_porodem_tyg), 0)",
        "Część urlopu macierzyńskiego przed porodem (dni)",
        "KP art. 180 § 2",
        KP,
        G_MAT,
    ),
    V(
        "matka_min_osobiscie_tyg",
        "jesli(sytuacja_matki.rodzaj == 'niezdolnosc', param('maternity_mother_min_weeks_disabled'), "
        "param('maternity_mother_mandatory_weeks'))",
        "Ile tygodni po porodzie matka wykorzystuje, zanim przekaże resztę ojcu",
        "KP art. 180 § 4 i § 6; UZ art. 29 ust. 3 i 5",
        KP,
        G_MAT,
    ),
    V(
        "dla_taty_dni",
        "jesli(porod and mama_uprawniona and tata_uprawniony and dziecko_zyje, tygodnie(plan.dla_taty_tyg), 0)",
        "Część urlopu macierzyńskiego przejmowana przez tatę (dni)",
        "KP art. 180 § 4–5; UZ art. 29 ust. 3",
        KP,
        G_MAT,
    ),
    V(
        "mama_pula_po_porodzie",
        "jesli(mama_uprawniona, wymiar_macierzynski_dni - przed_porodem_dni, 0)",
        "Urlop macierzyński po porodzie do podziału (dni)",
        "KP art. 180 § 3",
        KP,
        G_MAT,
    ),
    V(
        "szpital_matki",
        "porod and mama_uprawniona and tata_uprawniony and sytuacja_matki.rodzaj == 'szpital' and jest(sytuacja_matki.od)",
        "Matka w szpitalu – część urlopu wykorzystuje tata",
        "KP art. 180 § 10–11; UZ art. 29 ust. 6",
        KP,
        G_MAT,
    ),
    V(
        "zgon_porzucenie_matki",
        "sytuacja_matki.rodzaj in ['zgon', 'porzucenie'] and jest(sytuacja_matki.od)",
        "Zgon matki albo porzucenie dziecka",
        "KP art. 180 § 12–13, § 15; UZ art. 29 ust. 7 i 9",
        KP,
        G_MAT,
    ),
    V(
        "mama_dni_1",
        "jesli(not mama_uprawniona, 0, "
        "jesli(zgon_porzucenie_matki, min(mama_pula_po_porodzie, jesli(sytuacja_matki.rodzaj == 'porzucenie', "
        "max(dni_miedzy(data_zdarzenia, sytuacja_matki.od) + 1, tygodnie(param('maternity_min_weeks_before_transfer'))), "
        "dni_miedzy(data_zdarzenia, sytuacja_matki.od) + 1)), "
        "jesli(szpital_matki, min(mama_pula_po_porodzie, max(dni_miedzy(data_zdarzenia, sytuacja_matki.od), "
        "tygodnie(param('maternity_min_weeks_before_transfer')))), mama_pula_po_porodzie - dla_taty_dni)))",
        "Urlop macierzyński mamy po porodzie – pierwsza część (dni)",
        "KP art. 180, 182; UZ art. 29",
        KP,
        G_MAT,
    ),
    V(
        "tata_szpital_dni",
        "jesli(szpital_matki, min(mama_pula_po_porodzie - mama_macierzynski.dni, "
        "dni_miedzy(sytuacja_matki.od, jesli(jest(sytuacja_matki.do), sytuacja_matki.do, sytuacja_matki.od)) + 1), 0)",
        "Część urlopu taty na czas pobytu matki w szpitalu (dni)",
        "KP art. 180 § 10–11; UZ art. 29 ust. 6",
        KP,
        G_MAT,
    ),
    V(
        "przyjecie_tata_calosc",
        "przyjecie and not mama_uprawniona and tata_uprawniony",
        "Przyjęcie dziecka: urlop na warunkach urlopu macierzyńskiego wykorzystuje tata",
        "KP art. 183; UZ art. 29 ust. 2",
        KP,
        G_MAT,
    ),
    V(
        "tata_przejecie_dni",
        "jesli(not tata_uprawniony or not dziecko_zyje, 0, "
        "jesli(przyjecie_tata_calosc, wymiar_na_warunkach_dni, "
        "jesli(mama_uprawniona, jesli(zgon_porzucenie_matki, mama_pula_po_porodzie - mama_macierzynski.dni, dla_taty_dni), "
        "jesli(porod and sytuacja_matki.rodzaj in ['zgon', 'porzucenie', 'niezdolnosc'] and jest(sytuacja_matki.od), "
        "max(0, dni_miedzy(sytuacja_matki.od, dodaj_dni(data_zdarzenia, wymiar_macierzynski_dni - 1))), "
        "jesli(porod and sytuacja_matki.rodzaj == 'zatrudnienie' and jest(sytuacja_matki.od), "
        "max(0, min(dni_miedzy(sytuacja_matki.od, dodaj_dni(data_zdarzenia, wymiar_macierzynski_dni - 1)) + 1, "
        "jesli(jest(sytuacja_matki.do), dni_miedzy(sytuacja_matki.od, sytuacja_matki.do) + 1, 100000))), 0)))))",
        "Urlop (zasiłek) macierzyński taty: przejęta część albo okres po zdarzeniu dotyczącym matki (dni)",
        "KP art. 180 § 4–17, art. 183; UZ art. 29 ust. 3–10",
        KP,
        G_MAT,
    ),
    P(
        "mama_macierzynski_przed",
        "mama",
        "maternity",
        "Urlop macierzyński przed porodem",
        "dodaj_dni(data_zdarzenia, -przed_porodem_dni)",
        "przed_porodem_dni",
        "stawka_macierzynska",
        "KP art. 180 § 2; UZ art. 31 ust. 1",
        KP,
        G_MAT,
        payer="mama_platnik",
    ),
    P(
        "mama_macierzynski",
        "mama",
        "maternity",
        "{jesli(porod, 'Urlop macierzyński', 'Urlop na warunkach urlopu macierzyńskiego')}",
        "data_zdarzenia",
        "mama_dni_1",
        "stawka_macierzynska",
        "KP art. 180, 180¹, 183; UZ art. 29, 31",
        KP,
        G_MAT,
        payer="mama_platnik",
    ),
    P(
        "tata_macierzynski_szpital",
        "tata",
        "maternity",
        "Urlop macierzyński taty – pobyt matki w szpitalu",
        "dodaj_dni(mama_macierzynski.koniec, 1)",
        "tata_szpital_dni",
        "stawka_macierzynska",
        "KP art. 180 § 10–11; UZ art. 29 ust. 6",
        KP,
        G_MAT,
        payer="tata_platnik",
    ),
    P(
        "mama_macierzynski_dokonczenie",
        "mama",
        "maternity",
        "Urlop macierzyński – dokończenie po szpitalu",
        "dodaj_dni(tata_macierzynski_szpital.koniec, 1)",
        "mama_pula_po_porodzie - mama_macierzynski.dni - tata_szpital_dni - dla_taty_dni",
        "stawka_macierzynska",
        "KP art. 180 § 10; UZ art. 29 ust. 6",
        KP,
        G_MAT,
        condition="szpital_matki",
        payer="mama_platnik",
    ),
    P(
        "tata_macierzynski",
        "tata",
        "maternity",
        "{jesli(przyjecie, 'Urlop na warunkach urlopu macierzyńskiego', 'Urlop macierzyński taty')}",
        "jesli(przyjecie_tata_calosc, data_zdarzenia, jesli(mama_uprawniona, dodaj_dni(najpozniej(mama_macierzynski.koniec, "
        "mama_macierzynski_dokonczenie.koniec), 1), jesli(sytuacja_matki.rodzaj == 'zatrudnienie', sytuacja_matki.od, "
        "dodaj_dni(sytuacja_matki.od, 1))))",
        "tata_przejecie_dni",
        "stawka_macierzynska",
        "KP art. 180 § 4–17, art. 183; UZ art. 29",
        KP,
        G_MAT,
        payer="tata_platnik",
    ),
    V(
        "koniec_macierzynskiego",
        "najpozniej(mama_macierzynski.koniec, mama_macierzynski_dokonczenie.koniec, tata_macierzynski.koniec)",
        "Ostatni dzień urlopu macierzyńskiego w rodzinie",
        "KP art. 180",
        KP,
        G_MAT,
    ),
]
