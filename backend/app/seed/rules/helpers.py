"""Shared pieces of the rule seed: constructors V/P/B/M, source codes, late-advice templates.

Rules of the guide – written only from the six source documents (see parameters_2026.py).

Each rule is data: expressions in the rule language (app/engine/expressions.py) that read
facts (app/engine/facts.py), parameters (param / tabela) and other rules by their code.
The seed loads them into the `rule` table; afterwards they are edited in the admin panel.
Source codes in `source`: KP, UZ, RZ, RW, PR, ZAL; SR = ustawa o świadczeniach rodzinnych (becikowe), spoza sześciu źródeł.
"""

from __future__ import annotations

KP, UZ, RZ, RW, PR, ZAL, SR = "KP", "UZ", "RZ", "RW", "PR", "ZAL", "SR"
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
    "t_ojcowski": "{jesli(ojcowski_termin < dzis(), 'Czas na wykorzystanie urlopu ojcowskiego minął ' + ojcowski_termin + "
    "' – niewykorzystana część przepada.', jesli(tata.pracownik, 'Wskaż późniejszy początek urlopu (najwcześniej ' + "
    "dodaj_dni(dzis(), tabela('application_lead_days', 'paternity')) + '). Urlop ojcowski musi się skończyć najpóźniej ' + "
    "ojcowski_termin + '.', 'Złóż wniosek do ZUS jak najszybciej. Urlop ojcowski musi się skończyć najpóźniej ' + "
    "ojcowski_termin + '.'))}",
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
