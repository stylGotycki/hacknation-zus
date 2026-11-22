"""Rules: Świadczenia (karty wyniku)."""

from __future__ import annotations

from app.seed.rules.helpers import (
    KP,
    PR,
    SR,
    UZ,
    B,
)

RULES: list[dict] = [
    # ======================================================================================
    # Świadczenia (karty wyniku)
    # ======================================================================================
    B(
        "zasilek_chorobowy_ciaza",
        "mama",
        "Zasiłek chorobowy w czasie ciąży",
        "porod and mama.obecny and mama.ubezpieczenie != 'brak'",
        "jesli(zwolnienie_b_dni > 0, jesli(mama_chorobowe_prawo, 'przysluguje', 'nie_przysluguje'), jesli(przed_zdarzeniem, 'informacja', None))",
        "Niezdolność do pracy w ciąży (zwolnienie z kodem B): {zaokr(param('rate_sickness_pregnancy') * 100, 0)}% podstawy "
        "wymiaru, najdłużej {tabela('sickness_benefit_period_days', 'pregnancy')} dni okresu zasiłkowego. "
        "{jesli(mama.pracownik, 'Za pierwsze ' + limit_wynagrodzenia_chorobowego + ' dni w roku płaci pracodawca (wynagrodzenie chorobowe), dalej zasiłek.', 'Zasiłek od pierwszego dnia niezdolności, po okresie wyczekiwania.')}",
        ["mama_wynagrodzenie_chorobowe", "mama_zasilek_chorobowy"],
        "UZ art. 4, 8, 11 ust. 2; KP art. 92",
        UZ,
        payer="mama_platnik",
        apply_to="Zwolnienie e-ZLA lekarz przesyła do ZUS i płatnika; {jesli(mama_platnik == 'zus', 'zasiłek wypłaca ZUS.', 'zasiłek wypłaca płatnik składek.')}",
        order=10,
    ),
    B(
        "swiadczenie_rehabilitacyjne",
        "mama",
        "Świadczenie rehabilitacyjne",
        "porod and mama_chorobowe_prawo and (przed_zdarzeniem or zwolnienie_b_dni > 0)",
        "'informacja'",
        "Gdy po wyczerpaniu zasiłku chorobowego nadal jesteś niezdolna do pracy, a leczenie rokuje powrót do zdrowia – "
        "do {param('rehabilitation_max_months')} miesięcy, w ciąży {zaokr(tabela('rate_rehabilitation', 'pregnancy') * 100, 0)}% podstawy.",
        [],
        "UZ art. 18–19",
        UZ,
        order=12,
    ),
    B(
        "zasilek_w_wysokosci_macierzynskiego",
        "mama",
        "Zasiłek w wysokości zasiłku macierzyńskiego",
        "zasilek_wys_mac",
        "'przysluguje'",
        "Umowa ustała w ciąży z powodu upadłości, likwidacji albo śmierci pracodawcy i nie zapewniono innej pracy: "
        "zasiłek do dnia porodu, {zaokr(param('rate_maternity') * 100, 0)}% podstawy. Po porodzie – zasiłek macierzyński.",
        ["mama_zasilek_wys_mac"],
        "UZ art. 30 ust. 1 i 3",
        UZ,
        payer="'zus'",
        apply_to="Wniosek i dokumenty składasz w ZUS.",
        order=15,
    ),
    B(
        "macierzynski_mama",
        "mama",
        "{jesli(porod, 'Zasiłek macierzyński za okres urlopu macierzyńskiego', 'Zasiłek macierzyński za okres urlopu na warunkach urlopu macierzyńskiego')}",
        "mama.obecny and (porod or przyjecie) and not przyjecie_tata_calosc",
        "jesli(mama_uprawniona, jesli(mama_dlug_do_splaty, 'warunkowo', 'przysluguje'), 'nie_przysluguje')",
        "{jesli(mama_uprawniona, 'Wymiar: ' + zaokr(wymiar_macierzynski_dni / 7, 1) + ' tyg., stawka ' + zaokr(stawka_macierzynska * 100, 1) + '% podstawy.', jesli(mama_dlug_przedawnia, 'Zadłużenie składkowe nie zostało spłacone w ciągu 6 miesięcy – prawo do zasiłku się przedawniło.', jesli(przyjecie and not przyjecie_w_limicie, 'Dziecko przekroczyło wiek, do którego przysługuje zasiłek.', 'W dniu porodu / przyjęcia dziecka nie ma ubezpieczenia chorobowego ani urlopu wychowawczego.')))}",
        ["mama_macierzynski_przed", "mama_macierzynski", "mama_macierzynski_dokonczenie"],
        "UZ art. 29, 29a, 30, 31; KP art. 180, 180¹, 183",
        UZ,
        payer="mama_platnik",
        apply_to="{jesli(mama.pracownik, 'Wniosek o urlop składasz u pracodawcy', 'Wniosek o zasiłek składasz') + jesli(mama_platnik == 'zus', '; zasiłek ustala i wypłaca ZUS.', jesli(mama_platnik == 'pracodawca', '; zasiłek wypłaca płatnik składek.', '.'))}",
        order=20,
    ),
    B(
        "macierzynski_tata",
        "tata",
        "{jesli(przyjecie, 'Zasiłek macierzyński za okres urlopu na warunkach urlopu macierzyńskiego', 'Zasiłek macierzyński za część urlopu macierzyńskiego')}",
        "tata.obecny and (tata_przejecie_dni > 0 or tata_szpital_dni > 0)",
        "jesli(tata_dlug_do_splaty, 'warunkowo', 'przysluguje')",
        "{jesli(przyjecie_tata_calosc, 'Tata korzysta z urlopu na warunkach urlopu macierzyńskiego.', jesli(szpital_matki, 'Na czas pobytu mamy w szpitalu.', jesli(zgon_porzucenie_matki or not mama_uprawniona, 'Za okres po dniu zdarzenia dotyczącego mamy.', 'Część urlopu po rezygnacji mamy (po co najmniej ' + matka_min_osobiscie_tyg + ' tyg. po porodzie).')))} "
        "Stawka {zaokr(stawka_macierzynska * 100, 1)}%.",
        ["tata_macierzynski_szpital", "tata_macierzynski"],
        "UZ art. 29 ust. 3–10, art. 29a ust. 2; KP art. 180 § 4–17",
        UZ,
        payer="tata_platnik",
        order=21,
    ),
    B(
        "uzupelniajacy",
        "uzup_bierze",
        "Zasiłek za uzupełniający urlop macierzyński",
        "uzup_tyg > 0",
        "jesli(plan.uzupelniajacy and jest(uzup_bierze), 'przysluguje', jesli(jest(uzup_bierze), 'informacja', 'nie_przysluguje'))",
        "{uzup_tyg} tyg. ({jesli(uzup_przypadek == 1, 'urodzenie przed 28. tyg. ciąży lub masa do 1000 g', jesli(uzup_przypadek == 2, 'urodzenie między 28. a 37. tyg. ciąży', 'dziecko w terminie, szpital od 5. dnia'))}), "
        "bezpośrednio po urlopie macierzyńskim, jednorazowo, przez jedno z rodziców; {zaokr(param('rate_maternity') * 100, 0)}% podstawy.",
        ["okres_uzupelniajacy"],
        "KP art. 180²; UZ art. 29a ust. 1, art. 31 ust. 1",
        KP,
        payer="jesli(uzup_bierze == 'tata', tata_platnik, mama_platnik)",
        order=25,
    ),
    B(
        "rodzicielski_mama",
        "mama",
        "Zasiłek macierzyński za okres urlopu rodzicielskiego",
        "mama.obecny and dziecko_zyje and mama_uprawniona and not zgon_porzucenie_matki",
        "jesli(mama_rodzicielski_dni > 0, jesli(mama_dlug_do_splaty, 'warunkowo', 'przysluguje'), 'informacja')",
        "{mama_rodzicielski_tyg} z {wymiar_rodzicielski_tyg} tyg., stawka {zaokr(stawka_rodzicielska * 100, 1)}%"
        "{jesli(mama_praca > 0, ', praca na ' + zaokr(mama_praca * 100, 0) + '% etatu – urlop dłuższy, zasiłek proporcjonalnie niższy', '')}. "
        "Do {param('parental_max_parts')} części, najpóźniej do {rodzicielski_termin}.",
        ["mama_rodzicielski"],
        "KP art. 182¹ᵃ–182¹ᶠ; UZ art. 29a, 31",
        KP,
        payer="mama_platnik",
        order=30,
    ),
    B(
        "rodzicielski_tata",
        "tata",
        "Zasiłek macierzyński za okres urlopu rodzicielskiego",
        "tata.obecny and dziecko_zyje and tata_uprawniony",
        "jesli(tata_rodzicielski_dni > 0, jesli(tata_dlug_do_splaty, 'warunkowo', 'przysluguje'), 'informacja')",
        "{tata_rodzicielski_tyg} z {wymiar_rodzicielski_tyg} tygodni"
        "{jesli(oboje_rodzicielski, ', w tym ' + wylaczna_czesc_tyg + ' tyg. wyłącznie dla taty (zawsze ' + zaokr(param('rate_parental') * 100, 0) + '%)', '')}"
        "{jesli(tata_praca > 0, ', praca na ' + zaokr(tata_praca * 100, 0) + '% etatu', '')}"
        "{jesli(not mama_uprawniona, ' – mama nie ma prawa do zasiłku, więc tata może wykorzystać cały wymiar', '')}. "
        "Najpóźniej do {rodzicielski_termin}.",
        ["tata_rodzicielski_wylaczny", "tata_rodzicielski_wspolny"],
        "KP art. 182¹ᵃ–182¹ᶠ; UZ art. 29a, 31 ust. 3f, 3h",
        KP,
        payer="tata_platnik",
        order=31,
    ),
    B(
        "ojcowski",
        "tata",
        "Zasiłek macierzyński za okres urlopu ojcowskiego",
        "tata.obecny and ojcowski_mozliwy",
        "jesli(tata_dlug_do_splaty, 'warunkowo', 'przysluguje')",
        "{param('paternity_leave_weeks')} tygodnie, jednorazowo albo w 2 częściach po co najmniej tydzień, "
        "{zaokr(param('rate_maternity') * 100, 0)}% podstawy, do {ojcowski_termin}.",
        ["tata_ojcowski"],
        "KP art. 182³; UZ art. 29a ust. 1, art. 31 ust. 1",
        KP,
        payer="tata_platnik",
        order=35,
    ),
    B(
        "pogrzebowy",
        "rodzina",
        "Zasiłek pogrzebowy",
        "porod and dziecko.martwe_urodzenie",
        "'informacja'",
        "Gdy dziecko urodzi się martwe (bez względu na czas trwania ciąży): {param('funeral_allowance_stillbirth')} zł – "
        "pełna kwota, nawet jeśli koszty były niższe. Otrzymuje osoba, która pokryła koszty pogrzebu; wniosek Z-12 w ZUS "
        "w ciągu {param('funeral_application_months')} miesięcy od pochówku.",
        [],
        "Poradnik ZUS 2026 – Zasiłek pogrzebowy",
        PR,
        apply_to="Wniosek Z-12 z rachunkami składasz w ZUS.",
        order=40,
    ),
    B(
        "opiekunczy",
        "rodzina",
        "Zasiłek opiekuńczy",
        "dziecko_zyje",
        "'informacja'",
        "Na chore dziecko do 14 lat albo zdrowe do 8 lat w określonych sytuacjach (np. zamknięcie żłobka): "
        "{zaokr(param('rate_care_allowance') * 100, 0)}% podstawy, do {tabela('care_allowance_limits_days', 'child_under_14')} dni "
        "w roku łącznie dla rodziny; tylko gdy nie ma innego domownika, który zapewni opiekę (nie dotyczy chorego dziecka do 2 lat).",
        [],
        "Poradnik ZUS 2026 – Zasiłek opiekuńczy",
        PR,
        apply_to="Pracownik: wniosek Z-15A u pracodawcy.",
        order=45,
    ),
    B(
        "becikowe",
        "rodzina",
        "Becikowe – jednorazowa zapomoga z tytułu urodzenia dziecka",
        "porod and not dziecko.martwe_urodzenie",
        "'warunkowo'",
        "{param('birth_grant_amount')} zł na każde dziecko, czyli {param('birth_grant_amount') * dziecko.liczba} zł – jednorazowo, "
        "niezależnie od dochodu. Przysługuje matce, ojcu lub opiekunowi dziecka; wniosek składa się do gminy "
        "w ciągu {param('birth_grant_months')} miesięcy od urodzenia. Warunek: zaświadczenie, że matka pozostawała pod opieką "
        "medyczną od 10. tygodnia ciąży do porodu. To świadczenie spoza sześciu źródeł przewodnika – kwotę i terminy "
        "potwierdź na gov.pl.",
        [],
        "Ustawa o świadczeniach rodzinnych art. 15b; gov.pl – Uzyskaj becikowe",
        SR,
        apply_to="Wniosek składasz w urzędzie gminy albo ośrodku pomocy społecznej właściwym dla miejsca zamieszkania.",
        order=48,
    ),
    B(
        "swiadczenie_rodzicielskie_info",
        "rodzina",
        "Świadczenie rodzicielskie",
        "(porod or przyjecie) and dziecko_zyje and not mama_uprawniona and not tata_uprawniony",
        "'informacja'",
        "Osobom, które z powodu swojej sytuacji zawodowej nie mogą skorzystać z zasiłku macierzyńskiego (np. bezrobotnym, "
        "studentom, pracującym na umowę o dzieło), przysługuje świadczenie rodzicielskie lub uposażenie macierzyńskie. "
        "Szczegóły: gov.pl – Ministerstwo Rodziny, Pracy i Polityki Społecznej.",
        [],
        "Poradnik ZUS 2026 – Ważne informacje uzupełniające",
        PR,
        order=50,
    ),
]
