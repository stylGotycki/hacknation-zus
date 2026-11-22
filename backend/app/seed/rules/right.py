"""Rules: Prawo do zasiłku – dla każdego rodzica."""

from __future__ import annotations

from app.seed.rules.helpers import (
    G_BASE,
    G_PAR,
    G_RIGHT,
    KP,
    PARENTS,
    UZ,
    V,
)

RULES: list[dict] = [
    # ======================================================================================
    # Prawo do zasiłku – dla każdego rodzica
    # ======================================================================================
    *[
        rule
        for p, gen in PARENTS.items()
        for rule in (
            V(
                f"{p}_samoplatnik",
                f"{p}.zatrudnienie in ['dzialalnosc', 'wspolpracujaca']",
                f"Sam opłaca składki ({gen})",
                "UZ art. 2a ust. 1",
                UZ,
                G_RIGHT,
            ),
            V(
                f"{p}_dlug_ponad_prog",
                f"{p}_samoplatnik and {p}.dlug > param('contribution_debt_threshold_ratio') * param('minimum_wage')",
                f"Zadłużenie składkowe ponad 1% minimalnego wynagrodzenia ({gen})",
                "UZ art. 2a ust. 1",
                UZ,
                G_RIGHT,
            ),
            V(
                f"{p}_dlug_przedawnia",
                f"{p}_dlug_ponad_prog and (jesli(jest({p}.dlug_splacony), {p}.dlug_splacony, dzis()) > "
                f"dodaj_mies(data_zdarzenia, param('debt_repayment_window_months')))",
                f"Zadłużenie niespłacone w 6 miesięcy – prawo przedawnione ({gen})",
                "UZ art. 2a ust. 2",
                UZ,
                G_RIGHT,
            ),
            V(
                f"{p}_dlug_do_splaty",
                f"{p}_dlug_ponad_prog and not {p}_dlug_przedawnia and brak({p}.dlug_splacony)",
                f"Zasiłek po spłacie całego zadłużenia ({gen})",
                "UZ art. 2a ust. 1, art. 64 ust. 3",
                UZ,
                G_RIGHT,
            ),
            V(
                f"{p}_ubezpieczony",
                f"{p}.obecny and ({p}.ubezpieczony_w_dniu_zdarzenia or {p}.urlop_wychowawczy)",
                f"Ubezpieczenie chorobowe albo urlop wychowawczy w dniu porodu / przyjęcia ({gen})",
                "UZ art. 29 ust. 1–2",
                UZ,
                G_RIGHT,
            ),
            V(
                f"{p}_platnik",
                f"jesli({p}_samoplatnik or ({p}.liczba_ubezpieczonych <= param('payer_threshold_insured'))"
                + (" or mama_po_ustaniu" if p == "mama" else "")
                + f", 'zus', jesli(brak({p}.liczba_ubezpieczonych), 'nieznany', 'pracodawca'))",
                f"Kto ustala i wypłaca zasiłki ({gen})",
                "UZ art. 61 ust. 1–2",
                UZ,
                G_RIGHT,
                description="'pracodawca' = płatnik składek zgłaszający ponad 20 ubezpieczonych.",
            ),
            V(
                f"{p}_podstawa",
                f"zaokr(jesli({p}.pracownik, max({p}.podstawa_brutto * (1 - param('social_contribution_deduction')), "
                f"jesli({p}.wymiar_etatu >= 1, param('minimum_wage') * (1 - param('social_contribution_deduction')), 0)), "
                f"min({p}.podstawa_brutto, param('voluntary_sickness_base_max')) * (1 - param('social_contribution_deduction'))), 2)",
                f"Podstawa wymiaru zasiłku ({gen})",
                "UZ art. 36, 45, 47, 48, 52; ZAL",
                UZ,
                G_BASE,
                condition=f"jest({p}.podstawa_brutto)",
                description="Pracownik: przeciętne wynagrodzenie − 13,71%, przy pełnym etacie nie mniej niż płaca "
                "minimalna − 13,71%. Niepracownik: przeciętny przychód (podstawa składki chorobowej, "
                "najwyżej 23 550 zł) − 13,71%.",
            ),
            V(
                f"{p}_praca",
                f"jesli({p}.pracownik, {p}.praca_w_rodzicielskim, 0)",
                f"Część etatu wykonywana w czasie urlopu rodzicielskiego ({gen})",
                "KP art. 182¹ᵉ § 1",
                KP,
                G_PAR,
            ),
        )
    ],
    V(
        "mama_po_ustaniu",
        "porod and mama.obecny and not mama_ubezpieczony and (mama.przyczyna_ustania in "
        "['upadlosc_likwidacja_smierc', 'naruszenie_prawa'] or mama.umowa_przedluzona_do_porodu)",
        "Prawo do zasiłku macierzyńskiego po ustaniu ubezpieczenia (ustało w ciąży)",
        "UZ art. 30 ust. 1 i 4",
        UZ,
        G_RIGHT,
        description="Ubezpieczenie ustało w ciąży wskutek śmierci, upadłości lub likwidacji pracodawcy, "
        "z naruszeniem prawa (wyrok) albo umowa terminowa przedłużona do porodu.",
    ),
    V(
        "mama_uprawniona",
        "zdarzenie_uprawnia and (mama_ubezpieczony or mama_po_ustaniu) and not mama_dlug_przedawnia",
        "Mama ma prawo do zasiłku macierzyńskiego",
        "UZ art. 29 ust. 1, art. 30, art. 2a",
        UZ,
        G_RIGHT,
    ),
    V(
        "tata_uprawniony",
        "zdarzenie_uprawnia and tata_ubezpieczony and not tata_dlug_przedawnia",
        "Tata ma prawo do zasiłku macierzyńskiego (własny tytuł)",
        "UZ art. 29 ust. 2–10, art. 2a",
        UZ,
        G_RIGHT,
    ),
]
