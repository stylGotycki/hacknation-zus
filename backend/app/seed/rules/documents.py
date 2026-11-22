"""Rules: Dokumenty."""

from __future__ import annotations

from app.seed.rules.helpers import (
    KP,
    PARENTS,
    PR,
    RW,
    RZ,
    SR,
    UZ,
    M,
)

RULES: list[dict] = [
    # ======================================================================================
    # Dokumenty
    # ======================================================================================
    M(
        "dokument",
        "d_becikowe",
        "porod and not dziecko.martwe_urodzenie",
        "Becikowe – dokumenty do gminy",
        "Wniosek o jednorazową zapomogę, zaświadczenie lekarza lub położnej o opiece medycznej od 10. tygodnia ciąży do porodu, "
        "odpis skrócony aktu urodzenia dziecka oraz oświadczenie, że na dziecko nie pobrano już becikowego (np. przez drugiego rodzica).",
        "Ustawa o świadczeniach rodzinnych art. 15b; gov.pl – Uzyskaj becikowe",
        SR,
        benefit="becikowe",
    ),
    M(
        "termin",
        "t_becikowe",
        "porod and not dziecko.martwe_urodzenie",
        "Wniosek o becikowe",
        "Wniosek do gminy w ciągu {param('birth_grant_months')} miesięcy od urodzenia dziecka.",
        "Ustawa o świadczeniach rodzinnych art. 15b; gov.pl – Uzyskaj becikowe",
        SR,
        benefit="becikowe",
        date="dodaj_mies(data_zdarzenia, param('birth_grant_months'))",
        deadline_kind="apply",
        late="Wniosek złożony po terminie gmina pozostawia bez rozpoznania – becikowe przepadło.",
    ),
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
]
