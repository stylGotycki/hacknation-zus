"""Rules: Ryzyka."""

from __future__ import annotations

from app.seed.rules.helpers import (
    ENTITLED,
    KP,
    PARENTS,
    PR,
    UZ,
    M,
)

RULES: list[dict] = [
    # ======================================================================================
    # Ryzyka
    # ======================================================================================
    *[
        rule
        for p, gen in PARENTS.items()
        for rule in (
            M(
                "ryzyko",
                f"r_brak_ubezpieczenia_{p}",
                f"{p}.obecny and (porod or przyjecie) and not {ENTITLED[p]} and not {p}_dlug_przedawnia"
                + (" and not przyjecie_tata_calosc" if p == "tata" else ""),
                f"Brak prawa do zasiłku macierzyńskiego ({gen})",
                "Zasiłek macierzyński przysługuje, gdy w dniu porodu (przyjęcia dziecka) podlegasz ubezpieczeniu chorobowemu albo "
                "przebywasz na urlopie wychowawczym. Długość ubezpieczenia nie ma znaczenia.",
                "UZ art. 29 ust. 1; Poradnik ZUS 2026",
                UZ,
                person=p,
                severity="high",
                order=1,
            ),
            M(
                "ryzyko",
                f"r_dlug_{p}",
                f"{p}_dlug_ponad_prog",
                f"Zadłużenie z tytułu składek ({gen})",
                "Zadłużenie przekracza 1% minimalnego wynagrodzenia ({zaokr(param('contribution_debt_threshold_ratio') * param('minimum_wage'), 2)} zł): "
                "zasiłek nie przysługuje do spłaty całości. "
                f"{{jesli({p}_dlug_przedawnia, 'Zadłużenia nie spłacono w ciągu 6 miesięcy – prawo do zasiłku przedawniło się.', 'Spłać je w ciągu ' + param('debt_repayment_window_months') + ' miesięcy od porodu, inaczej prawo się przedawni.')}}",
                "UZ art. 2a",
                UZ,
                person=p,
                severity="high",
                order=2,
            ),
            M(
                "ryzyko",
                f"r_ulga_na_start_{p}",
                f"{p}.ulga_na_start",
                f"Ulga na start ({gen})",
                "W okresie ulgi na start nie podlegasz ubezpieczeniom społecznym, w tym chorobowemu – nie masz prawa do zasiłków. "
                "Możesz z ulgi zrezygnować, składając zgłoszenie do ubezpieczeń.",
                "Poradnik ZUS 2026 – Tzw. ulga na start",
                PR,
                person=p,
                severity="high",
                order=3,
            ),
            M(
                "ryzyko",
                f"r_dobrowolne_po_{p}",
                f"{p}.ubezpieczenie == 'dobrowolne' and {ENTITLED[p]}",
                f"Ponowne zgłoszenie do ubezpieczenia chorobowego ({gen})",
                "Gdy zaczynasz pobierać zasiłek macierzyński, dobrowolne ubezpieczenie chorobowe ustaje. Po zakończeniu zasiłku "
                "zgłoś się do niego ponownie (ZUS ZUA), aby znów mieć prawo do zasiłków.",
                "Poradnik ZUS 2026 – Ważne informacje uzupełniające",
                PR,
                person=p,
                severity="medium",
                order=10,
            ),
            M(
                "ryzyko",
                f"r_dobrowolne_wstecz_{p}",
                f"przed_zdarzeniem and {p}.zatrudnienie in ['zlecenie', 'dzialalnosc', 'wspolpracujaca'] and {p}.ubezpieczenie == 'brak' and not {p}.ulga_na_start",
                f"Brak dobrowolnego ubezpieczenia chorobowego ({gen})",
                "Do dobrowolnego ubezpieczenia chorobowego nie można zgłosić się z datą wsteczną – objęcie następuje od dnia złożenia "
                "zgłoszenia ZUS ZUA. Bez niego w dniu porodu zasiłek macierzyński nie przysługuje.",
                "Poradnik ZUS 2026; UZ art. 29 ust. 1",
                PR,
                person=p,
                severity="high",
                order=4,
            ),
        )
    ],
    M(
        "ryzyko",
        "r_9_tygodni",
        "oboje_rodzicielski and tata_rodzicielski_tyg < wylaczna_czesc_tyg",
        "Część urlopu taty przepadnie",
        "Tata ma wyłączne prawo do {wylaczna_czesc_tyg} tygodni urlopu rodzicielskiego, których nie można przenieść na mamę – "
        "jeśli z nich nie skorzysta, przepadną.",
        "KP art. 182¹ᵃ § 4",
        KP,
        person="tata",
        severity="medium",
        order=11,
    ),
    M(
        "ryzyko",
        "r_pierwszy_rok",
        "usredniona and wymiar_rodzicielski_tyg > 0 and not rodzicielski_w_1_roku",
        "Urlop rodzicielski poza pierwszym rokiem życia",
        "Jeśli w pierwszym roku życia dziecka nie wykorzystasz ani jednego dnia zasiłku za urlop rodzicielski, zasiłek za ten urlop "
        "wyniesie 70%, a za urlop macierzyński przysługuje jednorazowe wyrównanie do 100% – na wniosek.",
        "UZ art. 31 ust. 3g i 4",
        UZ,
        person="mama",
        severity="medium",
        order=12,
    ),
    M(
        "ryzyko",
        "r_usredniona_po_terminie",
        "plan.stawka_usredniona and not usredniona_w_terminie and mama_uprawniona",
        "Termin na stawkę 81,5% minął",
        "Wniosek o stawkę uśrednioną trzeba złożyć najpóźniej {param('averaged_application_deadline_days')} dni po porodzie – "
        "zasiłek wyniesie 100% za urlop macierzyński i 70% za rodzicielski.",
        "UZ art. 30a, art. 31 ust. 1–2",
        UZ,
        person="mama",
        severity="high",
        order=5,
    ),
    M(
        "ryzyko",
        "r_ojcowski_po_terminie",
        "tata_ojcowski.aktywny and tata_ojcowski.koniec > ojcowski_termin",
        "Urlop ojcowski po terminie",
        "Urlop ojcowski trzeba wykorzystać do {ojcowski_termin} – część po tym dniu nie przysługuje.",
        "KP art. 182³ § 1",
        KP,
        person="tata",
        severity="high",
        order=6,
    ),
    M(
        "ryzyko",
        "r_rodzicielski_po_terminie",
        "najpozniej(mama_rodzicielski.koniec, tata_rodzicielski_wspolny.koniec, tata_rodzicielski_wylaczny.koniec) > rodzicielski_termin",
        "Urlop rodzicielski po terminie",
        "Urlop rodzicielski trzeba wykorzystać do {rodzicielski_termin}.",
        "KP art. 182¹ᶜ",
        KP,
        severity="high",
        order=7,
    ),
    M(
        "ryzyko",
        "r_okres_zasilkowy",
        "zwolnienie_b_dni > tabela('sickness_benefit_period_days', 'pregnancy')",
        "Koniec okresu zasiłkowego",
        "Zasiłek chorobowy w ciąży przysługuje najdłużej {tabela('sickness_benefit_period_days', 'pregnancy')} dni. Gdy dalej jesteś "
        "niezdolna do pracy i leczenie rokuje powrót do zdrowia, możesz ubiegać się o świadczenie rehabilitacyjne.",
        "UZ art. 8 ust. 1, art. 18",
        UZ,
        person="mama",
        severity="medium",
        order=13,
    ),
    M(
        "ryzyko",
        "r_wyczekiwanie",
        "zwolnienie_b_dni > 0 and mama.ubezpieczenie != 'brak' and not wyczekiwanie_spelnione",
        "Okres wyczekiwania na zasiłek chorobowy",
        "Zasiłek chorobowy przysługuje po {okres_wyczekiwania} dniach nieprzerwanego ubezpieczenia chorobowego "
        "({jesli(mama.ubezpieczenie == 'obowiazkowe', 'obowiązkowego', 'dobrowolnego')}). Zasiłku macierzyńskiego to nie dotyczy.",
        "UZ art. 4 ust. 1",
        UZ,
        person="mama",
        severity="medium",
        order=14,
    ),
    M(
        "ryzyko",
        "r_kontrola_zwolnien",
        "zwolnienie_b_dni > 0",
        "Kontrola zwolnienia lekarskiego",
        "Praca zarobkowa albo aktywność niezgodna z celem zwolnienia w czasie zwolnienia oznacza utratę zasiłku za cały okres zwolnienia.",
        "UZ art. 17",
        UZ,
        person="mama",
        severity="info",
        order=20,
    ),
    M(
        "ryzyko",
        "r_ochrona",
        "mama.pracownik and porod",
        "Ochrona przed zwolnieniem z pracy",
        "W ciąży i w czasie urlopu macierzyńskiego (oraz od złożenia wniosku o urlop związany z rodzicielstwem) pracodawca nie może "
        "wypowiedzieć ani rozwiązać umowy, poza wyjątkami z art. 177 KP.",
        "KP art. 177 § 1, § 1¹, § 4",
        KP,
        person="mama",
        severity="info",
        order=21,
    ),
    M(
        "ryzyko",
        "r_umowa_terminowa",
        "mama.pracownik and porod and mama.umowa_przedluzona_do_porodu",
        "Umowa na czas określony",
        "Umowa na czas określony (lub okres próbny dłuższy niż miesiąc), która rozwiązałaby się po upływie "
        "{param('gestation_months_for_contract_extension')}. miesiąca ciąży, przedłuża się do dnia porodu – wtedy zasiłek "
        "macierzyński przysługuje także po ustaniu ubezpieczenia (nie dotyczy umowy na zastępstwo).",
        "KP art. 177 § 3–3¹; UZ art. 30 ust. 4",
        KP,
        person="mama",
        severity="info",
        order=22,
    ),
    M(
        "ryzyko",
        "r_pozorna_umowa",
        "porod and przed_zdarzeniem and (mama.zatrudnienie in ['umowa_o_prace', 'zlecenie'] or tata.zatrudnienie in ['umowa_o_prace', 'zlecenie'])",
        "Umowa zawarta dla pozoru",
        "Umowa o pracę lub zlecenia zawarta dla pozoru albo w celu obejścia prawa nie daje ubezpieczenia – ZUS może zbadać jej "
        "okoliczności i wynagrodzenie oraz wydać decyzję o niepodleganiu ubezpieczeniom.",
        "Poradnik ZUS 2026",
        PR,
        severity="info",
        order=23,
    ),
    M(
        "ryzyko",
        "r_podwyzszenie",
        "jest(param('parental_benefit_amount')) and mama_uprawniona and jest(mama_podstawa) and mama_podstawa * param('rate_parental') < param('parental_benefit_amount')",
        "Zasiłek niższy niż świadczenie rodzicielskie",
        "Gdy miesięczny zasiłek (po odliczeniu zaliczki na podatek) jest niższy niż kwota świadczenia rodzicielskiego "
        "({param('parental_benefit_amount')} zł), podwyższa się go do tej kwoty; za część miesiąca proporcjonalnie.",
        "UZ art. 31 ust. 3a–3c; Poradnik ZUS 2026",
        UZ,
        person="mama",
        severity="info",
        order=24,
    ),
]
