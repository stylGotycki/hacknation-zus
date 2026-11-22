"""Rules: Walidacja planu."""

from __future__ import annotations

from app.seed.rules.helpers import (
    KP,
    PARENTS,
    M,
)

RULES: list[dict] = [
    # ======================================================================================
    # Walidacja planu
    # ======================================================================================
    M(
        "walidacja",
        "w_martwe_przed_porodem",
        "dziecko.martwe_urodzenie and not dziecko.urodzone",
        "Martwe urodzenie przed porodem",
        "Martwe urodzenie można wskazać dopiero po porodzie (podaj datę porodu).",
        "KP art. 180¹; RZ § 13 ust. 1 pkt 2",
        KP,
    ),
    M(
        "walidacja",
        "w_zgon_daty",
        "jest(dziecko.data_zgonu) and (not dziecko.urodzone or dziecko.data_zgonu < dziecko.data_porodu or dziecko.data_zgonu > dzis())",
        "Data zgonu dziecka",
        "Data zgonu dziecka musi przypadać po porodzie i nie później niż dziś.",
        "KP art. 180¹",
        KP,
    ),
    M(
        "walidacja",
        "w_przed_porodem_max",
        "plan.przed_porodem_tyg > param('maternity_before_birth_max_weeks')",
        "Za dużo urlopu przed porodem",
        "Przed przewidywaną datą porodu można wykorzystać najwyżej {param('maternity_before_birth_max_weeks')} tygodni urlopu macierzyńskiego.",
        "KP art. 180 § 2",
        KP,
    ),
    M(
        "walidacja",
        "w_przed_porodem_tylko_porod",
        "plan.przed_porodem_tyg > 0 and not porod",
        "Urlop przed porodem",
        "Urlop przed porodem dotyczy tylko porodu (nie przyjęcia dziecka).",
        "KP art. 180 § 2",
        KP,
    ),
    M(
        "walidacja",
        "w_dla_taty_min",
        "dla_taty_dni > 0 and mama_pula_po_porodzie - dla_taty_dni < tygodnie(matka_min_osobiscie_tyg)",
        "Za dużo urlopu macierzyńskiego dla taty",
        "Mama musi wykorzystać po porodzie co najmniej {matka_min_osobiscie_tyg} tygodni urlopu macierzyńskiego – "
        "tata może przejąć najwyżej {zaokr((mama_pula_po_porodzie - tygodnie(matka_min_osobiscie_tyg)) / 7, 1)} tygodni.",
        "KP art. 180 § 4 i § 6; UZ art. 29 ust. 3 i 5",
        KP,
    ),
    M(
        "walidacja",
        "w_tata_rodzicielski_max",
        "oboje_rodzicielski and tata_rodzicielski_tyg > wymiar_rodzicielski_tyg - wylaczna_czesc_tyg",
        "Za dużo urlopu rodzicielskiego dla taty",
        "Każde z rodziców ma wyłączne prawo do {wylaczna_czesc_tyg} tygodni – tata może wziąć najwyżej "
        "{wymiar_rodzicielski_tyg - wylaczna_czesc_tyg} tygodni z {wymiar_rodzicielski_tyg}.",
        "KP art. 182¹ᵃ § 4",
        KP,
    ),
    *[
        rule
        for p, gen in PARENTS.items()
        for rule in (
            M(
                "walidacja",
                f"w_{p}_praca_max",
                f"{p}.praca_w_rodzicielskim > param('parental_work_max_fraction')",
                f"Za dużo pracy w trakcie urlopu rodzicielskiego ({gen})",
                "W czasie urlopu rodzicielskiego można pracować najwyżej na {zaokr(param('parental_work_max_fraction') * 100, 0)}% etatu.",
                "KP art. 182¹ᵉ § 1",
                KP,
            ),
            M(
                "walidacja",
                f"w_{p}_praca_pracownik",
                f"{p}.praca_w_rodzicielskim > 0 and not {p}.pracownik",
                f"Łączenie urlopu z pracą ({gen})",
                "Łączyć urlop rodzicielski z pracą u pracodawcy udzielającego urlopu może tylko pracownik.",
                "KP art. 182¹ᵉ § 1",
                KP,
            ),
            M(
                "walidacja",
                f"w_{p}_czesci",
                f"plan.czesci_{p} > param('parental_max_parts')",
                f"Za dużo części urlopu rodzicielskiego ({gen})",
                "Urlop rodzicielski udziela się jednorazowo albo najwyżej w {param('parental_max_parts')} częściach.",
                "KP art. 182¹ᶜ, art. 182¹ᵈ § 2",
                KP,
            ),
        )
    ],
    M(
        "walidacja",
        "w_rodzicielski_mamy_start",
        "jest(plan.rodzicielski_mama_od) and mama_rodzicielski_dni > 0 and plan.rodzicielski_mama_od <= koniec_ciaglosci",
        "Urlop rodzicielski w trakcie macierzyńskiego",
        "Urlop rodzicielski mamy może zacząć się dopiero po urlopie macierzyńskim (po {koniec_ciaglosci}).",
        "KP art. 182¹ᵃ",
        KP,
    ),
    M(
        "walidacja",
        "w_tata_nakladanie",
        "naklada(tata_ojcowski, tata_macierzynski) or naklada(tata_ojcowski, tata_rodzicielski_wylaczny) or "
        "naklada(tata_ojcowski, tata_rodzicielski_wspolny) or naklada(tata_macierzynski, tata_rodzicielski_wylaczny) or "
        "naklada(tata_ojcowski, tata_macierzynski_szpital)",
        "Urlopy taty nakładają się",
        "Urlop ojcowski, macierzyński i rodzicielski taty nie mogą trwać jednocześnie – zmień datę początku urlopu.",
        "KP art. 182³, art. 182¹ᵃ",
        KP,
    ),
    M(
        "walidacja",
        "w_ojcowski_czesci",
        "plan.ojcowski_czesci > param('paternity_max_parts') or tygodnie(param('paternity_leave_weeks')) / plan.ojcowski_czesci < tygodnie(param('paternity_min_part_weeks'))",
        "Podział urlopu ojcowskiego",
        "Urlop ojcowski można wykorzystać jednorazowo albo w {param('paternity_max_parts')} częściach, każda co najmniej {param('paternity_min_part_weeks')} tydzień.",
        "KP art. 182³ § 1¹",
        KP,
    ),
]
