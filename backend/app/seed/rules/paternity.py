"""Rules: Urlop ojcowski."""

from __future__ import annotations

from app.seed.rules.helpers import (
    G_PAT,
    KP,
    P,
    V,
)

RULES: list[dict] = [
    # ======================================================================================
    # Urlop ojcowski
    # ======================================================================================
    V(
        "ojcowski_mozliwy",
        "tata_uprawniony and dziecko_zyje and dziecko.zdarzenie in ['porod', 'przysposobienie']",
        "Tata może skorzystać z urlopu (zasiłku) ojcowskiego",
        "KP art. 182³; UZ art. 29a ust. 1",
        KP,
        G_PAT,
    ),
    V(
        "ojcowski_termin",
        "jesli(dziecko.zdarzenie == 'przysposobienie', najwczesniej(dodaj_mies(data_zdarzenia, param('paternity_deadline_months')), "
        "dodaj_mies(dziecko.data_urodzenia, 12 * tabela('adoption_leave_max_child_age_years', 'adoption'))), "
        "dodaj_dni(dodaj_mies(dziecko.data_urodzenia, param('paternity_deadline_months')), -1))",
        "Ostatni dzień urlopu ojcowskiego",
        "KP art. 182³ § 1",
        KP,
        G_PAT,
        description="Przy przysposobieniu termin liczy się od uprawomocnienia postanowienia – silnik przyjmuje datę przyjęcia dziecka.",
    ),
    P(
        "tata_ojcowski",
        "tata",
        "paternity",
        "Urlop ojcowski",
        "jesli(jest(plan.ojcowski_od), plan.ojcowski_od, jesli(tata_macierzynski.aktywny and "
        "tata_macierzynski.start <= data_zdarzenia, dodaj_dni(tata_macierzynski.koniec, 1), data_zdarzenia))",
        "tygodnie(param('paternity_leave_weeks'))",
        "param('rate_maternity')",
        "KP art. 182³; UZ art. 31 ust. 1",
        KP,
        G_PAT,
        condition="ojcowski_mozliwy",
        payer="tata_platnik",
    ),
]
