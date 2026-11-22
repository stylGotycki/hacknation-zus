# Przewodnik rodzica

Aplikacja dla przyszłych i świeżych rodziców: podpowiada, jakie świadczenia im przysługują
(urlop macierzyński, rodzicielski, ojcowski, zasiłki), liczy ich wysokość, rozpisuje urlopy
na osi czasu i prowadzi przez wnioski krok po kroku.

Projekt hackathonowy (HackNation, zadanie ZUS). Nie jest oficjalnym serwisem ZUS.
AI było używane wyłącznie w procesie tworzenia kodu – sama aplikacja nie korzysta z AI.

## Uruchomienie

Wymagany Docker z Docker Compose.

```bash
cp .env.example .env    # opcjonalnie – domyślne wartości działają od razu
make up
```

| Adres | Co jest |
| --- | --- |
| http://localhost | aplikacja |
| http://localhost/api/docs | dokumentacja API (Swagger) |
| http://localhost/api/health | `{"status":"ok"}` |
| http://localhost/api/parameters?date=2026-11-21 | parametry prawne na dany dzień |
| `POST` http://localhost/api/rules/evaluate | silnik reguł (reguły z bazy): profil rodziny → uprawnienia, kwoty, oś czasu, terminy, ryzyka |

Port 80 zajęty? Ustaw `HTTP_PORT=8080` w `.env` i otwórz http://localhost:8080.

### Komendy

| Komenda | Działanie |
| --- | --- |
| `make up` | buduje i uruchamia wszystko |
| `make down` | zatrzymuje (dane w bazie zostają) |
| `make logs` | logi wszystkich usług |
| `make test` | testy backendu |
| `make check-routes` | sprawdza, czy tabela adresów w nginxie, `routes.ts` i foldery stron są zgodne |
| `make seed` | ponowny seed parametrów prawnych |
| `make reset-db` | czyści bazę i startuje od zera |
| `make fmt` | formatowanie i lint backendu (ruff) |
| `make shell-db` | konsola `psql` |

Kod jest podmontowany do kontenerów – zmiany w `backend/app` i `frontend/src` widać od razu,
bez przebudowy. Przebudowa (`make up`) jest potrzebna tylko po zmianie zależności.

## Architektura

```
przeglądarka ──► nginx :80 ──┬── /api/*  ──► backend  (FastAPI :8000) ──► PostgreSQL
                             └── /*      ──► frontend (Next.js :3000)
```

Jeden adres dla frontendu i API, więc nie trzeba konfigurować CORS.

nginx tłumaczy też adresy stron: użytkownik widzi polskie URL-e (`/kalkulator`), a aplikacja
Next.js ma trasy po angielsku (`/calculator`). Szczegóły w sekcji „Adresy stron”.

## Struktura repozytorium

```
├── docker-compose.yml        # 4 usługi: db, backend, frontend, nginx (tryb deweloperski)
├── Makefile                  # skróty komend
├── .env.example              # zmienne środowiskowe z bezpiecznymi wartościami domyślnymi
├── CLAUDE.md                 # konwencje dla asystenta AI używanego przy tworzeniu kodu
├── infra/nginx/default.conf  # routing: /api → backend, reszta → frontend + tłumaczenie URL-i PL ↔ EN
├── scripts/check_routes.py   # pilnuje zgodności tabeli adresów (make check-routes)
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml        # zależności i konfiguracja pytest/ruff
│   └── app/
│       ├── main.py           # aplikacja FastAPI; przy starcie tworzy tabele i robi seed
│       ├── core/             # config.py (ustawienia z env), db.py (silnik, sesja, Base)
│       ├── models/           # tabele SQLAlchemy: legal_parameter, family, application, draft
│       ├── api/              # endpointy: health.py, parameters.py
│       ├── engine/           # E1 – silnik reguł: język wyrażeń, fakty, runtime, serwis
│       ├── rules/            # typy API silnika (FamilyProfile, EvaluationResult)
│       ├── mocks/            # E7 – mObywatel, dane ZUS, e-ZLA, PUE
│       ├── seed/             # parametry prawne 2026 + (E3) scenariusze ze spraw
│       └── tests/            # pytest na SQLite w pamięci
└── frontend/
    ├── Dockerfile            # etapy: dev (hot reload) i prod (standalone)
    ├── components.json       # konfiguracja shadcn/ui (`npx shadcn add <komponent>`)
    └── src/
        ├── app/              # strony (App Router) – jeden folder = jeden adres URL
        ├── components/       # nagłówek, stopka, placeholder; ui/ = komponenty shadcn
        └── lib/              # routes.ts (tabela adresów), nav.ts (menu), api.ts (klient API), utils.ts
```

## Adresy stron

Foldery i trasy w kodzie są po angielsku, a adresy widoczne w przeglądarce – po polsku.
Tłumaczy je nginx (`infra/nginx/default.conf`):

- wpisujesz `/kalkulator` → nginx serwuje stronę z trasy `/calculator`, adres w przeglądarce
  się nie zmienia,
- wpisujesz `/calculator` → nginx przekierowuje (301) na `/kalkulator`, więc każda strona
  ma jeden kanoniczny adres.

| Adres w przeglądarce | Trasa i folder w `frontend/src/app/` | Nazwa w menu | Epik |
| --- | --- | --- | --- |
| `/` | `(guide)/page.tsx` | strona główna | E9 |
| `/kalkulator` | `(guide)/calculator/` | Sprawdź uprawnienia i policz zasiłek | E2/E4 |
| `/os-czasu` | `(guide)/timeline/` | Oś czasu | E5 |
| `/wnioski` | `(guide)/applications/` | Wnioski | E6 |
| `/dane-zus` | `(guide)/zus/` | Dane z ZUS | E7 |
| `/pomoc` | `(guide)/help/` | Pomoc i wsparcie | – |
| `/logowanie` | `(guide)/login/` | Zaloguj przez mObywatel | E7 |
| `/admin` | `admin/` (własny układ) | Panel administratora | E8 |

Adresy API (`/api/...`) zostają po angielsku.

Dodając stronę, trzeba zmienić trzy miejsca: folder w `src/app/`, wpis w `src/lib/routes.ts`
oraz po jednym wierszu w obu tabelach (`map`) w pliku nginx. `make check-routes` sprawdza,
czy się zgadzają.

## Język w projekcie

Kod jest po angielsku: nazwy zmiennych, plików, folderów, adresów URL, tabel i kolumn,
komentarze, komunikaty błędów API i logi. Wyjątek: publiczne adresy stron są po polsku
(tłumaczy je nginx). Po polsku jest tylko treść dla użytkownika:
napisy w interfejsie, opisy parametrów, podstawy prawne, dokumentacja.
Pełna zasada jest w `CLAUDE.md`.

## Silnik reguł (E1) – reguły jako dane

Reguły nie są w kodzie. Leżą w tabeli `rule` (seed: `backend/app/seed/rules_2026.py`, 191 reguł) i powstały
**wyłącznie** z sześciu źródeł zadania: Kodeks pracy (KP), ustawa zasiłkowa (UZ), rozporządzenie o dokumentach do
zasiłków (RZ), rozporządzenie o wnioskach (RW), Poradnik ZUS 2026 (PR), załącznik o podstawie wymiaru (ZAL). Każda
reguła ma podstawę prawną i kod źródła. Liczby z przepisów są parametrami (`legal_parameter`), reguły tylko je czytają.

Reguła to wyrażenie w prostym, bezpiecznym języku (`app/engine/expressions.py`, polskie nazwy funkcji:
`jesli`, `dodaj_dni`, `tygodnie`, `param`, `tabela`…) nad danymi rodziny (`app/engine/facts.py`: `dziecko.*`,
`mama.*`, `tata.*`, `sytuacja_matki.*`, `plan.*`) i innymi regułami. **Zależności silnik odczytuje sam** z nazw
w wyrażeniach, liczy reguły w porządku topologicznym i odrzuca cykle (`app/engine/runtime.py`).

| Rodzaj | Co robi |
| --- | --- |
| `wartosc` | nazwana wartość (np. `mama_uprawniona`, `wymiar_macierzynski_dni`) |
| `okres` | urlop / zasiłek na osi czasu: początek, liczba dni, stawka, praca, osoba, płatnik |
| `swiadczenie` | karta wyniku: status, opis z `{wyrażeniami}`, okresy |
| `dokument`, `termin`, `ryzyko`, `informacja`, `zalozenie` | treści wyniku |
| `walidacja` | warunek prawdziwy → plan odrzucony (HTTP 422 z komunikatem) |

`POST /api/rules/evaluate` czyta reguły i parametry z bazy (`app/engine/service.py` → `EvaluationResult`).
Kwoty są brutto (podstawa − 13,71%, płaca minimalna dla pełnego etatu, limit 23 550 zł dla niepracowników, 1/30 za dzień).
Netto nie liczymy, bo podatek nie wynika ze źródeł.

Scenariusze i maszyna stanów: [`docs/maszyna-stanow.md`](docs/maszyna-stanow.md) (diagramy Mermaid + PNG w
`docs/diagramy/`). Katalog reguł: [`docs/reguly.md`](docs/reguly.md) (`python scripts/gen_rules_doc.py`).

## Panel administratora (`/admin`, hasło demo `admin`)

Osobna, prosta strona (bez układu przewodnika), zakładki:

- **Parametry i stawki** – zmiana wartości od dziś lub od daty wejścia w życie; złożone wnioski zachowują parametry z dnia złożenia.
- **Reguły** – lista z wyszukiwarką, edycja wyrażeń, „Sprawdź” (walidacja całego zestawu: nazwy, parametry, cykle),
  zapis z powodem zmiany, historia, wyłączenie, przywrócenie wersji ze źródeł, nowe reguły.
- **Słownik danych** – dane rodziny, funkcje, parametry i rodzaje reguł.
- **Zależności** – z czego korzysta reguła i na co wpływa.
- **Test na profilu** – persona albo JSON → wynik i wartości wszystkich reguł.
- **Wnioski** – decyzje płatnika.

API: `GET|POST /api/admin/rules`, `PUT|DELETE /api/admin/rules/{kod}`, `POST /api/admin/rules/validate`,
`POST /api/admin/rules/{kod}/reset`, `GET /api/admin/rules/{kod}/history`, `GET /api/admin/rules/dictionary`,
`GET /api/admin/rules/graph`, `POST /api/admin/rules/test`. Złożony wniosek zapisuje `rules_version`.

## Kalkulator krok po kroku

`/kalkulator` to jeden kreator: sytuacja → dziecko → rodzina → praca mamy → praca taty → szczególne sytuacje → plan → wynik.
Kroki, które nie dotyczą rodziny, są pomijane: bez taty nie ma pytań o podział, martwe urodzenie i zgon dziecka da się
wskazać tylko po porodzie, a plan nie pojawia się przy martwym urodzeniu ani gdy nikt nie jest ubezpieczony. Wynik
widać też na `/os-czasu` (każde zdarzenie ma ikonę, kliknięcie kropki otwiera szczegóły wniosku).

## Wygląd: osobna aplikacja w stylu zus.pl

Przewodnik to osobna aplikacja (własna nazwa w nagłówku, bez menu głównego zus.pl), ale wygląda jak serwis ZUS.
Wartości zmierzone na zrzutach zus.pl (listopad 2026) są w `frontend/src/app/globals.css`:

- font Lato (`@fontsource/lato`, bez pobierania z Google przy buildzie),
- zieleń `#007834` (aktywna pozycja menu bocznego, stopka), zieleń linków `#11783b`,
  granat `#00416e` (przyciski dostępności i obrysowane), pomarańcz `#fab856` (przycisk logowania),
  linie `#e7e7e7`, pas okruszków `#f5f5f5`, szare ikony treści `#777777`,
- kontener 1200 px, menu boczne 300 px z zieloną linią 7 px, okruszki 52 px.

Ramka: `components/site-header.tsx` (pasek „wersja demonstracyjna”, logo + nazwa, przyciski),
`components/zus/guide-frame.tsx` (okruszki + menu boczne + treść), `components/site-footer.tsx` (zielona stopka),
`components/zus/page-heading.tsx` (ikona + H1 na każdej stronie). Przyciski „Powiększ tekst” i „Wysoki kontrast”
działają naprawdę.

**Logo:** w repo jest neutralny placeholder `frontend/public/brand/logo-zus.svg`. Podmień go oficjalnym plikiem:

```bash
curl -o frontend/public/brand/logo-zus.svg https://www.zus.pl/o/portal-theme/img/logo/logo_zus_darker_with_text.svg
```

Strona nigdzie nie zbiera loginów ani haseł: logowanie mObywatel to wybór osoby testowej.

## Parametry prawne

Żadna liczba z przepisów (tygodnie urlopu, stawki, progi) nie jest wpisana w kod.
Wszystkie leżą w tabeli `legal_parameter` z okresem obowiązywania (`valid_from`/`valid_to`).
Gdy przepis się zmienia, dodajemy nowy wiersz – stare sprawy liczą się według starych wartości.
Seed: `backend/app/seed/parameters_2026.py` (dla przykładu jest też płaca minimalna z 2025 r.).

## Stack

Next.js (App Router, TypeScript, Tailwind CSS, shadcn/ui) · FastAPI · SQLAlchemy 2 ·
PostgreSQL 16 · nginx · Docker Compose.


## Źródła danych prawnych

Opis i linki (ELI, API Sejmu, zus.pl, gov.pl) w [`docs/zrodla-prawne.md`](docs/zrodla-prawne.md).

## Osoby testowe (E3)

Piętnaście person w `backend/app/seed/scenarios/` (`GET /api/scenarios`) to osoby do wyboru w symulowanym logowaniu
mObywatel – ich dane trafiają do „Dane z ZUS” i kalkulatora. Osobnej strony z przykładowymi wyliczeniami nie ma.

## Oś czasu ze szczegółami (E5)

`/os-czasu`: grube linie (gałąź rodziny, mamy i taty), każde zdarzenie ma ikonę w kropce: poród, macierzyński,
uzupełniający, rodzicielski, ojcowski, praca/powrót, termin wniosku, „wykorzystaj do”, złożony wniosek.
Kliknięcie kropki otwiera szczegóły: wniosek do złożenia (do kogo, termin, „Wypełnij wniosek”) albo status
złożonego wniosku z historią, a pod spodem kwoty, płatnik, dokumenty i podstawa prawna. Filtr Oboje / Mama / Tata.

## Wnioski (E6)

`/wnioski`: po wyliczeniu (kalkulator albo „Dane z ZUS”) strona podpowiada wnioski do złożenia i wypełnia je danymi
z wyniku. Pracownik dostaje wnioski o urlopy (macierzyński, rodzicielski, ojcowski – adresat pracodawca), pozostali
rodzice – uproszczony ZAM do ZUS. Wersje robocze zapisują się same, wysłany wniosek ma historię statusów
(`submitted` → `in_progress` → `decided`; kolejny etap symuluje przycisk w demo).

- Definicje formularzy: `backend/app/forms/definitions.py` (klucze po angielsku, teksty po polsku).
- API: `GET /api/forms`, `POST /api/applications/suggestions`, `GET|PUT|DELETE /api/drafts`,
  `GET|POST /api/applications`, `POST /api/applications/{id}/advance`.
- Tożsamość to na razie nagłówek `X-Owner-Id` z losowym identyfikatorem przeglądarki; mock mObywatel (E7) ją zastąpi.

## Mocki systemów zewnętrznych (E7)

Wszystko to symulacja na danych przykładowych, wyprowadzonych z 12 person (E3).

- `/logowanie` – mock mObywatel: wybór osoby, ekran potwierdzenia, sesja w przeglądarce (nagłówek pokazuje imię i „Wyloguj”).
  Logowanie ustawia `X-Owner-Id` (`mobywatel-S<n>`), więc wnioski i wersje robocze są osobne dla każdej osoby.
- `/dane-zus` – „Pobierz dane z ZUS”: poświadczenie ubezpieczenia z historią podstawy, zaświadczenie o zadłużeniu
  (na dzień powstania prawa do świadczenia), lista e-ZLA, pytanie do PUE/eZUS oraz „Policz uprawnienia z danych ZUS”.
- API: `GET /api/mock/citizens`, `POST /api/mock/mobywatel/login`, `GET /api/mock/zus/{id}/insurance|debt-certificate|ezla|profile`,
  `POST /api/mock/pue/question`. Kod: `backend/app/mocks/data.py`, `backend/app/api/mocks.py`.

## Panel administratora (E8)

`/admin` (hasło: zmienna `ADMIN_TOKEN`, domyślnie `admin` – zmień poza środowiskiem lokalnym). Wszystko po polsku.

- **Parametry:** pogrupowane (stawki, urlopy, podstawa i kwoty, terminy…), jedna linia na parametr: polska nazwa,
  wartość z jednostką („20 tyg.”, „81,5%”, „1 dziecko: 20 tyg. · 2 dzieci: 31 tyg.”), data, przycisk „Zmień”.
  Edycja w wierszu: jedno pole liczbowe na wartość (tabele – jedno na wiersz), procenty wpisuje się jako procenty.
  Nazwy, grupy, jednostki i opisy kluczy tabel są w bazie (kolumny `label_pl`, `group_pl`, `unit`, `value_labels`,
  seed: `backend/app/seed/parameter_labels.py`).
- **Zmiany dotyczą nowych wniosków:** zapis tworzy wersję od dziś (druga zmiana tego samego dnia ją nadpisuje);
  opcjonalnie od późniejszej daty, gdy przepis wejdzie w życie później. Wstecz nie można. Każdy złożony wniosek
  zapisuje parametry z dnia złożenia (`application.params_snapshot`), więc późniejsza zmiana go nie dotyka.
  Historia zmian i „cofnij tę zmianę” przy każdym parametrze.
- **Wnioski:** tabela złożonych wniosków ze zmianą statusu i notatką (obieg po stronie płatnika).
- Po zmianie modelu: `make reset-db`.

## Strona startowa i pomoc (E9)

- **Strona startowa** (`/`) – hasło, obietnice produktu, ścieżka w czterech krokach (przykładowa sprawa → ubezpieczenie
  w symulowanym ZUS → kalkulator → wnioski), kafelki wszystkich narzędzi i odnośnik do pomocy.
- **Pomoc i wsparcie** (`/pomoc`, folder `src/app/help`) – oficjalne odnośniki (ZUS, MRPiPS – urlop rodzicielski, PIP –
  rodzicielstwo, dodatkowy urlop dla rodziców wcześniaków, zmiany po stracie dziecka, rejestr stanu cywilnego na gov.pl)
  oraz przykładowe organizacje niekomercyjne: po stracie dziecka lub ciąży, dla rodziców wcześniaków i dzieci
  w szpitalu, dla rodzin ciężko chorych dzieci. Treść jest w jednym pliku: `frontend/src/content/support.ts`.
  Dane kontaktowe się zmieniają, dlatego strona odsyła do stron organizacji i KRS, a nie podaje telefonów.
- **Symulowany wniosek o odpis aktu urodzenia** – nowy formularz `civil_registry_extract` (adresat: urząd stanu cywilnego),
  dostępny z listy wniosków i bezpośrednio przez `/wnioski?form=civil_registry_extract`. Nic nie trafia do urzędu.
