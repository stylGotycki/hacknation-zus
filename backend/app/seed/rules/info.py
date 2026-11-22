"""Rules: Informacje i założenia obliczeń."""

from __future__ import annotations

from app.seed.rules.helpers import (
    KP,
    PR,
    UZ,
    M,
)

RULES: list[dict] = [
    # ======================================================================================
    # Informacje i założenia obliczeń
    # ======================================================================================
    M(
        "informacja",
        "i_wyplata",
        "mama_uprawniona or tata_uprawniony",
        "Termin wypłaty",
        "Płatnik składek wypłaca zasiłek w terminie wypłaty wynagrodzeń, ZUS – na bieżąco, najpóźniej "
        "{param('payment_deadline_days')} dni od wyjaśnienia ostatniej okoliczności. Na osi czasu pokazujemy przelew "
        "zasiłku za każdy miesiąc urlopu, przyjmując wypłatę {param('payout_day')}. dnia następnego miesiąca (założenie – "
        "zmienisz je w parametrach).",
        "UZ art. 64 ust. 1",
        UZ,
    ),
    M(
        "informacja",
        "i_wychowawczy",
        "mama.urlop_wychowawczy or tata.urlop_wychowawczy",
        "Urlop wychowawczy",
        "Zasiłek macierzyński przysługuje, gdy dziecko urodzi się w czasie urlopu wychowawczego, ale nie przysługuje za czas tego urlopu.",
        "UZ art. 29 ust. 1; Poradnik ZUS 2026",
        UZ,
    ),
    M(
        "informacja",
        "i_kontakt",
        "True",
        "Pytania do ZUS",
        "Skrzynka mama@zus.pl, infolinia 22 560 16 00, eZUS i aplikacja mZUS, placówki ZUS.",
        "Poradnik ZUS 2026 – Pozostańmy w kontakcie",
        PR,
        order=99,
    ),
    M(
        "zalozenie",
        "z_kwoty",
        "True",
        "Kwoty",
        "Podstawa wymiaru × stawka (kwoty brutto); za każdy dzień 1/{param('benefit_daily_divisor')} miesięcznej kwoty. "
        "Kwota netto nie jest liczona – zaliczka na podatek nie wynika ze źródeł przewodnika.",
        "UZ art. 11 ust. 4–5, art. 36 ust. 3",
        UZ,
    ),
    M(
        "zalozenie",
        "z_podstawa",
        "jest(mama_podstawa) or jest(tata_podstawa)",
        "Podstawa wymiaru",
        "Pracownik: przeciętne wynagrodzenie z 12 miesięcy (lub pełnych miesięcy ubezpieczenia) − 13,71%, przy pełnym etacie nie mniej "
        "niż {zaokr(param('minimum_wage') * (1 - param('social_contribution_deduction')), 2)} zł. Niepracownik: przeciętny przychód − 13,71%, "
        "najwyżej {zaokr(param('voluntary_sickness_base_max') * (1 - param('social_contribution_deduction')), 2)} zł.",
        "UZ art. 36, 38, 45, 48; ZAL",
        UZ,
    ),
    M(
        "zalozenie",
        "z_tydzien",
        "True",
        "Tydzień urlopu",
        "Tydzień urlopu = 7 dni kalendarzowych; urlop macierzyński zaczyna się w dniu porodu, "
        "jeśli nie wykorzystano go wcześniej.",
        "KP art. 183¹",
        KP,
    ),
]
