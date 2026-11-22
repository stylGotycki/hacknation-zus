# Maszyna stanów: scenariusze świadczeń rodzicielskich

Dokument opisuje **wszystkie scenariusze**, które przewodnik rozróżnia na podstawie sześciu źródeł
(Kodeks pracy – KP, ustawa zasiłkowa – UZ, rozporządzenie o dokumentach do zasiłków – RZ,
rozporządzenie o wnioskach dotyczących uprawnień rodzicielskich – RW, Poradnik ZUS 2026 – PR,
załącznik o podstawie wymiaru – ZAL). Innych źródeł nie ma.

Diagramy są tylko dokumentacją (wersje PNG: [1-kroki-kalkulatora](diagramy/1-kroki-kalkulatora.png), [2-prawo-do-zasilku](diagramy/2-prawo-do-zasilku.png), [3-urlop-macierzynski](diagramy/3-urlop-macierzynski.png), [4-rodzicielski-ojcowski-stawki](diagramy/4-rodzicielski-ojcowski-stawki.png), [5-ciaza](diagramy/5-ciaza.png)). Działające reguły leżą w bazie (tabela `rule`, seed:
`backend/app/seed/rules/` (pakiet: po jednym pliku na obszar)``), administrator zmienia je w panelu. Kody w nawiasach `[…]` to kody
reguł, które realizują dane przejście.

## 1. Kroki kalkulatora (to, o co pytamy)

Kroki, które w danej sytuacji nie mają sensu, są pomijane. Na przykład bez taty nie ma pytań o
podział urlopu, a martwego urodzenia nie da się wybrać w ciąży.

```mermaid
stateDiagram-v2
    direction TB
    [*] --> Sytuacja
    Sytuacja --> Dziecko_ciaza: Jestem w ciąży
    Sytuacja --> Dziecko_urodzone: Dziecko się urodziło
    Sytuacja --> Dziecko_przyjete: Przysposobienie / rodzina zastępcza

    state "Dziecko – ciąża" as Dziecko_ciaza
    note right of Dziecko_ciaza
        przewidywana data porodu (≥ dziś), liczba dzieci, „Za życiem”
        BRAK pytań o martwe urodzenie i zgon [w_martwe_przed_porodem]
    end note
    state "Dziecko – po porodzie" as Dziecko_urodzone
    note right of Dziecko_urodzone
        data porodu (≤ dziś), liczba dzieci,
        żyje / urodziło się martwe / zmarło (data zgonu: poród ≤ zgon ≤ dziś) [w_zgon_daty],
        wcześniak: tydzień ciąży, masa, dni w szpitalu, od którego dnia
    end note
    state "Dziecko – przyjęte" as Dziecko_przyjete
    note right of Dziecko_przyjete
        data przyjęcia, wiek dziecka, liczba dzieci,
        rodzina zastępcza: odroczony obowiązek szkolny
    end note

    Dziecko_ciaza --> Rodzina_porod
    Dziecko_urodzone --> Rodzina_porod
    Dziecko_przyjete --> Rodzina_przyjecie

    state "Rodzina (poród): mama + tata? / tylko mama" as Rodzina_porod
    state "Rodzina (przyjęcie): mama i tata / tylko mama / tylko tata" as Rodzina_przyjecie

    Rodzina_porod --> Praca_mamy
    Rodzina_przyjecie --> Praca_mamy: jest mama
    Rodzina_przyjecie --> Praca_taty: tylko tata

    state "Praca mamy" as Praca_mamy
    state "Praca taty" as Praca_taty
    note left of Praca_mamy
        tytuł ubezpieczenia, dobrowolne chorobowe, ulga na start,
        urlop wychowawczy, podstawa, płatnik >20 osób, etat,
        zadłużenie składkowe (JDG),
        poród: ustanie umowy w ciąży, zwolnienie z kodem B
    end note
    Praca_mamy --> Praca_taty: jest tata
    Praca_mamy --> Szczegolne: brak taty → pominięte
    Praca_taty --> Szczegolne

    state "Szczególne sytuacje matki" as Szczegolne
    note right of Szczegolne
        tylko: po porodzie, dziecko żyje, jest tata
        szpital / niezdolność do samodzielnej egzystencji /
        zgon / porzucenie / (matka bez ubezpieczenia) podjęła pracę
    end note
    Szczegolne --> Plan: dziecko żyje i ktoś jest ubezpieczony
    Szczegolne --> Wynik: martwe urodzenie albo nikt nie jest ubezpieczony

    state "Plan urlopów" as Plan
    note right of Plan
        przed porodem 0–6 tyg. (tylko ciąża, mama ubezpieczona)
        przejęcie przez tatę (oboje ubezpieczeni, brak szczególnej sytuacji)
        rodzicielski taty + start (oboje ubezpieczeni)
        ojcowski: start, 1 albo 2 części (tata ubezpieczony, poród / przysposobienie)
        praca w rodzicielskim (tylko pracownicy, ≤ 50%)
        uzupełniający (wcześniak / szpital), kto bierze (gdy oboje)
        81,5% (w ciąży albo ≤ 21 dni od zdarzenia, po terminie – czy złożono)
    end note
    Plan --> Wynik
    Wynik --> Plan: walidacja odrzuciła plan (HTTP 422) – „Popraw plan”
    Wynik --> [*]
```

## 2. Prawo do zasiłku macierzyńskiego (dla każdego rodzica)

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Zdarzenie
    state Zdarzenie <<choice>>
    Zdarzenie --> Porod: poród [porod]
    Zdarzenie --> Przyjecie: przysposobienie / rodzina zastępcza [przyjecie]
    state Przyjecie_wiek <<choice>>
    Przyjecie --> Przyjecie_wiek
    Przyjecie_wiek --> BrakPrawa: dziecko ≥ 14 lat (przysposobienie)<br/>≥ 7 / 10 lat (rodzina zastępcza) [przyjecie_w_limicie]
    Przyjecie_wiek --> Ubezpieczenie: w limicie wieku
    Porod --> Ubezpieczenie

    state Ubezpieczenie <<choice>>
    Ubezpieczenie --> Dlug: ubezpieczenie chorobowe albo urlop wychowawczy w dniu zdarzenia [*_ubezpieczony]
    Ubezpieczenie --> PoUstaniu: mama: umowa ustała w ciąży (upadłość, likwidacja, śmierć pracodawcy,<br/>naruszenie prawa, umowa przedłużona do porodu) [mama_po_ustaniu]
    Ubezpieczenie --> BrakPrawa: brak ubezpieczenia / ulga na start
    PoUstaniu --> Dlug

    state Dlug <<choice>>
    Dlug --> Uprawniony: brak zadłużenia > 1% płacy minimalnej
    Dlug --> Warunkowo: zadłużenie, < 6 mies. od zdarzenia [*_dlug_do_splaty]
    Dlug --> BrakPrawa: niespłacone w 6 miesięcy – przedawnienie [*_dlug_przedawnia]
    Warunkowo --> Uprawniony: spłata całości (wypłata do 60 dni)

    Uprawniony --> [*]
    BrakPrawa --> SwiadczenieRodzicielskie: nikt w rodzinie nie ma prawa
    SwiadczenieRodzicielskie --> [*]: informacja + przekierowanie (gov.pl)
```

Płatnik: ZUS, gdy rodzic sam opłaca składki, płatnik zgłasza ≤ 20 ubezpieczonych albo poród nastąpił
po ustaniu ubezpieczenia; w pozostałych przypadkach pracodawca [`*_platnik`].

## 3. Urlop macierzyński / na warunkach urlopu macierzyńskiego

```mermaid
stateDiagram-v2
    direction TB
    [*] --> Wymiar
    state Wymiar <<choice>>
    Wymiar --> Pelny: dziecko żyje – 20/31/33/35/37 tyg. wg liczby dzieci
    Wymiar --> Martwe: martwe urodzenie albo zgon < 8 tyg. życia<br/>8 tyg., nie krócej niż 7 dni od zgonu
    Wymiar --> Zgon: zgon później – do 7 dni od zgonu
    Wymiar --> Mnogi: poród mnogi, część dzieci zmarła – wymiar wg dzieci żyjących
    Wymiar --> Przyjety: przyjęcie – 20+ tyg. do granicy wieku, min. 9 tyg. [wymiar_na_warunkach_dni]

    Pelny --> PrzedPorodem: ciąża: 0–6 tyg. przed porodem [mama_macierzynski_przed]
    PrzedPorodem --> PoPorodzie
    Pelny --> PoPorodzie

    state PoPorodzie {
        direction LR
        [*] --> Mama14
        Mama14: mama ≥ 14 tyg. (≥ 8 tyg. przy niezdolności)
        Mama14 --> TataReszta: rezygnacja mamy – tata przejmuje resztę [tata_macierzynski]
        Mama14 --> Mama20: mama wykorzystuje całość
        [*] --> Szpital: mama w szpitalu po ≥ 8 tyg.
        Szpital --> TataSzpital: tata na czas pobytu [tata_macierzynski_szpital]
        TataSzpital --> MamaKonczy: wypis – mama kończy [mama_macierzynski_dokonczenie]
        [*] --> ZgonPorzucenie: zgon matki / porzucenie (≥ 8 tyg.)
        ZgonPorzucenie --> TataReszta
    }
    PoPorodzie --> Uzupelniajacy: wcześniak / szpital – 1 tydzień za każdy rozpoczęty tydzień pobytu<br/>(poniżej 28 tyg. lub do 1000 g – do 15 tyg., 28–36 tyg. albo w terminie od 5. do 28. dnia – do 8 tyg.)
    PoPorodzie --> Rodzicielski
    Uzupelniajacy --> Rodzicielski
    Mnogi --> PoPorodzie
    Martwe --> [*]: zasiłek pogrzebowy 7000 zł (informacja)
    Zgon --> [*]
    Przyjety --> Rodzicielski
```

Matka bez ubezpieczenia (UZ art. 29 ust. 9–10): zasiłek przysługuje tacie po dniu zgonu, porzucenia
albo orzeczenia o niezdolności matki, a gdy matka podjęła pracę (≥ ½ etatu) – na czas jej pracy
[`tata_przejecie_dni`].

## 4. Urlop rodzicielski, ojcowski, stawki

```mermaid
stateDiagram-v2
    direction TB
    [*] --> Pula
    Pula: 41 / 43 tyg. (Za życiem 65 / 67, przyjęcie z art. 183 § 3 KP: 38 / 62)
    state Kto <<choice>>
    Pula --> Kto
    Kto --> Oboje: oboje uprawnieni
    Kto --> Jedno: uprawniony tylko jeden rodzic (cała pula – interpretacja)
    Oboje --> Podzial: każdy ma 9 tyg. wyłącznie dla siebie (70% zawsze)<br/>tata ≤ pula − 9 [w_tata_rodzicielski_max]
    Podzial --> Praca
    Jedno --> Praca
    state Praca <<choice>>
    Praca --> ZPraca: pracownik łączy z pracą ≤ 50% – urlop dłuższy, zasiłek proporcjonalnie niższy<br/>(limit 82/86/130/134 tyg.)
    Praca --> BezPracy
    ZPraca --> Termin
    BezPracy --> Termin
    Termin: do końca roku, w którym dziecko kończy 6 lat<br/>(przysposobienie: do 14 lat), najwyżej 5 części

    state Stawka <<choice>>
    Termin --> Stawka
    Stawka --> S100_70: brak wniosku – 100% macierzyński, 70% rodzicielski
    Stawka --> S815: wniosek ≤ 21 dni – 81,5% za całość (9 tyg. drugiego rodzica 70%)
    S815 --> S70: ani dnia rodzicielskiego w 1. roku życia → 70% + wyrównanie macierzyńskiego do 100%
    S100_70 --> [*]
    S815 --> [*]
    S70 --> [*]

    [*] --> Ojcowski: tata ubezpieczony, dziecko żyje, poród / przysposobienie
    Ojcowski: 2 tyg., 100%, do 12 miesięcy życia (przysposobienie: 12 mies. od przyjęcia),<br/>jednorazowo albo 2 części ≥ 1 tydzień, nie w trakcie innego urlopu taty
    Ojcowski --> [*]
```

## 5. Ciąża: zwolnienie lekarskie i ustanie umowy

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Ubezp
    state Ubezp <<choice>>
    Ubezp --> Wyczekiwanie: ubezpieczona
    Ubezp --> Brak: nieubezpieczona – brak zasiłku chorobowego
    state Wyczekiwanie <<choice>>
    Wyczekiwanie --> Zwolnienie: 30 dni (obowiązkowe) / 90 dni (dobrowolne) minęło
    Wyczekiwanie --> Czeka: okres wyczekiwania – ryzyko [r_wyczekiwanie]
    Zwolnienie --> Pracodawca: pracownik – 33 dni w roku (14 po 50. r.ż.), 100%
    Pracodawca --> Zasilek: dalej zasiłek chorobowy 100% (ZUS lub płatnik)
    Zwolnienie --> Zasilek: niepracownik – od 1. dnia
    Zasilek --> Rehab: po 270 dniach – świadczenie rehabilitacyjne (informacja)
    [*] --> Upadlosc: umowa ustała w ciąży – upadłość / likwidacja / śmierć pracodawcy
    Upadlosc --> WysMac: zasiłek w wysokości zasiłku macierzyńskiego do porodu
    WysMac --> [*]: od porodu – zasiłek macierzyński
```

## 6. Terminy i ryzyka (co pilnuje przewodnik)

| Termin | Reguła | Źródło |
|---|---|---|
| Wniosek o urlop macierzyński przed porodem – 14 dni przed | `t_mac_przed` | KP 177 §1¹, RW §2 |
| Wniosek o 81,5% – 21 dni po zdarzeniu | `t_usredniona` | UZ 30a |
| Rezygnacja mamy – 7 dni przed powrotem; wniosek taty – 14 dni | `t_rezygnacja`, `t_tata_macierzynski` | KP 180 §8–9 |
| Urlop uzupełniający – 21 dni przed końcem macierzyńskiego | `t_uzupelniajacy` | KP 180² §4 |
| Urlop rodzicielski – 21 dni przed; łączenie z pracą – 21 dni | `t_rodzicielski_*`, `t_praca_*` | KP 182¹ᵈ, 182¹ᵉ |
| Urlop ojcowski – 7 dni przed; wykorzystać do 12 mies. | `t_ojcowski`, `t_ojcowski_do` | KP 182³ |
| Urlop na warunkach macierzyńskiego – wniosek 7 dni od przyjęcia | `t_na_warunkach` | KP 183 §6 |
| Spłata zadłużenia – 6 miesięcy | `t_dlug_*` | UZ 2a |
| Przedawnienie roszczenia – 6 miesięcy od ostatniego dnia zasiłku | `t_przedawnienie` | UZ 67 |

Pełny katalog reguł z wyrażeniami i podstawą prawną: [reguly.md](reguly.md) (generowany:
`python scripts/gen_rules_doc.py`).

## 7. Interpretacje do potwierdzenia z mentorem

Są skonfigurowane jako reguły, więc można je zmienić w panelu bez wdrożenia:

1. **Cała pula rodzicielskiego dla jedynego uprawnionego rodzica** (`tata_rodzicielski_tyg`,
   `mama_rodzicielski_tyg`). KP 182¹ᵃ §4 mówi o „pracownikach – rodzicach”, UZ 31 ust. 3h
   przewiduje zasiłek rodzicielski taty, gdy matka nie jest ubezpieczona.
2. **Art. 183 §3 KP (9 tygodni / 38 tygodni)** stosujemy, gdy granica wieku dziecka skraca urlop
   na warunkach urlopu macierzyńskiego (`przyjecie_okres_minimalny`).
3. **Termin rodzicielskiego dla rodziny zastępczej** w przypadku z §3 to ukończenie przez dziecko
   14 lat (§4²), w pozostałych przypadkach koniec roku, w którym dziecko kończy 6 lat
   (`rodzicielski_termin`).
4. **Urlop ojcowski przy przysposobieniu**: przepis liczy 12 miesięcy od uprawomocnienia
   postanowienia, a silnik przyjmuje datę przyjęcia dziecka (`ojcowski_termin`).
5. **Kwota świadczenia rodzicielskiego** (podwyższenie z UZ 31 ust. 3a) nie wynika ze źródeł, więc
   parametr `parental_benefit_amount` jest pusty, a reguła `r_podwyzszenie` włączy się po jego
   uzupełnieniu.
6. **Kwoty netto** nie są liczone, bo zaliczka na PIT nie wynika ze źródeł. Wszystkie kwoty są
   brutto.
