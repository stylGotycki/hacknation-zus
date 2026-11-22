"""Rules: Stawka uśredniona (81,5%)."""

from __future__ import annotations

from app.seed.rules.helpers import (
    UZ,
    V,
)

RULES: list[dict] = [
    # ======================================================================================
    # Stawka uśredniona (81,5%)
    # ======================================================================================
    V(
        "usredniona_w_terminie",
        "przed_zdarzeniem or dzis() <= dodaj_dni(data_zdarzenia, param('averaged_application_deadline_days')) or "
        "(jest(plan.wniosek_usredniony_zlozony) and plan.wniosek_usredniony_zlozony <= "
        "dodaj_dni(data_zdarzenia, param('averaged_application_deadline_days')))",
        "Wniosek o stawkę uśrednioną jest jeszcze możliwy albo złożony w terminie",
        "UZ art. 30a ust. 1–2",
        UZ,
        "Stawki",
    ),
    V(
        "usredniona",
        "plan.stawka_usredniona and usredniona_w_terminie and dziecko_zyje and (mama_uprawniona or (przyjecie and tata_uprawniony))",
        "Zasiłek w stawce uśrednionej (wniosek z art. 30a)",
        "UZ art. 30a, art. 31 ust. 3",
        UZ,
        "Stawki",
    ),
    V(
        "stawka_macierzynska",
        "jesli(usredniona, param('rate_averaged'), param('rate_maternity'))",
        "Stawka za urlop macierzyński / na warunkach urlopu macierzyńskiego",
        "UZ art. 31 ust. 1 i 3",
        UZ,
        "Stawki",
    ),
]
