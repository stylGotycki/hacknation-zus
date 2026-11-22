"""Rules: Ciąża: zasiłek chorobowy, zasiłek w wysokości zasiłku macierzyńskiego."""

from __future__ import annotations

from app.seed.rules.helpers import (
    G_SICK,
    KP,
    UZ,
    P,
    V,
)

RULES: list[dict] = [
    # ======================================================================================
    # Ciąża: zasiłek chorobowy, zasiłek w wysokości zasiłku macierzyńskiego
    # ======================================================================================
    V(
        "zwolnienie_b_dni",
        "dni_miedzy(mama.zwolnienie_b_od, mama.zwolnienie_b_do) + 1",
        "Długość zwolnienia lekarskiego z kodem B (dni)",
        "UZ art. 57 ust. 1 pkt 2",
        UZ,
        G_SICK,
        condition="porod and jest(mama.zwolnienie_b_od) and jest(mama.zwolnienie_b_do)",
    ),
    V(
        "okres_wyczekiwania",
        "jesli(mama.ubezpieczenie == 'obowiazkowe', tabela('sickness_waiting_days', 'mandatory'), "
        "tabela('sickness_waiting_days', 'voluntary'))",
        "Okres wyczekiwania na zasiłek chorobowy (dni)",
        "UZ art. 4 ust. 1",
        UZ,
        G_SICK,
    ),
    V(
        "wyczekiwanie_spelnione",
        "brak(mama.dni_ubezpieczenia) or mama.dni_ubezpieczenia >= okres_wyczekiwania",
        "Okres wyczekiwania minął",
        "UZ art. 4 ust. 1",
        UZ,
        G_SICK,
    ),
    V(
        "mama_chorobowe_prawo",
        "mama.obecny and mama.ubezpieczenie != 'brak' and wyczekiwanie_spelnione",
        "Mama ma prawo do zasiłku chorobowego",
        "UZ art. 4, 6",
        UZ,
        G_SICK,
    ),
    V(
        "limit_wynagrodzenia_chorobowego",
        "jesli(mama.wiek_50, param('employer_sickness_paid_days_over_50'), param('sickness_employer_paid_days'))",
        "Dni wynagrodzenia chorobowego od pracodawcy w roku",
        "KP art. 92 § 1",
        KP,
        G_SICK,
    ),
    V(
        "wynagrodzenie_chorobowe_dni",
        "jesli(mama.pracownik and mama_chorobowe_prawo and zwolnienie_b_dni > 0, "
        "min(zwolnienie_b_dni, max(0, limit_wynagrodzenia_chorobowego - mama.dni_chorobowego_w_roku)), 0)",
        "Dni wynagrodzenia chorobowego (płaci pracodawca)",
        "KP art. 92 § 1 pkt 2, § 4",
        KP,
        G_SICK,
    ),
    V(
        "zasilek_chorobowy_dni",
        "jesli(mama_chorobowe_prawo and zwolnienie_b_dni > 0, max(0, min(zwolnienie_b_dni, "
        "tabela('sickness_benefit_period_days', 'pregnancy')) - wynagrodzenie_chorobowe_dni), 0)",
        "Dni zasiłku chorobowego w ciąży (okres zasiłkowy 270 dni, wlicza się wynagrodzenie chorobowe)",
        "UZ art. 8 ust. 1, art. 12 ust. 1",
        UZ,
        G_SICK,
    ),
    P(
        "mama_wynagrodzenie_chorobowe",
        "mama",
        "pregnancy_sickness",
        "Wynagrodzenie chorobowe w ciąży (płaci pracodawca)",
        "mama.zwolnienie_b_od",
        "wynagrodzenie_chorobowe_dni",
        "param('rate_sickness_pregnancy')",
        "KP art. 92 § 1 pkt 2",
        KP,
        G_SICK,
        payer="'pracodawca'",
    ),
    P(
        "mama_zasilek_chorobowy",
        "mama",
        "pregnancy_sickness",
        "Zasiłek chorobowy w ciąży",
        "dodaj_dni(mama.zwolnienie_b_od, wynagrodzenie_chorobowe_dni)",
        "zasilek_chorobowy_dni",
        "param('rate_sickness_pregnancy')",
        "UZ art. 6, 8, 11 ust. 2 pkt 1",
        UZ,
        G_SICK,
        payer="mama_platnik",
    ),
    V(
        "zasilek_wys_mac",
        "porod and mama.obecny and mama.pracownik and mama.przyczyna_ustania == 'upadlosc_likwidacja_smierc' and "
        "jest(mama.ustanie_ubezpieczenia) and mama.ustanie_ubezpieczenia < data_zdarzenia",
        "Prawo do zasiłku w wysokości zasiłku macierzyńskiego (do porodu)",
        "UZ art. 30 ust. 3",
        UZ,
        G_SICK,
    ),
    P(
        "mama_zasilek_wys_mac",
        "mama",
        "maternity_equivalent",
        "Zasiłek w wysokości zasiłku macierzyńskiego",
        "dodaj_dni(mama.ustanie_ubezpieczenia, 1)",
        "dni_miedzy(dodaj_dni(mama.ustanie_ubezpieczenia, 1), najwczesniej(mama_macierzynski_przed.start, data_zdarzenia))",
        "param('rate_maternity')",
        "UZ art. 30 ust. 3, art. 31 ust. 1",
        UZ,
        G_SICK,
        condition="zasilek_wys_mac",
        payer="'zus'",
    ),
    V(
        "koniec_ostatniego_okresu",
        "najpozniej(tata_rodzicielski_wspolny.koniec, tata_rodzicielski_wylaczny.koniec, mama_rodzicielski.koniec, "
        "koniec_ciaglosci, tata_ojcowski.koniec)",
        "Ostatni dzień ostatniego zasiłku macierzyńskiego w rodzinie",
        "UZ art. 67",
        UZ,
        "Terminy",
    ),
]
