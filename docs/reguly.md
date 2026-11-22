# Katalog reguł (seed)

194 reguł ze źródeł: KP – Kodeks pracy, UZ – Ustawa zasiłkowa, RZ – Rozp. – dokumenty, RW – Rozp. – wnioski, PR – Poradnik ZUS 2026, ZAL – Załącznik.
Plik generowany: `python scripts/gen_rules_doc.py`. Aktualne reguły (po zmianach w panelu) są w bazie.

## Zdarzenie i dziecko

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `porod` | Wartość | Zdarzeniem jest poród | `dziecko.zdarzenie == 'porod'` | UZ: UZ art. 29 ust. 1 pkt 1 |
| `przyjecie` | Wartość | Zdarzeniem jest przyjęcie dziecka na wychowanie | `dziecko.zdarzenie in ['przysposobienie', 'rodzina_zastepcza']` | UZ: UZ art. 29 ust. 1 pkt 2–3 |
| `data_zdarzenia` | Wartość | Data zdarzenia (porodu / przewidywanego porodu / przyjęcia) | `dziecko.data` | UZ: KP art. 183¹ § 2; UZ art. 29 |
| `przed_zdarzeniem` | Wartość | Zdarzenie jeszcze nie nastąpiło (planowanie) | `data_zdarzenia > dzis()` | PR:  |
| `dzieci_zywe` | Wartość | Liczba dzieci pozostałych przy życiu | `dziecko.liczba_zywych` | KP: KP art. 180¹ |
| `dziecko_zyje` | Wartość | Co najmniej jedno dziecko żyje | `dzieci_zywe > 0` | KP: KP art. 180¹ |
| `klucz_liczby_dzieci` | Wartość | Klucz tabel wg liczby dzieci | `klucz_dzieci(dziecko.liczba)` | KP: KP art. 180 § 1 |
| `wiek_przy_zgonie_tyg` | Wartość | Wiek dziecka przy zgonie (tygodnie życia) | `dni_miedzy(dziecko.data_porodu, dziecko.data_zgonu) / 7 **gdy** jest(dziecko.data_zgonu)` | KP: KP art. 180¹ |
| `zgon_wczesny` | Wartość | Martwe urodzenie albo zgon przed upływem 8 tygodni życia | `dziecko.martwe_urodzenie or wiek_przy_zgonie_tyg < param('stillbirth_child_death_weeks_limit')` | KP: KP art. 180¹ § 1 |
| `dni_do_zgonu_plus` | Wartość | Dni od porodu do upływu 7 dni od zgonu | `dni_miedzy(dziecko.data_porodu, dziecko.data_zgonu) + param('child_death_min_days') **gdy** jest(dziecko.data_zgonu)` | KP: KP art. 180¹ § 1–2 |
| `limit_wieku_przyjecia` | Wartość | Wiek dziecka, do którego przysługuje urlop na warunkach urlopu macierzyńskiego | `jesli(dziecko.zdarzenie == 'przysposobienie', tabela('adoption_leave_max_child_age_years', 'adoption'), jesli(dziecko.odroczony_obowiazek, tabela('adoption_leave_max_child_age_years', 'foster_school_deferred'), tabela('adoption_leave_max_child_age_years', 'foster'))) **gdy** przyjecie` | UZ: UZ art. 29 ust. 1 pkt 2–3; KP art. 183 § 1 i § 1¹ |
| `przyjecie_w_limicie` | Wartość | Dziecko przyjęte przed ukończeniem wymaganego wieku | `przyjecie and dziecko.wiek_lat < limit_wieku_przyjecia` | UZ: UZ art. 29 ust. 1 pkt 2–3 |
| `zdarzenie_uprawnia` | Wartość | Zdarzenie daje prawo do zasiłku macierzyńskiego | `porod or przyjecie_w_limicie` | UZ: UZ art. 29 ust. 1 |
| `dni_do_limitu_wieku` | Wartość | Dni do osiągnięcia przez dziecko granicy wieku | `zaokr((limit_wieku_przyjecia - dziecko.wiek_lat) * 365.25, 0) **gdy** przyjecie_w_limicie` | KP: KP art. 183 § 1 i § 1¹ |

## Prawo do zasiłku

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `mama_samoplatnik` | Wartość | Sam opłaca składki (mamy) | `mama.zatrudnienie in ['dzialalnosc', 'wspolpracujaca']` | UZ: UZ art. 2a ust. 1 |
| `mama_dlug_ponad_prog` | Wartość | Zadłużenie składkowe ponad 1% minimalnego wynagrodzenia (mamy) | `mama_samoplatnik and mama.dlug > param('contribution_debt_threshold_ratio') * param('minimum_wage')` | UZ: UZ art. 2a ust. 1 |
| `mama_dlug_przedawnia` | Wartość | Zadłużenie niespłacone w 6 miesięcy – prawo przedawnione (mamy) | `mama_dlug_ponad_prog and (jesli(jest(mama.dlug_splacony), mama.dlug_splacony, dzis()) > dodaj_mies(data_zdarzenia, param('debt_repayment_window_months')))` | UZ: UZ art. 2a ust. 2 |
| `mama_dlug_do_splaty` | Wartość | Zasiłek po spłacie całego zadłużenia (mamy) | `mama_dlug_ponad_prog and not mama_dlug_przedawnia and brak(mama.dlug_splacony)` | UZ: UZ art. 2a ust. 1, art. 64 ust. 3 |
| `mama_ubezpieczony` | Wartość | Ubezpieczenie chorobowe albo urlop wychowawczy w dniu porodu / przyjęcia (mamy) | `mama.obecny and (mama.ubezpieczony_w_dniu_zdarzenia or mama.urlop_wychowawczy)` | UZ: UZ art. 29 ust. 1–2 |
| `mama_platnik` | Wartość | Kto ustala i wypłaca zasiłki (mamy) | `jesli(mama_samoplatnik or (mama.liczba_ubezpieczonych <= param('payer_threshold_insured')) or mama_po_ustaniu, 'zus', jesli(brak(mama.liczba_ubezpieczonych), 'nieznany', 'pracodawca'))` | UZ: UZ art. 61 ust. 1–2 |
| `tata_samoplatnik` | Wartość | Sam opłaca składki (taty) | `tata.zatrudnienie in ['dzialalnosc', 'wspolpracujaca']` | UZ: UZ art. 2a ust. 1 |
| `tata_dlug_ponad_prog` | Wartość | Zadłużenie składkowe ponad 1% minimalnego wynagrodzenia (taty) | `tata_samoplatnik and tata.dlug > param('contribution_debt_threshold_ratio') * param('minimum_wage')` | UZ: UZ art. 2a ust. 1 |
| `tata_dlug_przedawnia` | Wartość | Zadłużenie niespłacone w 6 miesięcy – prawo przedawnione (taty) | `tata_dlug_ponad_prog and (jesli(jest(tata.dlug_splacony), tata.dlug_splacony, dzis()) > dodaj_mies(data_zdarzenia, param('debt_repayment_window_months')))` | UZ: UZ art. 2a ust. 2 |
| `tata_dlug_do_splaty` | Wartość | Zasiłek po spłacie całego zadłużenia (taty) | `tata_dlug_ponad_prog and not tata_dlug_przedawnia and brak(tata.dlug_splacony)` | UZ: UZ art. 2a ust. 1, art. 64 ust. 3 |
| `tata_ubezpieczony` | Wartość | Ubezpieczenie chorobowe albo urlop wychowawczy w dniu porodu / przyjęcia (taty) | `tata.obecny and (tata.ubezpieczony_w_dniu_zdarzenia or tata.urlop_wychowawczy)` | UZ: UZ art. 29 ust. 1–2 |
| `tata_platnik` | Wartość | Kto ustala i wypłaca zasiłki (taty) | `jesli(tata_samoplatnik or (tata.liczba_ubezpieczonych <= param('payer_threshold_insured')), 'zus', jesli(brak(tata.liczba_ubezpieczonych), 'nieznany', 'pracodawca'))` | UZ: UZ art. 61 ust. 1–2 |
| `mama_po_ustaniu` | Wartość | Prawo do zasiłku macierzyńskiego po ustaniu ubezpieczenia (ustało w ciąży) | `porod and mama.obecny and not mama_ubezpieczony and (mama.przyczyna_ustania in ['upadlosc_likwidacja_smierc', 'naruszenie_prawa'] or mama.umowa_przedluzona_do_porodu)` | UZ: UZ art. 30 ust. 1 i 4 |
| `mama_uprawniona` | Wartość | Mama ma prawo do zasiłku macierzyńskiego | `zdarzenie_uprawnia and (mama_ubezpieczony or mama_po_ustaniu) and not mama_dlug_przedawnia` | UZ: UZ art. 29 ust. 1, art. 30, art. 2a |
| `tata_uprawniony` | Wartość | Tata ma prawo do zasiłku macierzyńskiego (własny tytuł) | `zdarzenie_uprawnia and tata_ubezpieczony and not tata_dlug_przedawnia` | UZ: UZ art. 29 ust. 2–10, art. 2a |

## Podstawa wymiaru

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `mama_podstawa` | Wartość | Podstawa wymiaru zasiłku (mamy) | `zaokr(jesli(mama.pracownik, max(mama.podstawa_brutto * (1 - param('social_contribution_deduction')), jesli(mama.wymiar_etatu >= 1, param('minimum_wage') * (1 - param('social_contribution_deduction')), 0)), min(mama.podstawa_brutto, param('voluntary_sickness_base_max')) * (1 - param('social_contribution_deduction'))), 2) **gdy** jest(mama.podstawa_brutto)` | UZ: UZ art. 36, 45, 47, 48, 52; ZAL |
| `tata_podstawa` | Wartość | Podstawa wymiaru zasiłku (taty) | `zaokr(jesli(tata.pracownik, max(tata.podstawa_brutto * (1 - param('social_contribution_deduction')), jesli(tata.wymiar_etatu >= 1, param('minimum_wage') * (1 - param('social_contribution_deduction')), 0)), min(tata.podstawa_brutto, param('voluntary_sickness_base_max')) * (1 - param('social_contribution_deduction'))), 2) **gdy** jest(tata.podstawa_brutto)` | UZ: UZ art. 36, 45, 47, 48, 52; ZAL |

## Urlop rodzicielski

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `mama_praca` | Wartość | Część etatu wykonywana w czasie urlopu rodzicielskiego (mamy) | `jesli(mama.pracownik, mama.praca_w_rodzicielskim, 0)` | KP: KP art. 182¹ᵉ § 1 |
| `tata_praca` | Wartość | Część etatu wykonywana w czasie urlopu rodzicielskiego (taty) | `jesli(tata.pracownik, tata.praca_w_rodzicielskim, 0)` | KP: KP art. 182¹ᵉ § 1 |
| `klucz_rodzicielski` | Wartość | Klucz wymiaru urlopu rodzicielskiego | `jesli(dziecko.za_zyciem, 'za_zyciem_', '') + jesli(jesli(porod, dzieci_zywe, dziecko.liczba) > 1, 'multiple', 'single')` | KP: KP art. 182¹ᵃ § 1–2 |
| `wymiar_rodzicielski_tyg` | Wartość | Wymiar urlopu rodzicielskiego dla obojga rodziców (tygodnie) | `jesli(not dziecko_zyje or not zdarzenie_uprawnia, 0, jesli(przyjecie_okres_minimalny, tabela('parental_leave_weeks', jesli(dziecko.za_zyciem, 'za_zyciem_taken_in_short', 'taken_in_short')), tabela('parental_leave_weeks', klucz_rodzicielski)))` | KP: KP art. 182¹ᵃ § 1–3, art. 183 § 4–4⁵ |
| `wylaczna_czesc_tyg` | Wartość | Nieprzenoszalna część każdego rodzica (tygodnie) | `param('parental_non_transferable_weeks')` | KP: KP art. 182¹ᵃ § 4 |
| `oboje_rodzicielski` | Wartość | Oboje rodzice mają prawo do urlopu (zasiłku) rodzicielskiego | `mama_uprawniona and tata_uprawniony and dziecko_zyje and not zgon_porzucenie_matki` | KP: KP art. 182¹ᵃ § 3–4; UZ art. 29a ust. 3 |
| `tata_rodzicielski_tyg` | Wartość | Urlop rodzicielski taty (tygodnie) | `jesli(not tata_uprawniony or not dziecko_zyje, 0, jesli(oboje_rodzicielski, jesli(jest(plan.rodzicielski_tata_tyg), plan.rodzicielski_tata_tyg, wylaczna_czesc_tyg), jesli(mama_uprawniona and not zgon_porzucenie_matki, 0, wymiar_rodzicielski_tyg)))` | KP: KP art. 182¹ᵃ § 3–4; UZ art. 31 ust. 3h |
| `mama_rodzicielski_tyg` | Wartość | Urlop rodzicielski mamy (tygodnie) | `jesli(not mama_uprawniona or not dziecko_zyje or zgon_porzucenie_matki, 0, wymiar_rodzicielski_tyg - tata_rodzicielski_tyg)` | KP: KP art. 182¹ᵃ § 3 |
| `limit_z_praca_tyg` | Wartość | Najdłuższy urlop rodzicielski łączony z pracą (tygodnie) | `tabela('parental_with_work_max_weeks', jesli(dziecko.za_zyciem, 'za_zyciem_', '') + jesli(jesli(porod, dzieci_zywe, dziecko.liczba) > 1, 'multiple', 'single'))` | KP: KP art. 182¹ᶠ § 1 i § 1¹ |
| `mama_rodzicielski_dni` | Wartość | Urlop rodzicielski mamy w dniach (wydłużony przy łączeniu z pracą) | `jesli(mama_rodzicielski_tyg > 0, min(zaokr(tygodnie(mama_rodzicielski_tyg) / (1 - mama_praca), 0), tygodnie(limit_z_praca_tyg)), 0)` | KP: KP art. 182¹ᶠ § 1–7 |
| `tata_rodzicielski_dni` | Wartość | Urlop rodzicielski taty w dniach (wydłużony przy łączeniu z pracą) | `jesli(tata_rodzicielski_tyg > 0, min(zaokr(tygodnie(tata_rodzicielski_tyg) / (1 - tata_praca), 0), tygodnie(limit_z_praca_tyg)), 0)` | KP: KP art. 182¹ᶠ § 1–7 |
| `tata_wylaczny_dni` | Wartość | Część wyłączna urlopu rodzicielskiego taty (dni) | `jesli(oboje_rodzicielski, min(tata_rodzicielski_dni, zaokr(tygodnie(min(tata_rodzicielski_tyg, wylaczna_czesc_tyg)) / (1 - tata_praca), 0)), 0)` | KP: KP art. 182¹ᵃ § 4; UZ art. 31 ust. 3f |
| `start_rodzicielski_mamy` | Wartość | Początek urlopu rodzicielskiego mamy (domyślnie bezpośrednio po macierzyńskim) | `jesli(jest(plan.rodzicielski_mama_od), plan.rodzicielski_mama_od, dodaj_dni(najpozniej(koniec_ciaglosci, dodaj_dni(data_zdarzenia, -1)), 1))` | KP: KP art. 182¹ᵃ, art. 182¹ᶜ |
| `mama_rodzicielski` | Okres | Urlop rodzicielski | `start: start_rodzicielski_mamy; dni: mama_rodzicielski_dni; stawka: stawka_rodzicielska` | KP: KP art. 182¹ᵃ–182¹ᶠ; UZ art. 31 ust. 2, 3, 3g, 4a |
| `koniec_rodzicielskiego_mamy` | Wartość | Ostatni dzień urlopu rodzicielskiego mamy | `dodaj_dni(start_rodzicielski_mamy, mama_rodzicielski_dni - 1) **gdy** mama_rodzicielski_dni > 0` | KP: KP art. 182¹ᵃ |
| `start_rodzicielski_taty` | Wartość | Początek urlopu rodzicielskiego taty (domyślnie po urlopie mamy i po urlopie ojcowskim) | `jesli(jest(plan.rodzicielski_tata_od), plan.rodzicielski_tata_od, dodaj_dni(najpozniej(koniec_rodzicielskiego_mamy, koniec_ciaglosci, dodaj_dni(data_zdarzenia, -1), jesli(brak(plan.ojcowski_od), tata_ojcowski.koniec, None)), 1))` | KP: KP art. 182¹ᵃ § 6–7 |
| `tata_rodzicielski_wylaczny` | Okres | Urlop rodzicielski – część wyłączna (9 tyg.) | `start: start_rodzicielski_taty; dni: tata_wylaczny_dni; stawka: param('rate_parental')` | KP: KP art. 182¹ᵃ § 4; UZ art. 31 ust. 3f |
| `tata_rodzicielski_wspolny` | Okres | Urlop rodzicielski | `start: jesli(tata_rodzicielski_wylaczny.aktywny, dodaj_dni(tata_rodzicielski_wylaczny.koniec, 1), start_rodzicielski_taty); dni: tata_rodzicielski_dni - tata_wylaczny_dni; stawka: stawka_rodzicielska` | KP: KP art. 182¹ᵃ; UZ art. 30a ust. 3, art. 31 ust. 2–3 |
| `rodzicielski_termin` | Wartość | Ostatni dzień na wykorzystanie urlopu rodzicielskiego | `jesli(dziecko.zdarzenie == 'przysposobienie' or (przyjecie and przyjecie_okres_minimalny), dodaj_dni(dodaj_mies(dziecko.data_urodzenia, 12 * tabela('adoption_leave_max_child_age_years', 'adoption')), -1), koniec_roku(dziecko.data_urodzenia, param('parental_deadline_child_age_years')))` | KP: KP art. 182¹ᶜ, art. 183 § 4¹–4², § 5 |

## Urlop macierzyński

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `wymiar_macierzynski_pelny_dni` | Wartość | Pełny wymiar urlopu macierzyńskiego (dni) | `tygodnie(tabela('maternity_leave_weeks', klucz_liczby_dzieci))` | KP: KP art. 180 § 1, art. 183 § 1 i § 1¹, art. 183¹ § 1 |
| `wymiar_macierzynski_zywe_dni` | Wartość | Wymiar stosowny do liczby dzieci pozostałych przy życiu (dni) | `jesli(dziecko_zyje, tygodnie(tabela('maternity_leave_weeks', klucz_dzieci(dzieci_zywe))), 0)` | KP: KP art. 180¹ § 1–2 |
| `przyjecie_okres_minimalny` | Wartość | Przyjęcie: urlop ograniczony wiekiem dziecka (przypadek z art. 183 § 3 KP) | `przyjecie_w_limicie and dni_do_limitu_wieku < wymiar_macierzynski_pelny_dni` | KP: KP art. 183 § 3, § 4 pkt 3, § 4² |
| `wymiar_na_warunkach_dni` | Wartość | Wymiar urlopu na warunkach urlopu macierzyńskiego (dni) | `jesli(przyjecie_w_limicie, max(min(wymiar_macierzynski_pelny_dni, dni_do_limitu_wieku), tygodnie(param('taken_in_min_maternity_weeks'))), 0)` | KP: KP art. 183 § 1, § 1¹, § 3; ZAL |
| `wymiar_macierzynski_dni` | Wartość | Wymiar urlopu macierzyńskiego w tej sytuacji (dni) | `jesli(przyjecie, wymiar_na_warunkach_dni, jesli(brak(dziecko.data_zgonu), wymiar_macierzynski_pelny_dni, jesli(dziecko_zyje, jesli(zgon_wczesny, wymiar_macierzynski_zywe_dni, min(wymiar_macierzynski_pelny_dni, max(wymiar_macierzynski_zywe_dni, dni_do_zgonu_plus))), jesli(zgon_wczesny, max(tygodnie(param('stillbirth_maternity_weeks')), dni_do_zgonu_plus), min(wymiar_macierzynski_pelny_dni, dni_do_zgonu_plus)))))` | KP: KP art. 180 § 1, art. 180¹, art. 183 |
| `przed_porodem_dni` | Wartość | Część urlopu macierzyńskiego przed porodem (dni) | `jesli(porod and mama_uprawniona, tygodnie(plan.przed_porodem_tyg), 0)` | KP: KP art. 180 § 2 |
| `matka_min_osobiscie_tyg` | Wartość | Ile tygodni po porodzie matka wykorzystuje, zanim przekaże resztę ojcu | `jesli(sytuacja_matki.rodzaj == 'niezdolnosc', param('maternity_mother_min_weeks_disabled'), param('maternity_mother_mandatory_weeks'))` | KP: KP art. 180 § 4 i § 6; UZ art. 29 ust. 3 i 5 |
| `dla_taty_dni` | Wartość | Część urlopu macierzyńskiego przejmowana przez tatę (dni) | `jesli(porod and mama_uprawniona and tata_uprawniony and dziecko_zyje, tygodnie(plan.dla_taty_tyg), 0)` | KP: KP art. 180 § 4–5; UZ art. 29 ust. 3 |
| `mama_pula_po_porodzie` | Wartość | Urlop macierzyński po porodzie do podziału (dni) | `jesli(mama_uprawniona, wymiar_macierzynski_dni - przed_porodem_dni, 0)` | KP: KP art. 180 § 3 |
| `szpital_matki` | Wartość | Matka w szpitalu – część urlopu wykorzystuje tata | `porod and mama_uprawniona and tata_uprawniony and sytuacja_matki.rodzaj == 'szpital' and jest(sytuacja_matki.od)` | KP: KP art. 180 § 10–11; UZ art. 29 ust. 6 |
| `zgon_porzucenie_matki` | Wartość | Zgon matki albo porzucenie dziecka | `sytuacja_matki.rodzaj in ['zgon', 'porzucenie'] and jest(sytuacja_matki.od)` | KP: KP art. 180 § 12–13, § 15; UZ art. 29 ust. 7 i 9 |
| `mama_dni_1` | Wartość | Urlop macierzyński mamy po porodzie – pierwsza część (dni) | `jesli(not mama_uprawniona, 0, jesli(zgon_porzucenie_matki, min(mama_pula_po_porodzie, jesli(sytuacja_matki.rodzaj == 'porzucenie', max(dni_miedzy(data_zdarzenia, sytuacja_matki.od) + 1, tygodnie(param('maternity_min_weeks_before_transfer'))), dni_miedzy(data_zdarzenia, sytuacja_matki.od) + 1)), jesli(szpital_matki, min(mama_pula_po_porodzie, max(dni_miedzy(data_zdarzenia, sytuacja_matki.od), tygodnie(param('maternity_min_weeks_before_transfer')))), mama_pula_po_porodzie - dla_taty_dni)))` | KP: KP art. 180, 182; UZ art. 29 |
| `tata_szpital_dni` | Wartość | Część urlopu taty na czas pobytu matki w szpitalu (dni) | `jesli(szpital_matki, min(mama_pula_po_porodzie - mama_macierzynski.dni, dni_miedzy(sytuacja_matki.od, jesli(jest(sytuacja_matki.do), sytuacja_matki.do, sytuacja_matki.od)) + 1), 0)` | KP: KP art. 180 § 10–11; UZ art. 29 ust. 6 |
| `przyjecie_tata_calosc` | Wartość | Przyjęcie dziecka: urlop na warunkach urlopu macierzyńskiego wykorzystuje tata | `przyjecie and not mama_uprawniona and tata_uprawniony` | KP: KP art. 183; UZ art. 29 ust. 2 |
| `tata_przejecie_dni` | Wartość | Urlop (zasiłek) macierzyński taty: przejęta część albo okres po zdarzeniu dotyczącym matki (dni) | `jesli(not tata_uprawniony or not dziecko_zyje, 0, jesli(przyjecie_tata_calosc, wymiar_na_warunkach_dni, jesli(mama_uprawniona, jesli(zgon_porzucenie_matki, mama_pula_po_porodzie - mama_macierzynski.dni, dla_taty_dni), jesli(porod and sytuacja_matki.rodzaj in ['zgon', 'porzucenie', 'niezdolnosc'] and jest(sytuacja_matki.od), max(0, dni_miedzy(sytuacja_matki.od, dodaj_dni(data_zdarzenia, wymiar_macierzynski_dni - 1))), jesli(porod and sytuacja_matki.rodzaj == 'zatrudnienie' and jest(sytuacja_matki.od), max(0, min(dni_miedzy(sytuacja_matki.od, dodaj_dni(data_zdarzenia, wymiar_macierzynski_dni - 1)) + 1, jesli(jest(sytuacja_matki.do), dni_miedzy(sytuacja_matki.od, sytuacja_matki.do) + 1, 100000))), 0)))))` | KP: KP art. 180 § 4–17, art. 183; UZ art. 29 ust. 3–10 |
| `mama_macierzynski_przed` | Okres | Urlop macierzyński przed porodem | `start: dodaj_dni(data_zdarzenia, -przed_porodem_dni); dni: przed_porodem_dni; stawka: stawka_macierzynska` | KP: KP art. 180 § 2; UZ art. 31 ust. 1 |
| `mama_macierzynski` | Okres | {jesli(porod, 'Urlop macierzyński', 'Urlop na warunkach urlopu macierzyńskiego')} | `start: data_zdarzenia; dni: mama_dni_1; stawka: stawka_macierzynska` | KP: KP art. 180, 180¹, 183; UZ art. 29, 31 |
| `tata_macierzynski_szpital` | Okres | Urlop macierzyński taty – pobyt matki w szpitalu | `start: dodaj_dni(mama_macierzynski.koniec, 1); dni: tata_szpital_dni; stawka: stawka_macierzynska` | KP: KP art. 180 § 10–11; UZ art. 29 ust. 6 |
| `mama_macierzynski_dokonczenie` | Okres | Urlop macierzyński – dokończenie po szpitalu | `start: dodaj_dni(tata_macierzynski_szpital.koniec, 1); dni: mama_pula_po_porodzie - mama_macierzynski.dni - tata_szpital_dni - dla_taty_dni; stawka: stawka_macierzynska **gdy** szpital_matki` | KP: KP art. 180 § 10; UZ art. 29 ust. 6 |
| `tata_macierzynski` | Okres | {jesli(przyjecie, 'Urlop na warunkach urlopu macierzyńskiego', 'Urlop macierzyński taty')} | `start: jesli(przyjecie_tata_calosc, data_zdarzenia, jesli(mama_uprawniona, dodaj_dni(najpozniej(mama_macierzynski.koniec, mama_macierzynski_dokonczenie.koniec), 1), jesli(sytuacja_matki.rodzaj == 'zatrudnienie', sytuacja_matki.od, dodaj_dni(sytuacja_matki.od, 1)))); dni: tata_przejecie_dni; stawka: stawka_macierzynska` | KP: KP art. 180 § 4–17, art. 183; UZ art. 29 |
| `koniec_macierzynskiego` | Wartość | Ostatni dzień urlopu macierzyńskiego w rodzinie | `najpozniej(mama_macierzynski.koniec, mama_macierzynski_dokonczenie.koniec, tata_macierzynski.koniec)` | KP: KP art. 180 |

## Stawki

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `usredniona_w_terminie` | Wartość | Wniosek o stawkę uśrednioną jest jeszcze możliwy albo złożony w terminie | `przed_zdarzeniem or dzis() <= dodaj_dni(data_zdarzenia, param('averaged_application_deadline_days')) or (jest(plan.wniosek_usredniony_zlozony) and plan.wniosek_usredniony_zlozony <= dodaj_dni(data_zdarzenia, param('averaged_application_deadline_days')))` | UZ: UZ art. 30a ust. 1–2 |
| `usredniona` | Wartość | Zasiłek w stawce uśrednionej (wniosek z art. 30a) | `plan.stawka_usredniona and usredniona_w_terminie and dziecko_zyje and (mama_uprawniona or (przyjecie and tata_uprawniony))` | UZ: UZ art. 30a, art. 31 ust. 3 |
| `stawka_macierzynska` | Wartość | Stawka za urlop macierzyński / na warunkach urlopu macierzyńskiego | `jesli(usredniona, param('rate_averaged'), param('rate_maternity'))` | UZ: UZ art. 31 ust. 1 i 3 |
| `rodzicielski_w_1_roku` | Wartość | Co najmniej jeden dzień urlopu rodzicielskiego w pierwszym roku życia dziecka | `najwczesniej(jesli(mama_rodzicielski_dni > 0, start_rodzicielski_mamy, None), jesli(tata_rodzicielski_dni > 0, start_rodzicielski_taty, None)) < dodaj_mies(dziecko.data_urodzenia, 12)` | UZ: UZ art. 31 ust. 3g i 4 |
| `stawka_rodzicielska` | Wartość | Stawka za urlop rodzicielski | `jesli(usredniona and rodzicielski_w_1_roku, param('rate_averaged'), param('rate_parental'))` | UZ: UZ art. 31 ust. 2, 3, 3g |

## Uzupełniający urlop macierzyński

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `uzup_przypadek` | Wartość | Przypadek uzupełniającego urlopu (1: < 28 tyg. lub ≤ 1000 g; 2: 28–36 tyg.; 3: w terminie, szpital od 5.–28. dnia) | `jesli(not dziecko_zyje or not (porod or przyjecie_w_limicie), 0, jesli(dziecko.tydzien_ciazy < tabela('supplementary_criteria', 'long_gestation_below') or dziecko.masa_g <= tabela('supplementary_criteria', 'long_weight_max_g'), 1, jesli(dziecko.tydzien_ciazy < tabela('supplementary_criteria', 'preterm_gestation_below'), 2, jesli(dziecko.dni_szpitala >= tabela('supplementary_criteria', 'term_min_stay_days') and dziecko.pierwszy_dzien_szpitala >= tabela('supplementary_criteria', 'term_first_day_from') and dziecko.pierwszy_dzien_szpitala <= tabela('supplementary_criteria', 'term_first_day_to'), 3, 0))))` | KP: KP art. 180² § 1–2, art. 183 § 3¹ |
| `uzup_limit_tyg` | Wartość | Najwięcej tygodni uzupełniającego urlopu | `jesli(uzup_przypadek == 1, tabela('supplementary_maternity_max_weeks', 'long'), jesli(uzup_przypadek in [2, 3], tabela('supplementary_maternity_max_weeks', 'short'), 0))` | KP: KP art. 180² § 1 |
| `uzup_tyg` | Wartość | Wymiar uzupełniającego urlopu (tydzień za każdy rozpoczęty tydzień pobytu w szpitalu) | `jesli(dziecko.dni_szpitala > 0, min(uzup_limit_tyg, zaokr_gora(dziecko.dni_szpitala / 7)), 0)` | KP: KP art. 180² § 1 i § 3 |
| `uzup_bierze` | Wartość | Kto korzysta z uzupełniającego urlopu (tylko jedno z rodziców) | `jesli(plan.uzupelniajacy_bierze == 'tata' and tata_uprawniony, 'tata', jesli(mama_uprawniona, 'mama', jesli(tata_uprawniony, 'tata', None)))` | KP: KP art. 180² § 1; RW § 14 |
| `okres_uzupelniajacy` | Okres | Uzupełniający urlop macierzyński | `start: dodaj_dni(koniec_macierzynskiego, 1); dni: tygodnie(uzup_tyg); stawka: param('rate_maternity') **gdy** plan.uzupelniajacy and jest(uzup_bierze)` | KP: KP art. 180²; UZ art. 29a ust. 1, art. 31 ust. 1 |
| `koniec_ciaglosci` | Wartość | Koniec urlopu macierzyńskiego i uzupełniającego | `najpozniej(koniec_macierzynskiego, okres_uzupelniajacy.koniec)` | KP: KP art. 180² |

## Urlop ojcowski

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `ojcowski_mozliwy` | Wartość | Tata może skorzystać z urlopu (zasiłku) ojcowskiego | `tata_uprawniony and dziecko_zyje and dziecko.zdarzenie in ['porod', 'przysposobienie']` | KP: KP art. 182³; UZ art. 29a ust. 1 |
| `ojcowski_termin` | Wartość | Ostatni dzień urlopu ojcowskiego | `jesli(dziecko.zdarzenie == 'przysposobienie', najwczesniej(dodaj_mies(data_zdarzenia, param('paternity_deadline_months')), dodaj_mies(dziecko.data_urodzenia, 12 * tabela('adoption_leave_max_child_age_years', 'adoption'))), dodaj_dni(dodaj_mies(dziecko.data_urodzenia, param('paternity_deadline_months')), -1))` | KP: KP art. 182³ § 1 |
| `tata_ojcowski` | Okres | Urlop ojcowski | `start: jesli(jest(plan.ojcowski_od), plan.ojcowski_od, jesli(tata_macierzynski.aktywny and tata_macierzynski.start <= data_zdarzenia, dodaj_dni(tata_macierzynski.koniec, 1), data_zdarzenia)); dni: tygodnie(param('paternity_leave_weeks')); stawka: param('rate_maternity') **gdy** ojcowski_mozliwy` | KP: KP art. 182³; UZ art. 31 ust. 1 |

## Ciąża: zasiłek chorobowy

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `zwolnienie_b_dni` | Wartość | Długość zwolnienia lekarskiego z kodem B (dni) | `dni_miedzy(mama.zwolnienie_b_od, mama.zwolnienie_b_do) + 1 **gdy** porod and jest(mama.zwolnienie_b_od) and jest(mama.zwolnienie_b_do)` | UZ: UZ art. 57 ust. 1 pkt 2 |
| `okres_wyczekiwania` | Wartość | Okres wyczekiwania na zasiłek chorobowy (dni) | `jesli(mama.ubezpieczenie == 'obowiazkowe', tabela('sickness_waiting_days', 'mandatory'), tabela('sickness_waiting_days', 'voluntary'))` | UZ: UZ art. 4 ust. 1 |
| `wyczekiwanie_spelnione` | Wartość | Okres wyczekiwania minął | `brak(mama.dni_ubezpieczenia) or mama.dni_ubezpieczenia >= okres_wyczekiwania` | UZ: UZ art. 4 ust. 1 |
| `mama_chorobowe_prawo` | Wartość | Mama ma prawo do zasiłku chorobowego | `mama.obecny and mama.ubezpieczenie != 'brak' and wyczekiwanie_spelnione` | UZ: UZ art. 4, 6 |
| `limit_wynagrodzenia_chorobowego` | Wartość | Dni wynagrodzenia chorobowego od pracodawcy w roku | `jesli(mama.wiek_50, param('employer_sickness_paid_days_over_50'), param('sickness_employer_paid_days'))` | KP: KP art. 92 § 1 |
| `wynagrodzenie_chorobowe_dni` | Wartość | Dni wynagrodzenia chorobowego (płaci pracodawca) | `jesli(mama.pracownik and mama_chorobowe_prawo and zwolnienie_b_dni > 0, min(zwolnienie_b_dni, max(0, limit_wynagrodzenia_chorobowego - mama.dni_chorobowego_w_roku)), 0)` | KP: KP art. 92 § 1 pkt 2, § 4 |
| `zasilek_chorobowy_dni` | Wartość | Dni zasiłku chorobowego w ciąży (okres zasiłkowy 270 dni, wlicza się wynagrodzenie chorobowe) | `jesli(mama_chorobowe_prawo and zwolnienie_b_dni > 0, max(0, min(zwolnienie_b_dni, tabela('sickness_benefit_period_days', 'pregnancy')) - wynagrodzenie_chorobowe_dni), 0)` | UZ: UZ art. 8 ust. 1, art. 12 ust. 1 |
| `mama_wynagrodzenie_chorobowe` | Okres | Wynagrodzenie chorobowe w ciąży (płaci pracodawca) | `start: mama.zwolnienie_b_od; dni: wynagrodzenie_chorobowe_dni; stawka: param('rate_sickness_pregnancy')` | KP: KP art. 92 § 1 pkt 2 |
| `mama_zasilek_chorobowy` | Okres | Zasiłek chorobowy w ciąży | `start: dodaj_dni(mama.zwolnienie_b_od, wynagrodzenie_chorobowe_dni); dni: zasilek_chorobowy_dni; stawka: param('rate_sickness_pregnancy')` | UZ: UZ art. 6, 8, 11 ust. 2 pkt 1 |
| `zasilek_wys_mac` | Wartość | Prawo do zasiłku w wysokości zasiłku macierzyńskiego (do porodu) | `porod and mama.obecny and mama.pracownik and mama.przyczyna_ustania == 'upadlosc_likwidacja_smierc' and jest(mama.ustanie_ubezpieczenia) and mama.ustanie_ubezpieczenia < data_zdarzenia` | UZ: UZ art. 30 ust. 3 |
| `mama_zasilek_wys_mac` | Okres | Zasiłek w wysokości zasiłku macierzyńskiego | `start: dodaj_dni(mama.ustanie_ubezpieczenia, 1); dni: dni_miedzy(dodaj_dni(mama.ustanie_ubezpieczenia, 1), najwczesniej(mama_macierzynski_przed.start, data_zdarzenia)); stawka: param('rate_maternity') **gdy** zasilek_wys_mac` | UZ: UZ art. 30 ust. 3, art. 31 ust. 1 |

## Terminy

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `koniec_ostatniego_okresu` | Wartość | Ostatni dzień ostatniego zasiłku macierzyńskiego w rodzinie | `najpozniej(tata_rodzicielski_wspolny.koniec, tata_rodzicielski_wylaczny.koniec, mama_rodzicielski.koniec, koniec_ciaglosci, tata_ojcowski.koniec)` | UZ: UZ art. 67 |
| `t_becikowe` | Termin | Wniosek o becikowe | `dodaj_mies(data_zdarzenia, param('birth_grant_months')) **gdy** porod and not dziecko.martwe_urodzenie` | SR: Ustawa o świadczeniach rodzinnych art. 15b; gov.pl – Uzyskaj becikowe |
| `t_usredniona` | Termin | Wniosek o stawkę uśrednioną 81,5% | `dodaj_dni(data_zdarzenia, param('averaged_application_deadline_days')) **gdy** mama_uprawniona and dziecko_zyje and brak(plan.wniosek_usredniony_zlozony)` | UZ: UZ art. 30a ust. 1–2 |
| `t_mac_przed` | Termin | Wniosek o urlop macierzyński przed porodem | `dodaj_dni(mama_macierzynski_przed.start, -tabela('application_lead_days', 'maternity_before_birth')) **gdy** mama.pracownik and przed_porodem_dni > 0` | KP: KP art. 177 § 1¹ pkt 1; RW § 2; Poradnik ZUS 2026 |
| `t_rezygnacja` | Termin | Wniosek mamy o rezygnację z części urlopu | `dodaj_dni(tata_macierzynski.start, -tabela('application_lead_days', 'mother_resignation')) **gdy** mama.pracownik and dla_taty_dni > 0` | KP: KP art. 180 § 8 |
| `t_tata_macierzynski` | Termin | Wniosek taty o część urlopu macierzyńskiego | `dodaj_dni(tata_macierzynski.start, -tabela('application_lead_days', 'father_maternity_part')) **gdy** tata.pracownik and tata_przejecie_dni > 0 and mama_uprawniona and not zgon_porzucenie_matki` | KP: KP art. 180 § 9 |
| `t_uzupelniajacy` | Termin | Wniosek o uzupełniający urlop macierzyński | `jesli(jesli(uzup_bierze == 'tata', tata.pracownik, mama.pracownik), dodaj_dni(koniec_macierzynskiego, -tabela('application_lead_days', 'supplementary')), koniec_macierzynskiego) **gdy** okres_uzupelniajacy.aktywny` | KP: KP art. 180² § 4; RZ § 26 pkt 3 |
| `t_rodzicielski_mama` | Termin | Wniosek o urlop rodzicielski | `jesli(mama.pracownik, dodaj_dni(mama_rodzicielski.start, -tabela('application_lead_days', 'parental')), mama_rodzicielski.start) **gdy** mama_rodzicielski.aktywny` | KP: KP art. 182¹ᵈ § 1; RZ § 29 pkt 3 |
| `t_rodzicielski_tata` | Termin | Wniosek o urlop rodzicielski | `jesli(tata.pracownik, dodaj_dni(start_rodzicielski_taty, -tabela('application_lead_days', 'parental')), start_rodzicielski_taty) **gdy** tata_rodzicielski_wylaczny.aktywny or tata_rodzicielski_wspolny.aktywny` | KP: KP art. 182¹ᵈ § 1; RZ § 30 pkt 4 |
| `t_praca_mama` | Termin | Wniosek o łączenie urlopu z pracą | `dodaj_dni(mama_rodzicielski.start, -tabela('application_lead_days', 'work_combination')) **gdy** mama_praca > 0 and mama_rodzicielski_dni > 0` | KP: KP art. 182¹ᵉ § 2 |
| `t_praca_tata` | Termin | Wniosek o łączenie urlopu z pracą | `dodaj_dni(start_rodzicielski_taty, -tabela('application_lead_days', 'work_combination')) **gdy** tata_praca > 0 and tata_rodzicielski_dni > 0` | KP: KP art. 182¹ᵉ § 2 |
| `t_ojcowski` | Termin | Wniosek o urlop ojcowski | `jesli(tata.pracownik, dodaj_dni(tata_ojcowski.start, -tabela('application_lead_days', 'paternity')), tata_ojcowski.start) **gdy** tata_ojcowski.aktywny` | KP: KP art. 182³ § 2; RZ § 33 pkt 3 |
| `t_ojcowski_do` | Termin | Ostatni dzień urlopu ojcowskiego | `ojcowski_termin **gdy** ojcowski_mozliwy` | KP: KP art. 182³ § 1 |
| `t_rodzicielski_do` | Termin | Ostatni dzień na urlop rodzicielski | `rodzicielski_termin **gdy** wymiar_rodzicielski_tyg > 0 and (mama_uprawniona or tata_uprawniony)` | KP: KP art. 182¹ᶜ, art. 183 § 4¹ |
| `t_na_warunkach` | Termin | Wniosek o urlop na warunkach urlopu macierzyńskiego | `dodaj_dni(data_zdarzenia, tabela('application_lead_days', 'taken_in_application')) **gdy** przyjecie_w_limicie and (mama.pracownik or tata.pracownik)` | KP: KP art. 183 § 6; RW § 18 |
| `t_dlug_mama` | Termin | Spłata zadłużenia składkowego | `dodaj_mies(data_zdarzenia, param('debt_repayment_window_months')) **gdy** mama_dlug_do_splaty` | UZ: UZ art. 2a, art. 64 ust. 3 |
| `t_dlug_tata` | Termin | Spłata zadłużenia składkowego | `dodaj_mies(data_zdarzenia, param('debt_repayment_window_months')) **gdy** tata_dlug_do_splaty` | UZ: UZ art. 2a, art. 64 ust. 3 |
| `t_przedawnienie` | Termin | Przedawnienie roszczenia o zasiłek | `dodaj_mies(koniec_ostatniego_okresu, param('claim_limitation_months')) **gdy** jest(koniec_ostatniego_okresu)` | UZ: UZ art. 67 |

## Walidacja planu

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `w_martwe_przed_porodem` | Walidacja | Martwe urodzenie przed porodem | `**gdy** dziecko.martwe_urodzenie and not dziecko.urodzone` | KP: KP art. 180¹; RZ § 13 ust. 1 pkt 2 |
| `w_zgon_daty` | Walidacja | Data zgonu dziecka | `**gdy** jest(dziecko.data_zgonu) and (not dziecko.urodzone or dziecko.data_zgonu < dziecko.data_porodu or dziecko.data_zgonu > dzis())` | KP: KP art. 180¹ |
| `w_przed_porodem_max` | Walidacja | Za dużo urlopu przed porodem | `**gdy** plan.przed_porodem_tyg > param('maternity_before_birth_max_weeks')` | KP: KP art. 180 § 2 |
| `w_przed_porodem_tylko_porod` | Walidacja | Urlop przed porodem | `**gdy** plan.przed_porodem_tyg > 0 and not porod` | KP: KP art. 180 § 2 |
| `w_dla_taty_min` | Walidacja | Za dużo urlopu macierzyńskiego dla taty | `**gdy** dla_taty_dni > 0 and mama_pula_po_porodzie - dla_taty_dni < tygodnie(matka_min_osobiscie_tyg)` | KP: KP art. 180 § 4 i § 6; UZ art. 29 ust. 3 i 5 |
| `w_tata_rodzicielski_max` | Walidacja | Za dużo urlopu rodzicielskiego dla taty | `**gdy** oboje_rodzicielski and tata_rodzicielski_tyg > wymiar_rodzicielski_tyg - wylaczna_czesc_tyg` | KP: KP art. 182¹ᵃ § 4 |
| `w_mama_praca_max` | Walidacja | Za dużo pracy w trakcie urlopu rodzicielskiego (mamy) | `**gdy** mama.praca_w_rodzicielskim > param('parental_work_max_fraction')` | KP: KP art. 182¹ᵉ § 1 |
| `w_mama_praca_pracownik` | Walidacja | Łączenie urlopu z pracą (mamy) | `**gdy** mama.praca_w_rodzicielskim > 0 and not mama.pracownik` | KP: KP art. 182¹ᵉ § 1 |
| `w_mama_czesci` | Walidacja | Za dużo części urlopu rodzicielskiego (mamy) | `**gdy** plan.czesci_mama > param('parental_max_parts')` | KP: KP art. 182¹ᶜ, art. 182¹ᵈ § 2 |
| `w_tata_praca_max` | Walidacja | Za dużo pracy w trakcie urlopu rodzicielskiego (taty) | `**gdy** tata.praca_w_rodzicielskim > param('parental_work_max_fraction')` | KP: KP art. 182¹ᵉ § 1 |
| `w_tata_praca_pracownik` | Walidacja | Łączenie urlopu z pracą (taty) | `**gdy** tata.praca_w_rodzicielskim > 0 and not tata.pracownik` | KP: KP art. 182¹ᵉ § 1 |
| `w_tata_czesci` | Walidacja | Za dużo części urlopu rodzicielskiego (taty) | `**gdy** plan.czesci_tata > param('parental_max_parts')` | KP: KP art. 182¹ᶜ, art. 182¹ᵈ § 2 |
| `w_rodzicielski_mamy_start` | Walidacja | Urlop rodzicielski w trakcie macierzyńskiego | `**gdy** jest(plan.rodzicielski_mama_od) and mama_rodzicielski_dni > 0 and plan.rodzicielski_mama_od <= koniec_ciaglosci` | KP: KP art. 182¹ᵃ |
| `w_tata_nakladanie` | Walidacja | Urlopy taty nakładają się | `**gdy** naklada(tata_ojcowski, tata_macierzynski) or naklada(tata_ojcowski, tata_rodzicielski_wylaczny) or naklada(tata_ojcowski, tata_rodzicielski_wspolny) or naklada(tata_macierzynski, tata_rodzicielski_wylaczny) or naklada(tata_ojcowski, tata_macierzynski_szpital)` | KP: KP art. 182³, art. 182¹ᵃ |
| `w_ojcowski_czesci` | Walidacja | Podział urlopu ojcowskiego | `**gdy** plan.ojcowski_czesci > param('paternity_max_parts') or tygodnie(param('paternity_leave_weeks')) / plan.ojcowski_czesci < tygodnie(param('paternity_min_part_weeks'))` | KP: KP art. 182³ § 1¹ |

## Świadczenia

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `zasilek_chorobowy_ciaza` | Świadczenie | Zasiłek chorobowy w czasie ciąży | `**gdy** porod and mama.obecny and mama.ubezpieczenie != 'brak'` | UZ: UZ art. 4, 8, 11 ust. 2; KP art. 92 |
| `swiadczenie_rehabilitacyjne` | Świadczenie | Świadczenie rehabilitacyjne | `**gdy** porod and mama_chorobowe_prawo and (przed_zdarzeniem or zwolnienie_b_dni > 0)` | UZ: UZ art. 18–19 |
| `zasilek_w_wysokosci_macierzynskiego` | Świadczenie | Zasiłek w wysokości zasiłku macierzyńskiego | `**gdy** zasilek_wys_mac` | UZ: UZ art. 30 ust. 1 i 3 |
| `macierzynski_mama` | Świadczenie | {jesli(porod, 'Zasiłek macierzyński za okres urlopu macierzyńskiego', 'Zasiłek macierzyński za okres urlopu na warunkach urlopu macierzyńskiego')} | `**gdy** mama.obecny and (porod or przyjecie) and not przyjecie_tata_calosc` | UZ: UZ art. 29, 29a, 30, 31; KP art. 180, 180¹, 183 |
| `macierzynski_tata` | Świadczenie | {jesli(przyjecie, 'Zasiłek macierzyński za okres urlopu na warunkach urlopu macierzyńskiego', 'Zasiłek macierzyński za część urlopu macierzyńskiego')} | `**gdy** tata.obecny and (tata_przejecie_dni > 0 or tata_szpital_dni > 0)` | UZ: UZ art. 29 ust. 3–10, art. 29a ust. 2; KP art. 180 § 4–17 |
| `uzupelniajacy` | Świadczenie | Zasiłek za uzupełniający urlop macierzyński | `**gdy** uzup_tyg > 0` | KP: KP art. 180²; UZ art. 29a ust. 1, art. 31 ust. 1 |
| `rodzicielski_mama` | Świadczenie | Zasiłek macierzyński za okres urlopu rodzicielskiego | `**gdy** mama.obecny and dziecko_zyje and mama_uprawniona and not zgon_porzucenie_matki` | KP: KP art. 182¹ᵃ–182¹ᶠ; UZ art. 29a, 31 |
| `rodzicielski_tata` | Świadczenie | Zasiłek macierzyński za okres urlopu rodzicielskiego | `**gdy** tata.obecny and dziecko_zyje and tata_uprawniony` | KP: KP art. 182¹ᵃ–182¹ᶠ; UZ art. 29a, 31 ust. 3f, 3h |
| `ojcowski` | Świadczenie | Zasiłek macierzyński za okres urlopu ojcowskiego | `**gdy** tata.obecny and ojcowski_mozliwy` | KP: KP art. 182³; UZ art. 29a ust. 1, art. 31 ust. 1 |
| `pogrzebowy` | Świadczenie | Zasiłek pogrzebowy | `**gdy** porod and dziecko.martwe_urodzenie` | PR: Poradnik ZUS 2026 – Zasiłek pogrzebowy |
| `opiekunczy` | Świadczenie | Zasiłek opiekuńczy | `**gdy** dziecko_zyje` | PR: Poradnik ZUS 2026 – Zasiłek opiekuńczy |
| `becikowe` | Świadczenie | Becikowe – jednorazowa zapomoga z tytułu urodzenia dziecka | `**gdy** porod and not dziecko.martwe_urodzenie` | SR: Ustawa o świadczeniach rodzinnych art. 15b; gov.pl – Uzyskaj becikowe |
| `swiadczenie_rodzicielskie_info` | Świadczenie | Świadczenie rodzicielskie | `**gdy** (porod or przyjecie) and dziecko_zyje and not mama_uprawniona and not tata_uprawniony` | PR: Poradnik ZUS 2026 – Ważne informacje uzupełniające |

## Dokumenty

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `d_becikowe` | Dokument | Becikowe – dokumenty do gminy | `**gdy** porod and not dziecko.martwe_urodzenie` | SR: Ustawa o świadczeniach rodzinnych art. 15b; gov.pl – Uzyskaj becikowe |
| `d_mac_wniosek_pracodawca` | Dokument | Wniosek o urlop | `**gdy** mama.pracownik and mama_uprawniona and porod` | PR: Poradnik ZUS 2026 – Jak otrzymać zasiłek; RW § 15 |
| `d_mac_przed_porodem` | Dokument | Zaświadczenie o przewidywanej dacie porodu | `**gdy** porod and przed_porodem_dni > 0` | RZ: RZ § 13 ust. 1 pkt 1; RW § 2; UZ art. 53 ust. 2 |
| `d_mac_zus` | Dokument | Wniosek do ZUS | `**gdy** mama_uprawniona and mama_platnik == 'zus'` | RZ: RZ § 3, § 12, zał. 6; UZ art. 61b ust. 5; Poradnik ZUS 2026 |
| `d_mac_odpis_zus` | Dokument | Odpis aktu urodzenia | `**gdy** porod and dziecko.urodzone and mama_uprawniona and mama_platnik == 'zus' and not dziecko.martwe_urodzenie` | RZ: RZ § 13 ust. 2–4 |
| `d_mac_martwe` | Dokument | Dokument o martwym urodzeniu | `**gdy** porod and dziecko.martwe_urodzenie` | RZ: RZ § 13 ust. 1 pkt 2 |
| `d_mac_po_ustaniu` | Dokument | Dokumenty – poród po ustaniu ubezpieczenia | `**gdy** mama_po_ustaniu` | RZ: RZ § 15 |
| `d_wys_mac` | Dokument | Dokumenty – zasiłek w wysokości zasiłku macierzyńskiego | `**gdy** zasilek_wys_mac` | RZ: RZ § 17 |
| `d_przysposobienie` | Dokument | Dokumenty – przysposobienie | `**gdy** dziecko.zdarzenie == 'przysposobienie' and (mama_uprawniona or tata_uprawniony)` | RZ: RZ § 16 ust. 1; RW § 18 |
| `d_rodzina_zastepcza` | Dokument | Dokumenty – rodzina zastępcza | `**gdy** dziecko.zdarzenie == 'rodzina_zastepcza' and (mama_uprawniona or tata_uprawniony)` | RZ: RZ § 16 ust. 2; RW § 18 |
| `d_tata_przejecie` | Dokument | Dokumenty – tata przejmuje część urlopu | `**gdy** dla_taty_dni > 0` | RZ: RZ § 18, § 20 ust. 1; RW § 3, § 5 |
| `d_szpital_matki` | Dokument | Dokumenty – pobyt mamy w szpitalu | `**gdy** szpital_matki` | RZ: RZ § 23–24; RW § 6–7 |
| `d_zgon_porzucenie` | Dokument | Dokumenty – zgon matki / porzucenie dziecka | `**gdy** zgon_porzucenie_matki and tata_uprawniony` | RZ: RZ § 20 ust. 3–4; RW § 8–11 |
| `d_niezdolnosc` | Dokument | Dokumenty – niezdolność matki do samodzielnej egzystencji | `**gdy** sytuacja_matki.rodzaj == 'niezdolnosc' and tata_uprawniony` | RZ: RZ § 21–22; RW § 4, § 12 |
| `d_zatrudnienie_matki` | Dokument | Dokumenty – matka podjęła pracę | `**gdy** sytuacja_matki.rodzaj == 'zatrudnienie' and tata_uprawniony` | RZ: RZ § 25; RW § 13 |
| `d_uzupelniajacy` | Dokument | Dokumenty – urlop uzupełniający | `**gdy** uzup_tyg > 0 and plan.uzupelniajacy and jest(uzup_bierze)` | KP: KP art. 180² § 5; RW § 14; RZ § 26–27 |
| `d_rodzicielski_mama` | Dokument | Dokumenty – urlop rodzicielski | `**gdy** mama_rodzicielski_dni > 0` | RW: RW § 15; RZ § 29–30 |
| `d_rodzicielski_tata` | Dokument | Dokumenty – urlop rodzicielski | `**gdy** tata_rodzicielski_dni > 0` | RW: RW § 15; RZ § 29–30; RZ § 32 |
| `d_praca_mama` | Dokument | Wniosek o łączenie urlopu z pracą | `**gdy** mama_praca > 0 and mama_rodzicielski_dni > 0` | RW: RW § 16; RZ § 29 pkt 2 |
| `d_praca_tata` | Dokument | Wniosek o łączenie urlopu z pracą | `**gdy** tata_praca > 0 and tata_rodzicielski_dni > 0` | RW: RW § 16; RZ § 29 pkt 2 |
| `d_ojcowski` | Dokument | Dokumenty – urlop ojcowski | `**gdy** ojcowski_mozliwy` | RW: RW § 17; RZ § 33 |
| `d_za_zyciem` | Dokument | Oświadczenie „Za życiem” | `**gdy** dziecko.za_zyciem and (mama_uprawniona or tata_uprawniony)` | UZ: UZ art. 61b ust. 4a |
| `d_chorobowy` | Dokument | Zwolnienie e-ZLA z kodem B | `**gdy** zwolnienie_b_dni > 0 and mama_chorobowe_prawo` | UZ: UZ art. 55, 61b ust. 2; RZ § 3; Poradnik ZUS 2026 |
| `d_podwyzszenie` | Dokument | Podwyższenie zasiłku | `**gdy** jest(param('parental_benefit_amount'))` | RZ: RZ § 28; UZ art. 62 ust. 4–6 |

## Ryzyka

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `r_brak_ubezpieczenia_mama` | Ryzyko | Brak prawa do zasiłku macierzyńskiego (mamy) | `**gdy** mama.obecny and (porod or przyjecie) and not mama_uprawniona and not mama_dlug_przedawnia` | UZ: UZ art. 29 ust. 1; Poradnik ZUS 2026 |
| `r_dlug_mama` | Ryzyko | Zadłużenie z tytułu składek (mamy) | `**gdy** mama_dlug_ponad_prog` | UZ: UZ art. 2a |
| `r_ulga_na_start_mama` | Ryzyko | Ulga na start (mamy) | `**gdy** mama.ulga_na_start` | PR: Poradnik ZUS 2026 – Tzw. ulga na start |
| `r_dobrowolne_po_mama` | Ryzyko | Ponowne zgłoszenie do ubezpieczenia chorobowego (mamy) | `**gdy** mama.ubezpieczenie == 'dobrowolne' and mama_uprawniona` | PR: Poradnik ZUS 2026 – Ważne informacje uzupełniające |
| `r_dobrowolne_wstecz_mama` | Ryzyko | Brak dobrowolnego ubezpieczenia chorobowego (mamy) | `**gdy** przed_zdarzeniem and mama.zatrudnienie in ['zlecenie', 'dzialalnosc', 'wspolpracujaca'] and mama.ubezpieczenie == 'brak' and not mama.ulga_na_start` | PR: Poradnik ZUS 2026; UZ art. 29 ust. 1 |
| `r_brak_ubezpieczenia_tata` | Ryzyko | Brak prawa do zasiłku macierzyńskiego (taty) | `**gdy** tata.obecny and (porod or przyjecie) and not tata_uprawniony and not tata_dlug_przedawnia and not przyjecie_tata_calosc` | UZ: UZ art. 29 ust. 1; Poradnik ZUS 2026 |
| `r_dlug_tata` | Ryzyko | Zadłużenie z tytułu składek (taty) | `**gdy** tata_dlug_ponad_prog` | UZ: UZ art. 2a |
| `r_ulga_na_start_tata` | Ryzyko | Ulga na start (taty) | `**gdy** tata.ulga_na_start` | PR: Poradnik ZUS 2026 – Tzw. ulga na start |
| `r_dobrowolne_po_tata` | Ryzyko | Ponowne zgłoszenie do ubezpieczenia chorobowego (taty) | `**gdy** tata.ubezpieczenie == 'dobrowolne' and tata_uprawniony` | PR: Poradnik ZUS 2026 – Ważne informacje uzupełniające |
| `r_dobrowolne_wstecz_tata` | Ryzyko | Brak dobrowolnego ubezpieczenia chorobowego (taty) | `**gdy** przed_zdarzeniem and tata.zatrudnienie in ['zlecenie', 'dzialalnosc', 'wspolpracujaca'] and tata.ubezpieczenie == 'brak' and not tata.ulga_na_start` | PR: Poradnik ZUS 2026; UZ art. 29 ust. 1 |
| `r_9_tygodni` | Ryzyko | Część urlopu taty przepadnie | `**gdy** oboje_rodzicielski and tata_rodzicielski_tyg < wylaczna_czesc_tyg` | KP: KP art. 182¹ᵃ § 4 |
| `r_pierwszy_rok` | Ryzyko | Urlop rodzicielski poza pierwszym rokiem życia | `**gdy** usredniona and wymiar_rodzicielski_tyg > 0 and not rodzicielski_w_1_roku` | UZ: UZ art. 31 ust. 3g i 4 |
| `r_usredniona_po_terminie` | Ryzyko | Termin na stawkę 81,5% minął | `**gdy** plan.stawka_usredniona and not usredniona_w_terminie and mama_uprawniona` | UZ: UZ art. 30a, art. 31 ust. 1–2 |
| `r_ojcowski_po_terminie` | Ryzyko | Urlop ojcowski po terminie | `**gdy** tata_ojcowski.aktywny and tata_ojcowski.koniec > ojcowski_termin` | KP: KP art. 182³ § 1 |
| `r_rodzicielski_po_terminie` | Ryzyko | Urlop rodzicielski po terminie | `**gdy** najpozniej(mama_rodzicielski.koniec, tata_rodzicielski_wspolny.koniec, tata_rodzicielski_wylaczny.koniec) > rodzicielski_termin` | KP: KP art. 182¹ᶜ |
| `r_okres_zasilkowy` | Ryzyko | Koniec okresu zasiłkowego | `**gdy** zwolnienie_b_dni > tabela('sickness_benefit_period_days', 'pregnancy')` | UZ: UZ art. 8 ust. 1, art. 18 |
| `r_wyczekiwanie` | Ryzyko | Okres wyczekiwania na zasiłek chorobowy | `**gdy** zwolnienie_b_dni > 0 and mama.ubezpieczenie != 'brak' and not wyczekiwanie_spelnione` | UZ: UZ art. 4 ust. 1 |
| `r_kontrola_zwolnien` | Ryzyko | Kontrola zwolnienia lekarskiego | `**gdy** zwolnienie_b_dni > 0` | UZ: UZ art. 17 |
| `r_ochrona` | Ryzyko | Ochrona przed zwolnieniem z pracy | `**gdy** mama.pracownik and porod` | KP: KP art. 177 § 1, § 1¹, § 4 |
| `r_umowa_terminowa` | Ryzyko | Umowa na czas określony | `**gdy** mama.pracownik and porod and mama.umowa_przedluzona_do_porodu` | KP: KP art. 177 § 3–3¹; UZ art. 30 ust. 4 |
| `r_pozorna_umowa` | Ryzyko | Umowa zawarta dla pozoru | `**gdy** porod and przed_zdarzeniem and (mama.zatrudnienie in ['umowa_o_prace', 'zlecenie'] or tata.zatrudnienie in ['umowa_o_prace', 'zlecenie'])` | PR: Poradnik ZUS 2026 |
| `r_podwyzszenie` | Ryzyko | Zasiłek niższy niż świadczenie rodzicielskie | `**gdy** jest(param('parental_benefit_amount')) and mama_uprawniona and jest(mama_podstawa) and mama_podstawa * param('rate_parental') < param('parental_benefit_amount')` | UZ: UZ art. 31 ust. 3a–3c; Poradnik ZUS 2026 |

## Informacje

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `i_wyplata` | Informacja | Termin wypłaty | `**gdy** mama_uprawniona or tata_uprawniony` | UZ: UZ art. 64 ust. 1 |
| `i_wychowawczy` | Informacja | Urlop wychowawczy | `**gdy** mama.urlop_wychowawczy or tata.urlop_wychowawczy` | UZ: UZ art. 29 ust. 1; Poradnik ZUS 2026 |
| `i_kontakt` | Informacja | Pytania do ZUS | `**gdy** True` | PR: Poradnik ZUS 2026 – Pozostańmy w kontakcie |

## Założenia obliczeń

| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |
|---|---|---|---|---|
| `z_kwoty` | Założenie | Kwoty | `**gdy** True` | UZ: UZ art. 11 ust. 4–5, art. 36 ust. 3 |
| `z_podstawa` | Założenie | Podstawa wymiaru | `**gdy** jest(mama_podstawa) or jest(tata_podstawa)` | UZ: UZ art. 36, 38, 45, 48; ZAL |
| `z_tydzien` | Założenie | Tydzień urlopu | `**gdy** True` | KP: KP art. 183¹ |
