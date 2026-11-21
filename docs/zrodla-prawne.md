# Źródła danych prawnych

Wszystkie liczby prawne żyją w tabeli `legal_parameter` (seed: `backend/app/seed/parameters_2026.py`).
Przy każdym parametrze `legal_basis` wskazuje artykuł. Poniżej skąd brać i weryfikować treść.

## Teksty ustaw (źródło urzędowe)

| Akt | Adres | Uwagi |
|---|---|---|
| Ustawa zasiłkowa (o świadczeniach pieniężnych z ubezpieczenia społecznego w razie choroby i macierzyństwa), tekst jedn. Dz.U. 2026 poz. 854 | https://eli.gov.pl/eli/DU/2026/854 · PDF: https://api.sejm.gov.pl/eli/acts/DU/2026/854/text/T/D20260854L.pdf | zasiłek macierzyński (art. 29–31), chorobowy (art. 4–11), opiekuńczy (art. 32–35) |
| Ustawa o świadczeniach rodzinnych, tekst jedn. Dz.U. 2026 poz. 1240 | https://eli.gov.pl/eli/DU/2026/1240 | becikowe, zasiłek rodzinny |
| Kodeks pracy (urlopy: art. 180–182³, wynagrodzenie chorobowe art. 92) | https://api.sejm.gov.pl/eli/acts/DU/<rok>/<poz>/text/T/… | pozycja aktualnego tekstu jedn. sprawdź na eli.gov.pl |
| Ustawa o zmianie ustawy zasiłkowej, Dz.U. 2026 poz. 441 (w życie 1.07.2026) | https://eli.gov.pl/eli/DU/2026/441 | zmiana już ujęta w tekście jednolitym |

Dostęp programowy: **API Sejmu ELI** (`https://api.sejm.gov.pl/eli/acts/DU/<rok>/<poz>/text.pdf`, `.../text.html`)
oraz `eli.gov.pl`. Można z niego pobierać tekst i stan prawny na dany dzień.

## Wyjaśnienia i stawki

- zus.pl – opisy spraw, bieżące wyjaśnienia komórek merytorycznych, formularze (Z-3, Z-15, ZAS-53, ZAM).
- gov.pl/web/rodzina – pytania i odpowiedzi o urlopach i zasiłkach.
- Kwoty zmienne rok do roku (płaca minimalna, świadczenie rodzicielskie, składki): obwieszczenia i rozporządzenia
  publikowane w Dzienniku Ustaw / Monitorze Polskim – po każdej zmianie dodaj **nowy wiersz** z `valid_from`.
- Serwisy komentujące (infor.pl, lexlege.pl, arslege.pl) są wygodne do czytania artykułów, ale nieurzędowe –
  zawsze potwierdzaj na tekście z ELI.

## Co sprawdzono w tej rundzie

- Wynagrodzenie chorobowe od pracodawcy: 33 dni w roku kalendarzowym, 14 dni po ukończeniu 50 lat
  (dotyczy niezdolności w roku następującym po roku 50. urodzin) – art. 92 KP; w ciąży 100% podstawy.
- Zasiłek opiekuńczy: limity 60/30/14 dni, wspólne dla całej rodziny, bez względu na liczbę dzieci
  i uprawnionych – art. 32–33 ustawy zasiłkowej; wyłączenie przy innym domowniku – art. 34
  (nie dotyczy chorego dziecka do 2 lat); dodatkowy zasiłek ojca do 8 tygodni – art. 32a.
- Zasiłek macierzyński bez okresu wyczekiwania, także po ustaniu ubezpieczenia w określonych przypadkach
  (art. 29–30); roszczenie przedawnia się po 6 miesiącach od ostatniego dnia okresu zasiłku.

## Do potwierdzenia z mentorem ZUS

- znaczenie „brak spłaty = przedawnienie” przy zadłużeniu składkowym,
- dokładne warunki wyjątków ubezpieczeniowych (rozwiązanie umowy w ciąży),
- pozycje Dz.U. tekstów jednolitych Kodeksu pracy (zmieniają się po każdej nowelizacji).
