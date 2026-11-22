"""Rules of the guide – written only from the six source documents (see parameters_2026.py).

Each rule is data: expressions in the rule language (app/engine/expressions.py) that read
facts (app/engine/facts.py), parameters (param / tabela) and other rules by their code.
The seed loads them into the `rule` table; afterwards they are edited in the admin panel.
Source codes in `source`: KP, UZ, RZ, RW, PR, ZAL.
"""

from __future__ import annotations

KP, UZ, RZ, RW, PR, ZAL = "KP", "UZ", "RZ", "RW", "PR", "ZAL"
PARENTS = {"mama": "mamy", "tata": "taty"}
ENTITLED = {"mama": "mama_uprawniona", "tata": "tata_uprawniony"}


def _soonest(key):
    """Template: the earliest start date if the request is filed today."""
    return f"{{dodaj_dni(dzis(), tabela('application_lead_days', '{key}'))}}"


# Advice shown once a deadline has passed (rule field `late_text_pl`): what is lost, what can
# still be done. Every sentence follows from the cited provisions of the deadline rule.
LATE = {
    "t_usredniona": "Stawki {zaokr(param('rate_averaged') * 100, 1)}% nie można już wybrać. Zasiłek wyniesie "
    "{zaokr(param('rate_maternity') * 100, 0)}% podstawy za urlop macierzyński i {zaokr(param('rate_parental') * 100, 0)}% "
    "za urlop rodzicielski.",
    "t_mac_przed": "Wniosek trzeba złożyć najpóźniej {tabela('application_lead_days', 'maternity_before_birth')} dni przed "
    "rozpoczęciem urlopu – wskaż późniejszy początek (najwcześniej "
    + _soonest("maternity_before_birth")
    + "). "
    "Jeśli nie wykorzystasz urlopu przed porodem, zacznie się on w dniu porodu.",
    "t_rezygnacja": "Wskaż późniejszy dzień powrotu do pracy – co najmniej {tabela('application_lead_days', 'mother_resignation')} "
    "dni od złożenia wniosku (najwcześniej "
    + _soonest("mother_resignation")
    + "). Do tego dnia trwa Twój urlop macierzyński.",
    "t_tata_macierzynski": "Wskaż późniejszy początek urlopu – co najmniej {tabela('application_lead_days', 'father_maternity_part')} "
    "dni od złożenia wniosku (najwcześniej "
    + _soonest("father_maternity_part")
    + "). Do tego czasu urlop wykorzystuje mama.",
    "t_uzupelniajacy": "{jesli(jesli(uzup_bierze == 'tata', tata.pracownik, mama.pracownik), "
    "'Pracodawca jest obowiązany uwzględnić tylko wniosek złożony w terminie. Złóż go od razu i ustal z pracodawcą, czy go uwzględni – urlop uzupełniający musi zacząć się bezpośrednio po macierzyńskim.', "
    "'Wniosek trzeba było złożyć przed końcem zasiłku za urlop macierzyński. Zapytaj w ZUS, czy możesz go jeszcze złożyć.')}",
    "t_rodzicielski_mama": "{jesli(mama.pracownik, 'Pracodawca jest obowiązany uwzględnić wniosek złożony co najmniej ' + "
    "tabela('application_lead_days', 'parental') + ' dni przed początkiem urlopu – wskaż późniejszy start (najwcześniej ' + "
    "dodaj_dni(dzis(), tabela('application_lead_days', 'parental')) + ').', 'Złóż wniosek do ZUS jak najszybciej – zasiłek "
    "nadal Ci przysługuje, a roszczenie przedawnia się po ' + param('claim_limitation_months') + ' miesiącach od ostatniego dnia okresu.')} "
    "Urlop wykorzystaj do {rodzicielski_termin}.",
    "t_rodzicielski_tata": "{jesli(tata.pracownik, 'Pracodawca jest obowiązany uwzględnić wniosek złożony co najmniej ' + "
    "tabela('application_lead_days', 'parental') + ' dni przed początkiem urlopu – wskaż późniejszy start (najwcześniej ' + "
    "dodaj_dni(dzis(), tabela('application_lead_days', 'parental')) + ').', 'Złóż wniosek do ZUS jak najszybciej – zasiłek "
    "nadal przysługuje, a roszczenie przedawnia się po ' + param('claim_limitation_months') + ' miesiącach od ostatniego dnia okresu.')} "
    "Urlop wykorzystaj do {rodzicielski_termin}.",
    "t_praca_mama": "Wskaż późniejszy początek pracy (najwcześniej "
    + _soonest("work_combination")
    + "). Do tego dnia "
    "korzystasz z pełnego urlopu rodzicielskiego.",
    "t_praca_tata": "Wskaż późniejszy początek pracy (najwcześniej "
    + _soonest("work_combination")
    + "). Do tego dnia "
    "tata korzysta z pełnego urlopu rodzicielskiego.",
    "t_ojcowski": "{jesli(tata.pracownik, 'Wskaż późniejszy początek urlopu (najwcześniej ' + dodaj_dni(dzis(), "
    "tabela('application_lead_days', 'paternity')) + ').', 'Złóż wniosek do ZUS jak najszybciej.')} Urlop ojcowski "
    "musi się skończyć najpóźniej {ojcowski_termin}.",
    "t_ojcowski_do": "Prawo do urlopu i zasiłku ojcowskiego wygasło – niewykorzystana część przepada.",
    "t_rodzicielski_do": "Niewykorzystana część urlopu rodzicielskiego przepada – zasiłek za nią nie przysługuje.",
    "t_na_warunkach": "Pracodawca jest obowiązany uwzględnić wniosek złożony w ciągu "
    "{tabela('application_lead_days', 'taken_in_application')} dni od przyjęcia dziecka. "
    "{jesli(dodaj_dni(data_zdarzenia, tabela('application_lead_days', 'taken_in_start_max')) >= dzis(), "
    "'Złóż go od razu – urlop musi się zacząć najpóźniej ' + dodaj_dni(data_zdarzenia, tabela('application_lead_days', 'taken_in_start_max')) + '.', "
    "'Minął też dzień, w którym urlop musiał się zacząć (' + dodaj_dni(data_zdarzenia, tabela('application_lead_days', 'taken_in_start_max')) + ') – ustal z pracodawcą, czy go udzieli.')}",
    "t_dlug_mama": "Zadłużenie nie zostało spłacone w ciągu {param('debt_repayment_window_months')} miesięcy – prawo "
    "do zasiłku z tego zdarzenia przedawniło się.",
    "t_dlug_tata": "Zadłużenie nie zostało spłacone w ciągu {param('debt_repayment_window_months')} miesięcy – prawo "
    "do zasiłku z tego zdarzenia przedawniło się.",
    "t_przedawnienie": "Roszczenie się przedawniło. Wyjątki: jeśli nie mogłeś go zgłosić z przyczyn od Ciebie "
    "niezależnych, {param('claim_limitation_months')} miesięcy liczy się od dnia, w którym ustała przeszkoda; jeśli "
    "zasiłku nie wypłacono przez błąd płatnika lub ZUS, roszczenie przedawnia się po 3 latach.",
}


def V(code, expression, title, basis, source, group, condition=None, description=""):  # noqa: N802
    return dict(
        code=code,
        kind="wartosc",
        expression=expression,
        title_pl=title,
        legal_basis=basis,
        source=source,
        group_pl=group,
        condition=condition,
        description_pl=description,
    )


def P(
    code,
    person,
    period_kind,
    title,
    start,
    days,
    rate,
    basis,
    source,
    group,  # noqa: N802
    condition=None,
    work=None,
    payer=None,
    description="",
):
    return dict(
        code=code,
        kind="okres",
        person=person,
        period_kind=period_kind,
        title_pl=title,
        start=start,
        expression=days,
        rate=rate,
        work=work,
        payer=payer,
        legal_basis=basis,
        source=source,
        group_pl=group,
        condition=condition,
        description_pl=description,
    )


def B(
    code,
    person,
    title,
    condition,
    status,
    text,
    periods,
    basis,
    source,
    payer=None,  # noqa: N802
    apply_to="",
    order=0,
):
    return dict(
        code=code,
        kind="swiadczenie",
        person=person,
        title_pl=title,
        condition=condition,
        status=status,
        text_pl=text,
        periods=periods,
        legal_basis=basis,
        source=source,
        payer=payer,
        apply_to_pl=apply_to,
        order=order,
        group_pl="Świadczenia",
    )


def M(
    kind,
    code,
    condition,
    title,
    text,
    basis,
    source,
    person="rodzina",
    benefit=None,  # noqa: N802
    severity=None,
    date=None,
    deadline_kind=None,
    order=0,
    group=None,
    late="",
):
    groups = {
        "dokument": "Dokumenty",
        "termin": "Terminy",
        "ryzyko": "Ryzyka",
        "informacja": "Informacje",
        "zalozenie": "Założenia obliczeń",
        "walidacja": "Walidacja planu",
    }
    return dict(
        code=code,
        kind=kind,
        condition=condition,
        title_pl=title,
        text_pl=text,
        legal_basis=basis,
        source=source,
        person=person,
        benefit=benefit,
        severity=severity,
        expression=date,
        deadline_kind=deadline_kind,
        late_text_pl=late or LATE.get(code, ""),
        order=order,
        group_pl=group or groups[kind],
    )


G_EVENT = "Zdarzenie i dziecko"
G_RIGHT = "Prawo do zasiłku"
G_BASE = "Podstawa wymiaru"
G_MAT = "Urlop macierzyński"
G_SUP = "Uzupełniający urlop macierzyński"
G_PAR = "Urlop rodzicielski"
G_PAT = "Urlop ojcowski"
G_SICK = "Ciąża: zasiłek chorobowy"

RULES: list[dict] = [
    # ======================================================================================
    # Zdarzenie i dziecko
    # ======================================================================================
    V(
        "porod",
        "dziecko.zdarzenie == 'porod'",
        "Zdarzeniem jest poród",
        "UZ art. 29 ust. 1 pkt 1",
        UZ,
        G_EVENT,
    ),
    V(
        "przyjecie",
        "dziecko.zdarzenie in ['przysposobienie', 'rodzina_zastepcza']",
        "Zdarzeniem jest przyjęcie dziecka na wychowanie",
        "UZ art. 29 ust. 1 pkt 2–3",
        UZ,
        G_EVENT,
    ),
    V(
        "data_zdarzenia",
        "dziecko.data",
        "Data zdarzenia (porodu / przewidywanego porodu / przyjęcia)",
        "KP art. 183¹ § 2; UZ art. 29",
        UZ,
        G_EVENT,
    ),
    V(
        "przed_zdarzeniem",
        "data_zdarzenia > dzis()",
        "Zdarzenie jeszcze nie nastąpiło (planowanie)",
        "",
        PR,
        G_EVENT,
    ),
    V(
        "dzieci_zywe",
        "dziecko.liczba_zywych",
        "Liczba dzieci pozostałych przy życiu",
        "KP art. 180¹",
        KP,
        G_EVENT,
    ),
    V(
        "dziecko_zyje",
        "dzieci_zywe > 0",
        "Co najmniej jedno dziecko żyje",
        "KP art. 180¹",
        KP,
        G_EVENT,
    ),
    V(
        "klucz_liczby_dzieci",
        "klucz_dzieci(dziecko.liczba)",
        "Klucz tabel wg liczby dzieci",
        "KP art. 180 § 1",
        KP,
        G_EVENT,
    ),
    V(
        "wiek_przy_zgonie_tyg",
        "dni_miedzy(dziecko.data_porodu, dziecko.data_zgonu) / 7",
        "Wiek dziecka przy zgonie (tygodnie życia)",
        "KP art. 180¹",
        KP,
        G_EVENT,
        condition="jest(dziecko.data_zgonu)",
    ),
    V(
        "zgon_wczesny",
        "dziecko.martwe_urodzenie or wiek_przy_zgonie_tyg < param('stillbirth_child_death_weeks_limit')",
        "Martwe urodzenie albo zgon przed upływem 8 tygodni życia",
        "KP art. 180¹ § 1",
        KP,
        G_EVENT,
    ),
    V(
        "dni_do_zgonu_plus",
        "dni_miedzy(dziecko.data_porodu, dziecko.data_zgonu) + param('child_death_min_days')",
        "Dni od porodu do upływu 7 dni od zgonu",
        "KP art. 180¹ § 1–2",
        KP,
        G_EVENT,
        condition="jest(dziecko.data_zgonu)",
        description="Okres 7 dni liczony łącznie z dniem zgonu.",
    ),
    V(
        "limit_wieku_przyjecia",
        "jesli(dziecko.zdarzenie == 'przysposobienie', tabela('adoption_leave_max_child_age_years', 'adoption'), "
        "jesli(dziecko.odroczony_obowiazek, tabela('adoption_leave_max_child_age_years', 'foster_school_deferred'), "
        "tabela('adoption_leave_max_child_age_years', 'foster')))",
        "Wiek dziecka, do którego przysługuje urlop na warunkach urlopu macierzyńskiego",
        "UZ art. 29 ust. 1 pkt 2–3; KP art. 183 § 1 i § 1¹",
        UZ,
        G_EVENT,
        condition="przyjecie",
    ),
    V(
        "przyjecie_w_limicie",
        "przyjecie and dziecko.wiek_lat < limit_wieku_przyjecia",
        "Dziecko przyjęte przed ukończeniem wymaganego wieku",
        "UZ art. 29 ust. 1 pkt 2–3",
        UZ,
        G_EVENT,
    ),
    V(
        "zdarzenie_uprawnia",
        "porod or przyjecie_w_limicie",
        "Zdarzenie daje prawo do zasiłku macierzyńskiego",
        "UZ art. 29 ust. 1",
        UZ,
        G_EVENT,
    ),
    V(
        "dni_do_limitu_wieku",
        "zaokr((limit_wieku_przyjecia - dziecko.wiek_lat) * 365.25, 0)",
        "Dni do osiągnięcia przez dziecko granicy wieku",
        "KP art. 183 § 1 i § 1¹",
        KP,
        G_EVENT,
        condition="przyjecie_w_limicie",
    ),
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
    # ======================================================================================
    # Uzupełniający urlop macierzyński
    # ======================================================================================
    V(
        "uzup_przypadek",
        "jesli(not dziecko_zyje or not (porod or przyjecie_w_limicie), 0, "
        "jesli(dziecko.tydzien_ciazy < tabela('supplementary_criteria', 'long_gestation_below') or "
        "dziecko.masa_g <= tabela('supplementary_criteria', 'long_weight_max_g'), 1, "
        "jesli(dziecko.tydzien_ciazy < tabela('supplementary_criteria', 'preterm_gestation_below'), 2, "
        "jesli(dziecko.dni_szpitala >= tabela('supplementary_criteria', 'term_min_stay_days') and "
        "dziecko.pierwszy_dzien_szpitala >= tabela('supplementary_criteria', 'term_first_day_from') and "
        "dziecko.pierwszy_dzien_szpitala <= tabela('supplementary_criteria', 'term_first_day_to'), 3, 0))))",
        "Przypadek uzupełniającego urlopu (1: < 28 tyg. lub ≤ 1000 g; 2: 28–36 tyg.; 3: w terminie, szpital od 5.–28. dnia)",
        "KP art. 180² § 1–2, art. 183 § 3¹",
        KP,
        G_SUP,
    ),
    V(
        "uzup_limit_tyg",
        "jesli(uzup_przypadek == 1, tabela('supplementary_maternity_max_weeks', 'long'), "
        "jesli(uzup_przypadek in [2, 3], tabela('supplementary_maternity_max_weeks', 'short'), 0))",
        "Najwięcej tygodni uzupełniającego urlopu",
        "KP art. 180² § 1",
        KP,
        G_SUP,
    ),
    V(
        "uzup_tyg",
        "jesli(dziecko.dni_szpitala > 0, min(uzup_limit_tyg, zaokr_gora(dziecko.dni_szpitala / 7)), 0)",
        "Wymiar uzupełniającego urlopu (tydzień za każdy rozpoczęty tydzień pobytu w szpitalu)",
        "KP art. 180² § 1 i § 3",
        KP,
        G_SUP,
    ),
    V(
        "uzup_bierze",
        "jesli(plan.uzupelniajacy_bierze == 'tata' and tata_uprawniony, 'tata', jesli(mama_uprawniona, 'mama', "
        "jesli(tata_uprawniony, 'tata', None)))",
        "Kto korzysta z uzupełniającego urlopu (tylko jedno z rodziców)",
        "KP art. 180² § 1; RW § 14",
        KP,
        G_SUP,
    ),
    P(
        "okres_uzupelniajacy",
        "uzup_bierze",
        "supplementary",
        "Uzupełniający urlop macierzyński",
        "dodaj_dni(koniec_macierzynskiego, 1)",
        "tygodnie(uzup_tyg)",
        "param('rate_maternity')",
        "KP art. 180²; UZ art. 29a ust. 1, art. 31 ust. 1",
        KP,
        G_SUP,
        condition="plan.uzupelniajacy and jest(uzup_bierze)",
        payer="jesli(uzup_bierze == 'tata', tata_platnik, mama_platnik)",
    ),
    V(
        "koniec_ciaglosci",
        "najpozniej(koniec_macierzynskiego, okres_uzupelniajacy.koniec)",
        "Koniec urlopu macierzyńskiego i uzupełniającego",
        "KP art. 180²",
        KP,
        G_SUP,
    ),
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
    # ======================================================================================
    # Dokumenty
    # ======================================================================================
    M(
        "dokument",
        "d_mac_wniosek_pracodawca",
        "mama.pracownik and mama_uprawniona and porod",
        "Wniosek o urlop",
        "Wniosek o urlop macierzyński u pracodawcy; jeśli zaraz po nim bierzesz urlop rodzicielski, "
        "wystarczy jeden wniosek. Pracodawcy pokazujesz odpis skrócony aktu urodzenia.",
        "Poradnik ZUS 2026 – Jak otrzymać zasiłek; RW § 15",
        PR,
        person="mama",
        benefit="macierzynski_mama",
    ),
    M(
        "dokument",
        "d_mac_przed_porodem",
        "porod and przed_porodem_dni > 0",
        "Zaświadczenie o przewidywanej dacie porodu",
        "Zaświadczenie lekarskie (zwykły druk) określające przewidywaną datę porodu – za okres przed porodem"
        "{jesli(mama.pracownik, '; pracownica dołącza kopię do wniosku o część urlopu przed porodem', '')}.",
        "RZ § 13 ust. 1 pkt 1; RW § 2; UZ art. 53 ust. 2",
        RZ,
        person="mama",
        benefit="macierzynski_mama",
    ),
    M(
        "dokument",
        "d_mac_zus",
        "mama_uprawniona and mama_platnik == 'zus'",
        "Wniosek do ZUS",
        "{jesli(mama_samoplatnik, 'Wniosek o zasiłek macierzyński na druku ZAM albo zaświadczenie płatnika składek na druku Z-3b – najwygodniej przez eZUS.', 'Wniosek o zasiłek macierzyński (dane z załącznika nr 6 do rozporządzenia) albo zaświadczenie płatnika składek – płatnik przekazuje je do ZUS w ciągu 7 dni.')}",
        "RZ § 3, § 12, zał. 6; UZ art. 61b ust. 5; Poradnik ZUS 2026",
        RZ,
        person="mama",
        benefit="macierzynski_mama",
    ),
    M(
        "dokument",
        "d_mac_odpis_zus",
        "porod and dziecko.urodzone and mama_uprawniona and mama_platnik == 'zus' and not dziecko.martwe_urodzenie",
        "Odpis aktu urodzenia",
        "Gdy płatnikiem jest ZUS, nie przedstawiasz odpisu skróconego aktu urodzenia – podajesz imię, nazwisko, "
        "PESEL, datę i miejsce urodzenia dziecka, a ZUS pobierze odpis z rejestru stanu cywilnego.",
        "RZ § 13 ust. 2–4",
        RZ,
        person="mama",
        benefit="macierzynski_mama",
    ),
    M(
        "dokument",
        "d_mac_martwe",
        "porod and dziecko.martwe_urodzenie",
        "Dokument o martwym urodzeniu",
        "Odpis skrócony aktu urodzenia z adnotacją o martwym urodzeniu, a gdy aktu nie sporządzono – "
        "zaświadczenie lekarza specjalisty położnictwa i ginekologii (lub w trakcie specjalizacji) albo położnej o martwym urodzeniu, "
        "bez względu na czas trwania ciąży.",
        "RZ § 13 ust. 1 pkt 2",
        RZ,
        person="mama",
        benefit="macierzynski_mama",
    ),
    M(
        "dokument",
        "d_mac_po_ustaniu",
        "mama_po_ustaniu",
        "Dokumenty – poród po ustaniu ubezpieczenia",
        "Zaświadczenie lekarskie o ciąży w okresie zatrudnienia; {jesli(mama.przyczyna_ustania == 'naruszenie_prawa', 'prawomocne orzeczenie sądu o rozwiązaniu umowy z naruszeniem prawa', 'świadectwo pracy lub inny dokument potwierdzający śmierć, upadłość lub likwidację pracodawcy')}.",
        "RZ § 15",
        RZ,
        person="mama",
        benefit="macierzynski_mama",
    ),
    M(
        "dokument",
        "d_wys_mac",
        "zasilek_wys_mac",
        "Dokumenty – zasiłek w wysokości zasiłku macierzyńskiego",
        "Zaświadczenie lekarskie o ciąży w okresie zatrudnienia, świadectwo pracy (lub inny dokument o upadłości, likwidacji, śmierci "
        "pracodawcy) i oświadczenie, że nie zapewniono innego zatrudnienia.",
        "RZ § 17",
        RZ,
        person="mama",
        benefit="zasilek_w_wysokosci_macierzynskiego",
    ),
    M(
        "dokument",
        "d_przysposobienie",
        "dziecko.zdarzenie == 'przysposobienie' and (mama_uprawniona or tata_uprawniony)",
        "Dokumenty – przysposobienie",
        "Oświadczenie o dacie przyjęcia dziecka na wychowanie oraz zaświadczenie sądu opiekuńczego o dacie "
        "wystąpienia o przysposobienie (z datą urodzenia dziecka) albo kopia wniosku z poświadczeniem sądu.",
        "RZ § 16 ust. 1; RW § 18",
        RZ,
        benefit="macierzynski_mama",
    ),
    M(
        "dokument",
        "d_rodzina_zastepcza",
        "dziecko.zdarzenie == 'rodzina_zastepcza' and (mama_uprawniona or tata_uprawniony)",
        "Dokumenty – rodzina zastępcza",
        "Orzeczenie sądu o umieszczeniu dziecka w rodzinie zastępczej (albo umowa ze starostą), dokument "
        "potwierdzający wiek dziecka{jesli(dziecko.odroczony_obowiazek, ' i kopia decyzji o odroczeniu obowiązku szkolnego', '')}.",
        "RZ § 16 ust. 2; RW § 18",
        RZ,
        benefit="macierzynski_mama",
    ),
    M(
        "dokument",
        "d_tata_przejecie",
        "dla_taty_dni > 0",
        "Dokumenty – tata przejmuje część urlopu",
        "Mama: oświadczenie, od kiedy tata korzysta z zasiłku{jesli(mama.pracownik, ' i wniosek o rezygnację z reszty urlopu (z kopią wniosku taty)', ', wniosek z datą rezygnacji')}. "
        "Tata: odpis aktu urodzenia i zaświadczenie płatnika o okresie i stawce zasiłku mamy{jesli(tata.pracownik, '; u pracodawcy wniosek o pozostałą część urlopu z oświadczeniem mamy', '')}.",
        "RZ § 18, § 20 ust. 1; RW § 3, § 5",
        RZ,
        person="tata",
        benefit="macierzynski_tata",
    ),
    M(
        "dokument",
        "d_szpital_matki",
        "szpital_matki",
        "Dokumenty – pobyt mamy w szpitalu",
        "Zaświadczenia placówki o dacie przyjęcia i wypisu mamy, oświadczenie mamy o przerwaniu zasiłku, zaświadczenie płatnika o "
        "zasiłku mamy i odpis aktu urodzenia.",
        "RZ § 23–24; RW § 6–7",
        RZ,
        person="tata",
        benefit="macierzynski_tata",
    ),
    M(
        "dokument",
        "d_zgon_porzucenie",
        "zgon_porzucenie_matki and tata_uprawniony",
        "Dokumenty – zgon matki / porzucenie dziecka",
        "Odpis aktu urodzenia, oświadczenie o dniu zgonu matki albo porzuceniu dziecka{jesli(mama_uprawniona, ' i zaświadczenie płatnika o okresie zasiłku mamy', '')}.",
        "RZ § 20 ust. 3–4; RW § 8–11",
        RZ,
        person="tata",
        benefit="macierzynski_tata",
    ),
    M(
        "dokument",
        "d_niezdolnosc",
        "sytuacja_matki.rodzaj == 'niezdolnosc' and tata_uprawniony",
        "Dokumenty – niezdolność matki do samodzielnej egzystencji",
        "Orzeczenie o niezdolności matki do samodzielnej egzystencji oraz dokumenty jak przy przejęciu urlopu (odpis aktu urodzenia, zaświadczenie płatnika).",
        "RZ § 21–22; RW § 4, § 12",
        RZ,
        person="tata",
        benefit="macierzynski_tata",
    ),
    M(
        "dokument",
        "d_zatrudnienie_matki",
        "sytuacja_matki.rodzaj == 'zatrudnienie' and tata_uprawniony",
        "Dokumenty – matka podjęła pracę",
        "Odpis aktu urodzenia, oświadczenie matki o dacie podjęcia zatrudnienia (co najmniej pół etatu) i oświadczenie taty o dacie, od której pobiera zasiłek.",
        "RZ § 25; RW § 13",
        RZ,
        person="tata",
        benefit="macierzynski_tata",
    ),
    M(
        "dokument",
        "d_uzupelniajacy",
        "uzup_tyg > 0 and plan.uzupelniajacy and jest(uzup_bierze)",
        "Dokumenty – urlop uzupełniający",
        "Zaświadczenie szpitala o okresie pobytu dziecka i tygodniu ciąży / masie urodzeniowej oraz oświadczenie, że drugi rodzic nie "
        "skorzysta z uzupełniającego urlopu (zasiłku).",
        "KP art. 180² § 5; RW § 14; RZ § 26–27",
        KP,
        person="uzup_bierze",
        benefit="uzupelniajacy",
    ),
    *[
        M(
            "dokument",
            f"d_rodzicielski_{p}",
            f"{p}_rodzicielski_dni > 0",
            "Dokumenty – urlop rodzicielski",
            f"{{jesli({p}.pracownik, 'Wniosek do pracodawcy z okresem urlopu i liczbą wykorzystanych części, odpis aktu urodzenia, oświadczenie o planach drugiego rodzica', 'Wniosek do płatnika zasiłku przed rozpoczęciem korzystania z zasiłku, oświadczenie o planach drugiego rodzica')}}"
            "{jesli(dziecko.za_zyciem, ' oraz kopia zaświadczenia „Za życiem”', '')}"
            + (
                "{jesli(not mama_uprawniona, '; oświadczenie, że matka nie ma tytułu do ubezpieczenia chorobowego', '')}"
                if p == "tata"
                else ""
            )
            + ".",
            "RW § 15; RZ § 29–30" + ("; RZ § 32" if p == "tata" else ""),
            RW,
            person=p,
            benefit=f"rodzicielski_{p}",
        )
        for p in PARENTS
    ],
    *[
        M(
            "dokument",
            f"d_praca_{p}",
            f"{p}_praca > 0 and {p}_rodzicielski_dni > 0",
            "Wniosek o łączenie urlopu z pracą",
            "Wniosek o łączenie urlopu rodzicielskiego z pracą (wymiar czasu pracy, okres, sposób wykorzystania wydłużenia)"
            f"{{jesli({p}_platnik == 'zus', '; pracodawca wystawia zaświadczenie o wymiarze pracy dla ZUS', '')}}.",
            "RW § 16; RZ § 29 pkt 2",
            RW,
            person=p,
            benefit=f"rodzicielski_{p}",
        )
        for p in PARENTS
    ],
    M(
        "dokument",
        "d_ojcowski",
        "ojcowski_mozliwy",
        "Dokumenty – urlop ojcowski",
        "{jesli(tata.pracownik, 'Wniosek do pracodawcy z okresem urlopu', 'Wniosek o zasiłek przed rozpoczęciem korzystania, z datą początku')}, "
        "odpis aktu urodzenia{jesli(dziecko.zdarzenie == 'przysposobienie', ' albo postanowienie sądu o przysposobieniu', '')} i oświadczenie, czy korzystałeś z urlopu (zasiłku) ojcowskiego.",
        "RW § 17; RZ § 33",
        RW,
        person="tata",
        benefit="ojcowski",
    ),
    M(
        "dokument",
        "d_za_zyciem",
        "dziecko.za_zyciem and (mama_uprawniona or tata_uprawniony)",
        "Oświadczenie „Za życiem”",
        "Do wniosku o zasiłek dołączasz oświadczenie, że dziecko ma zaświadczenie „Za życiem”.",
        "UZ art. 61b ust. 4a",
        UZ,
        benefit="rodzicielski_mama",
    ),
    M(
        "dokument",
        "d_chorobowy",
        "zwolnienie_b_dni > 0 and mama_chorobowe_prawo",
        "Zwolnienie e-ZLA z kodem B",
        "Zwolnienie wystawia lekarz elektronicznie (e-ZLA) – trafia do ZUS i płatnika. {jesli(mama_samoplatnik, 'Prowadząc działalność składasz do ZUS zaświadczenie płatnika składek na druku Z-3b (eZUS).', jesli(mama_platnik == 'zus', 'Płatnik przekazuje do ZUS zaświadczenie płatnika składek.', ''))}",
        "UZ art. 55, 61b ust. 2; RZ § 3; Poradnik ZUS 2026",
        UZ,
        person="mama",
        benefit="zasilek_chorobowy_ciaza",
    ),
    M(
        "dokument",
        "d_podwyzszenie",
        "jest(param('parental_benefit_amount'))",
        "Podwyższenie zasiłku",
        "Oświadczenie, czy zasiłek macierzyński przysługuje z więcej niż jednego tytułu i który płatnik wypłaci podwyższenie.",
        "RZ § 28; UZ art. 62 ust. 4–6",
        RZ,
        benefit="macierzynski_mama",
    ),
    # ======================================================================================
    # Terminy
    # ======================================================================================
    M(
        "termin",
        "t_usredniona",
        "mama_uprawniona and dziecko_zyje and brak(plan.wniosek_usredniony_zlozony)",
        "Wniosek o stawkę uśrednioną 81,5%",
        "Wniosek o zasiłek za pełny urlop macierzyński i rodzicielski w stawce 81,5% – najpóźniej {param('averaged_application_deadline_days')} dni po {jesli(porod, 'porodzie', 'przyjęciu dziecka')}.",
        "UZ art. 30a ust. 1–2",
        UZ,
        person="mama",
        benefit="macierzynski_mama",
        date="dodaj_dni(data_zdarzenia, param('averaged_application_deadline_days'))",
        deadline_kind="apply",
    ),
    M(
        "termin",
        "t_mac_przed",
        "mama.pracownik and przed_porodem_dni > 0",
        "Wniosek o urlop macierzyński przed porodem",
        "Wniosek z kopią zaświadczenia o przewidywanej dacie porodu – najpóźniej {tabela('application_lead_days', 'maternity_before_birth')} dni przed rozpoczęciem urlopu.",
        "KP art. 177 § 1¹ pkt 1; RW § 2; Poradnik ZUS 2026",
        KP,
        person="mama",
        benefit="macierzynski_mama",
        date="dodaj_dni(mama_macierzynski_przed.start, -tabela('application_lead_days', 'maternity_before_birth'))",
        deadline_kind="apply",
    ),
    M(
        "termin",
        "t_rezygnacja",
        "mama.pracownik and dla_taty_dni > 0",
        "Wniosek mamy o rezygnację z części urlopu",
        "Najpóźniej {tabela('application_lead_days', 'mother_resignation')} dni przed powrotem do pracy.",
        "KP art. 180 § 8",
        KP,
        person="mama",
        benefit="macierzynski_tata",
        date="dodaj_dni(tata_macierzynski.start, -tabela('application_lead_days', 'mother_resignation'))",
        deadline_kind="apply",
    ),
    M(
        "termin",
        "t_tata_macierzynski",
        "tata.pracownik and tata_przejecie_dni > 0 and mama_uprawniona and not zgon_porzucenie_matki",
        "Wniosek taty o część urlopu macierzyńskiego",
        "Najpóźniej {tabela('application_lead_days', 'father_maternity_part')} dni przed rozpoczęciem.",
        "KP art. 180 § 9",
        KP,
        person="tata",
        benefit="macierzynski_tata",
        date="dodaj_dni(tata_macierzynski.start, -tabela('application_lead_days', 'father_maternity_part'))",
        deadline_kind="apply",
    ),
    M(
        "termin",
        "t_uzupelniajacy",
        "okres_uzupelniajacy.aktywny",
        "Wniosek o uzupełniający urlop macierzyński",
        "{jesli(jesli(uzup_bierze == 'tata', tata.pracownik, mama.pracownik), 'Najpóźniej ' + tabela('application_lead_days', 'supplementary') + ' dni przed końcem urlopu macierzyńskiego.', 'Przed końcem pobierania zasiłku za urlop macierzyński.')}",
        "KP art. 180² § 4; RZ § 26 pkt 3",
        KP,
        person="uzup_bierze",
        benefit="uzupelniajacy",
        date="jesli(jesli(uzup_bierze == 'tata', tata.pracownik, mama.pracownik), dodaj_dni(koniec_macierzynskiego, -tabela('application_lead_days', 'supplementary')), koniec_macierzynskiego)",
        deadline_kind="apply",
    ),
    M(
        "termin",
        "t_rodzicielski_mama",
        "mama_rodzicielski.aktywny",
        "Wniosek o urlop rodzicielski",
        "{jesli(mama.pracownik, 'Najpóźniej ' + tabela('application_lead_days', 'parental') + ' dni przed rozpoczęciem (wystarczy jeden wniosek o urlop macierzyński i rodzicielski).', 'Przed rozpoczęciem korzystania z zasiłku.')}",
        "KP art. 182¹ᵈ § 1; RZ § 29 pkt 3",
        KP,
        person="mama",
        benefit="rodzicielski_mama",
        date="jesli(mama.pracownik, dodaj_dni(mama_rodzicielski.start, -tabela('application_lead_days', 'parental')), mama_rodzicielski.start)",
        deadline_kind="apply",
    ),
    M(
        "termin",
        "t_rodzicielski_tata",
        "tata_rodzicielski_wylaczny.aktywny or tata_rodzicielski_wspolny.aktywny",
        "Wniosek o urlop rodzicielski",
        "{jesli(tata.pracownik, 'Najpóźniej ' + tabela('application_lead_days', 'parental') + ' dni przed rozpoczęciem.', 'Przed rozpoczęciem korzystania z zasiłku.')}",
        "KP art. 182¹ᵈ § 1; RZ § 30 pkt 4",
        KP,
        person="tata",
        benefit="rodzicielski_tata",
        date="jesli(tata.pracownik, dodaj_dni(start_rodzicielski_taty, -tabela('application_lead_days', 'parental')), start_rodzicielski_taty)",
        deadline_kind="apply",
    ),
    *[
        M(
            "termin",
            f"t_praca_{p}",
            f"{p}_praca > 0 and {p}_rodzicielski_dni > 0",
            "Wniosek o łączenie urlopu z pracą",
            "Najpóźniej {tabela('application_lead_days', 'work_combination')} dni przed rozpoczęciem pracy.",
            "KP art. 182¹ᵉ § 2",
            KP,
            person=p,
            benefit=f"rodzicielski_{p}",
            date=f"dodaj_dni({'mama_rodzicielski.start' if p == 'mama' else 'start_rodzicielski_taty'}, -tabela('application_lead_days', 'work_combination'))",
            deadline_kind="apply",
        )
        for p in PARENTS
    ],
    M(
        "termin",
        "t_ojcowski",
        "tata_ojcowski.aktywny",
        "Wniosek o urlop ojcowski",
        "{jesli(tata.pracownik, 'Najpóźniej ' + tabela('application_lead_days', 'paternity') + ' dni przed rozpoczęciem.', 'Przed rozpoczęciem korzystania z zasiłku.')}",
        "KP art. 182³ § 2; RZ § 33 pkt 3",
        KP,
        person="tata",
        benefit="ojcowski",
        date="jesli(tata.pracownik, dodaj_dni(tata_ojcowski.start, -tabela('application_lead_days', 'paternity')), tata_ojcowski.start)",
        deadline_kind="apply",
    ),
    M(
        "termin",
        "t_ojcowski_do",
        "ojcowski_mozliwy",
        "Ostatni dzień urlopu ojcowskiego",
        "Po tym dniu prawo do urlopu (zasiłku) ojcowskiego wygasa.",
        "KP art. 182³ § 1",
        KP,
        person="tata",
        benefit="ojcowski",
        date="ojcowski_termin",
        deadline_kind="use_by",
    ),
    M(
        "termin",
        "t_rodzicielski_do",
        "wymiar_rodzicielski_tyg > 0 and (mama_uprawniona or tata_uprawniony)",
        "Ostatni dzień na urlop rodzicielski",
        "Urlop rodzicielski (wszystkie części) trzeba wykorzystać do tego dnia.",
        "KP art. 182¹ᶜ, art. 183 § 4¹",
        KP,
        benefit="rodzicielski_mama",
        date="rodzicielski_termin",
        deadline_kind="use_by",
    ),
    M(
        "termin",
        "t_na_warunkach",
        "przyjecie_w_limicie and (mama.pracownik or tata.pracownik)",
        "Wniosek o urlop na warunkach urlopu macierzyńskiego",
        "W ciągu {tabela('application_lead_days', 'taken_in_application')} dni od przyjęcia dziecka; urlop zaczyna się najpóźniej "
        "{tabela('application_lead_days', 'taken_in_start_max')} dni od przyjęcia.",
        "KP art. 183 § 6; RW § 18",
        KP,
        benefit="macierzynski_mama",
        date="dodaj_dni(data_zdarzenia, tabela('application_lead_days', 'taken_in_application'))",
        deadline_kind="apply",
    ),
    *[
        M(
            "termin",
            f"t_dlug_{p}",
            f"{p}_dlug_do_splaty",
            "Spłata zadłużenia składkowego",
            "Spłać całe zadłużenie najpóźniej do tego dnia – inaczej prawo do zasiłków się przedawni. Zasiłek wypłaca się "
            "najpóźniej {param('debt_payment_days_after_repayment')} dni po spłacie.",
            "UZ art. 2a, art. 64 ust. 3",
            UZ,
            person=p,
            date="dodaj_mies(data_zdarzenia, param('debt_repayment_window_months'))",
            deadline_kind="apply",
        )
        for p in PARENTS
    ],
    M(
        "termin",
        "t_przedawnienie",
        "jest(koniec_ostatniego_okresu)",
        "Przedawnienie roszczenia o zasiłek",
        "Roszczenie o wypłatę zasiłku przedawnia się po {param('claim_limitation_months')} miesiącach od ostatniego dnia okresu, "
        "za który przysługuje (3 lata, gdy wypłaty nie było z winy płatnika lub ZUS).",
        "UZ art. 67",
        UZ,
        date="dodaj_mies(koniec_ostatniego_okresu, param('claim_limitation_months'))",
        deadline_kind="use_by",
        order=99,
    ),
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
    # ======================================================================================
    # Informacje i założenia obliczeń
    # ======================================================================================
    M(
        "informacja",
        "i_wyplata",
        "mama_uprawniona or tata_uprawniony",
        "Termin wypłaty",
        "Płatnik składek wypłaca zasiłek w terminie wypłaty wynagrodzeń, ZUS – na bieżąco, najpóźniej "
        "{param('payment_deadline_days')} dni od wyjaśnienia ostatniej okoliczności.",
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


def all_rules() -> list[dict]:
    """Rules with defaults filled in (order inside a kind follows the list)."""
    out = []
    for i, r in enumerate(RULES):
        out.append({"order": r.get("order") or i, **{k: v for k, v in r.items() if k != "order"}})
    return out
