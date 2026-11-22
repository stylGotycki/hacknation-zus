"""Rules: Urlop rodzicielski."""

from __future__ import annotations

from app.seed.rules.helpers import (
    G_PAR,
    KP,
    PARENTS,
    UZ,
    P,
    V,
)

RULES: list[dict] = [
    # ======================================================================================
    # Urlop rodzicielski
    # ======================================================================================
    V(
        "klucz_rodzicielski",
        "jesli(dziecko.za_zyciem, 'za_zyciem_', '') + jesli(jesli(porod, dzieci_zywe, dziecko.liczba) > 1, 'multiple', 'single')",
        "Klucz wymiaru urlopu rodzicielskiego",
        "KP art. 182¹ᵃ § 1–2",
        KP,
        G_PAR,
    ),
    V(
        "wymiar_rodzicielski_tyg",
        "jesli(not dziecko_zyje or not zdarzenie_uprawnia, 0, jesli(przyjecie_okres_minimalny, "
        "tabela('parental_leave_weeks', jesli(dziecko.za_zyciem, 'za_zyciem_taken_in_short', 'taken_in_short')), "
        "tabela('parental_leave_weeks', klucz_rodzicielski)))",
        "Wymiar urlopu rodzicielskiego dla obojga rodziców (tygodnie)",
        "KP art. 182¹ᵃ § 1–3, art. 183 § 4–4⁵",
        KP,
        G_PAR,
    ),
    V(
        "wylaczna_czesc_tyg",
        "param('parental_non_transferable_weeks')",
        "Nieprzenoszalna część każdego rodzica (tygodnie)",
        "KP art. 182¹ᵃ § 4",
        KP,
        G_PAR,
    ),
    V(
        "oboje_rodzicielski",
        "mama_uprawniona and tata_uprawniony and dziecko_zyje and not zgon_porzucenie_matki",
        "Oboje rodzice mają prawo do urlopu (zasiłku) rodzicielskiego",
        "KP art. 182¹ᵃ § 3–4; UZ art. 29a ust. 3",
        KP,
        G_PAR,
    ),
    V(
        "tata_rodzicielski_tyg",
        "jesli(not tata_uprawniony or not dziecko_zyje, 0, jesli(oboje_rodzicielski, "
        "jesli(jest(plan.rodzicielski_tata_tyg), plan.rodzicielski_tata_tyg, wylaczna_czesc_tyg), "
        "jesli(mama_uprawniona and not zgon_porzucenie_matki, 0, wymiar_rodzicielski_tyg)))",
        "Urlop rodzicielski taty (tygodnie)",
        "KP art. 182¹ᵃ § 3–4; UZ art. 31 ust. 3h",
        KP,
        G_PAR,
        description="Gdy matka nie ma prawa do zasiłku, tata może wykorzystać cały wymiar (brak drugiego "
        "uprawnionego rodzica, na którego przypadałaby część wyłączna) – interpretacja art. 182¹ᵃ § 4 KP.",
    ),
    V(
        "mama_rodzicielski_tyg",
        "jesli(not mama_uprawniona or not dziecko_zyje or zgon_porzucenie_matki, 0, wymiar_rodzicielski_tyg - tata_rodzicielski_tyg)",
        "Urlop rodzicielski mamy (tygodnie)",
        "KP art. 182¹ᵃ § 3",
        KP,
        G_PAR,
    ),
    V(
        "limit_z_praca_tyg",
        "tabela('parental_with_work_max_weeks', jesli(dziecko.za_zyciem, 'za_zyciem_', '') + "
        "jesli(jesli(porod, dzieci_zywe, dziecko.liczba) > 1, 'multiple', 'single'))",
        "Najdłuższy urlop rodzicielski łączony z pracą (tygodnie)",
        "KP art. 182¹ᶠ § 1 i § 1¹",
        KP,
        G_PAR,
    ),
    *[
        V(
            f"{p}_rodzicielski_dni",
            f"jesli({p}_rodzicielski_tyg > 0, min(zaokr(tygodnie({p}_rodzicielski_tyg) / (1 - {p}_praca), 0), "
            f"tygodnie(limit_z_praca_tyg)), 0)",
            f"Urlop rodzicielski {gen} w dniach (wydłużony przy łączeniu z pracą)",
            "KP art. 182¹ᶠ § 1–7",
            KP,
            G_PAR,
        )
        for p, gen in PARENTS.items()
    ],
    V(
        "tata_wylaczny_dni",
        "jesli(oboje_rodzicielski, min(tata_rodzicielski_dni, zaokr(tygodnie(min(tata_rodzicielski_tyg, wylaczna_czesc_tyg)) "
        "/ (1 - tata_praca), 0)), 0)",
        "Część wyłączna urlopu rodzicielskiego taty (dni)",
        "KP art. 182¹ᵃ § 4; UZ art. 31 ust. 3f",
        KP,
        G_PAR,
    ),
    V(
        "start_rodzicielski_mamy",
        "jesli(jest(plan.rodzicielski_mama_od), plan.rodzicielski_mama_od, "
        "dodaj_dni(najpozniej(koniec_ciaglosci, dodaj_dni(data_zdarzenia, -1)), 1))",
        "Początek urlopu rodzicielskiego mamy (domyślnie bezpośrednio po macierzyńskim)",
        "KP art. 182¹ᵃ, art. 182¹ᶜ",
        KP,
        G_PAR,
    ),
    P(
        "mama_rodzicielski",
        "mama",
        "parental",
        "Urlop rodzicielski",
        "start_rodzicielski_mamy",
        "mama_rodzicielski_dni",
        "stawka_rodzicielska",
        "KP art. 182¹ᵃ–182¹ᶠ; UZ art. 31 ust. 2, 3, 3g, 4a",
        KP,
        G_PAR,
        work="mama_praca",
        payer="mama_platnik",
    ),
    V(
        "koniec_rodzicielskiego_mamy",
        "dodaj_dni(start_rodzicielski_mamy, mama_rodzicielski_dni - 1)",
        "Ostatni dzień urlopu rodzicielskiego mamy",
        "KP art. 182¹ᵃ",
        KP,
        G_PAR,
        condition="mama_rodzicielski_dni > 0",
    ),
    V(
        "start_rodzicielski_taty",
        "jesli(jest(plan.rodzicielski_tata_od), plan.rodzicielski_tata_od, "
        "dodaj_dni(najpozniej(koniec_rodzicielskiego_mamy, koniec_ciaglosci, dodaj_dni(data_zdarzenia, -1), "
        "jesli(brak(plan.ojcowski_od), tata_ojcowski.koniec, None)), 1))",
        "Początek urlopu rodzicielskiego taty (domyślnie po urlopie mamy i po urlopie ojcowskim)",
        "KP art. 182¹ᵃ § 6–7",
        KP,
        G_PAR,
    ),
    P(
        "tata_rodzicielski_wylaczny",
        "tata",
        "parental",
        "Urlop rodzicielski – część wyłączna (9 tyg.)",
        "start_rodzicielski_taty",
        "tata_wylaczny_dni",
        "param('rate_parental')",
        "KP art. 182¹ᵃ § 4; UZ art. 31 ust. 3f",
        KP,
        G_PAR,
        work="tata_praca",
        payer="tata_platnik",
    ),
    P(
        "tata_rodzicielski_wspolny",
        "tata",
        "parental",
        "Urlop rodzicielski",
        "jesli(tata_rodzicielski_wylaczny.aktywny, dodaj_dni(tata_rodzicielski_wylaczny.koniec, 1), start_rodzicielski_taty)",
        "tata_rodzicielski_dni - tata_wylaczny_dni",
        "stawka_rodzicielska",
        "KP art. 182¹ᵃ; UZ art. 30a ust. 3, art. 31 ust. 2–3",
        KP,
        G_PAR,
        work="tata_praca",
        payer="tata_platnik",
    ),
    V(
        "rodzicielski_w_1_roku",
        "najwczesniej(jesli(mama_rodzicielski_dni > 0, start_rodzicielski_mamy, None), "
        "jesli(tata_rodzicielski_dni > 0, start_rodzicielski_taty, None)) < dodaj_mies(dziecko.data_urodzenia, 12)",
        "Co najmniej jeden dzień urlopu rodzicielskiego w pierwszym roku życia dziecka",
        "UZ art. 31 ust. 3g i 4",
        UZ,
        "Stawki",
    ),
    V(
        "stawka_rodzicielska",
        "jesli(usredniona and rodzicielski_w_1_roku, param('rate_averaged'), param('rate_parental'))",
        "Stawka za urlop rodzicielski",
        "UZ art. 31 ust. 2, 3, 3g",
        UZ,
        "Stawki",
    ),
    V(
        "rodzicielski_termin",
        "jesli(dziecko.zdarzenie == 'przysposobienie' or (przyjecie and przyjecie_okres_minimalny), "
        "dodaj_dni(dodaj_mies(dziecko.data_urodzenia, 12 * tabela('adoption_leave_max_child_age_years', 'adoption')), -1), "
        "koniec_roku(dziecko.data_urodzenia, param('parental_deadline_child_age_years')))",
        "Ostatni dzień na wykorzystanie urlopu rodzicielskiego",
        "KP art. 182¹ᶜ, art. 183 § 4¹–4², § 5",
        KP,
        G_PAR,
        description="Poród i rodzina zastępcza: do końca roku kalendarzowego, w którym dziecko kończy 6 lat. "
        "Przysposobienie: do ukończenia 14 lat (art. 183 § 4¹). Interpretacja: rodzina zastępcza w przypadku "
        "z art. 183 § 3 (urlop 38 tygodni z § 4²) – także do ukończenia 14 lat.",
    ),
]
