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
| `POST` http://localhost/api/rules/evaluate | silnik reguł: profil rodziny → uprawnienia, kwoty, oś czasu, ryzyka |

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
│       ├── rules/            # E1 – silnik reguł (czyste funkcje, bez bazy i HTTP) – patrz „Silnik reguł”
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
| `/` | `page.tsx` | strona główna | E9 |
| `/kreator` | `wizard/` | Sprawdź uprawnienia | E4 |
| `/kalkulator` | `calculator/` | Kalkulator | E2 |
| `/os-czasu` | `timeline/` | Oś czasu | E5 |
| `/wnioski` | `applications/` | Wnioski | E6 |
| `/przyklady` | `examples/` | Przykłady | E3 |
| `/logowanie` | `login/` | Zaloguj przez mObywatel | E7 |
| `/admin` | `admin/` | Admin | E8 |

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

## Silnik reguł (E1)

`backend/app/rules/` to czyste funkcje: profil rodziny (`FamilyProfile`) + parametry prawne (`Params`)
→ wynik (`EvaluationResult`). Wywołanie: `POST /api/rules/evaluate?date=RRRR-MM-DD` (data wybiera
wersję parametrów prawnych; domyślnie dziś). Błędny plan (np. 7 tygodni przed porodem) → 422,
brak parametru na dany dzień → 409.

| Moduł | Zawartość |
| --- | --- |
| `models.py` | profil wejściowy (dziecko, rodzice, plan) i typy wyniku |
| `eligibility.py` | ubezpieczenie w dniu porodu, zadłużenie składkowe, płatnik (pracodawca / ZUS) |
| `leaves.py` | wymiary urlopów: macierzyński, uzupełniający, rodzicielski, ojcowski, martwe urodzenie, zgon dziecka, adopcja |
| `money.py` | podstawa wymiaru, kwota za okres (1/30 za niepełny miesiąc), szacunek netto, minimum 1000 zł |
| `planning.py` | walidacja planu i domyślna oś czasu; stawki 100% / 70% / 81,5% |
| `benefits.py` | lista świadczeń z uzasadnieniem, dokumentami, terminami i miejscem złożenia wniosku |
| `risks.py` | ryzyka utraty lub obniżenia świadczeń |

Świadczenia w wyniku: zasiłek chorobowy w ciąży (kod B), zasiłek w wysokości macierzyńskiego,
macierzyński, uzupełniający, rodzicielski, ojcowski, opiekuńczy, a gdy nikt nie ma ubezpieczenia –
świadczenie rodzicielskie. Przy poprawnym wniosku do 21 dni po porodzie silnik porównuje też
warianty „100% + 70%” i „stała 81,5%”.

Wynik zawiera też `deadlines`: ile dni zostało na złożenie każdego wniosku (`days_left`, ujemne = termin
minął) oraz do kiedy trzeba wykorzystać urlopy. Terminy wniosków do pracodawcy są parametrami prawnymi
(`application_lead_days`).

Kalkulator na stronie `/kalkulator` korzysta z tego endpointu. Jego wynik widać też na `/os-czasu` –
pionowej osi w stylu historii commitów (gałąź mamy i taty, każde zdarzenie to punkt). Tata, który nie
ma żadnego zasiłku, nie pojawia się w podsumowaniu ani na osi.

## Kolory

Interfejs używa palety ZUS: zieleń `#007834` (podstawowa), `#006837` (hover), granat `#003B73`,
błękit `#0066B3`, mięta `#E6F4EC` i neutralne szarości. Wartości są w `frontend/src/app/globals.css`.

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

## Rozszerzone obliczenia silnika

- zasiłek opiekuńczy: limity 60/30/14 dni, limit całej rodziny, wiek dziecka, inny domownik, kwota za dni (`care`),
- zasiłek chorobowy w ciąży: wynagrodzenie chorobowe 33/14 dni, zasiłek ZUS, okres 270 dni, kwota za okres,
- urlop rodzicielski w częściach z datami (`plan.parental_blocks`, do 5 części na rodzica, rodzice mogą korzystać równolegle),
- urlop ojcowski z datami startu (`plan.paternity_starts`, termin 12 miesięcy),
- podstawa z historii miesięcy (`monthly_bases`, także krótsza niż 12 miesięcy),
- wyjątki ubezpieczenia: urlop wychowawczy, umowa na czas określony przedłużona do porodu.

## Scenariusze (E3)

Dwanaście person w `backend/app/seed/scenarios/` (`GET /api/scenarios`), strona `/przyklady` liczy wybraną
sytuację silnikiem i zapisuje wynik dla osi czasu.

## Kreator (E4)

`/kreator` – pytania krok po kroku (sytuacja, data, szczegóły dziecka, mama, tata, plan urlopów), na końcu wynik z silnika
(`/api/rules/evaluate`) i przejście do osi czasu lub kalkulatora. Używa tego samego formularza i `buildProfile` co kalkulator.

## Oś czasu ze szczegółami (E5)

`/os-czasu`: przy każdym urlopie i terminie przycisk „Szczegóły” rozwija kwoty, płatnika, miejsce złożenia wniosku,
termin, dokumenty, uzasadnienie i podstawę prawną; filtr Oboje / Mama / Tata pokazuje gałąź wybranego rodzica.

## Wnioski (E6)

`/wnioski`: po wyliczeniu (kalkulator, kreator lub przykład) strona podpowiada wnioski do złożenia i wypełnia je danymi
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

`/admin` (hasło: zmienna `ADMIN_TOKEN`, domyślnie `admin` – zmień poza środowiskiem lokalnym).

- **Parametry prawne:** wyszukiwanie, historia wersji, „Zmień” = nowa wersja od wybranej daty (musi być późniejsza niż
  obecna). Poprzednia wersja kończy się dzień wcześniej, dawne sprawy liczą się według dawnych przepisów, a kalkulator
  korzysta z nowej wartości od razu. Nowa wartość musi mieć ten sam typ i klucze co poprzednia. Wersje dodane w panelu
  można usunąć (poprzednia otwiera się ponownie); wersje z seedu zostają.
- **Seed a panel:** klucz, który ma wersję spoza seedu, jest pomijany przy starcie – seed nie nadpisuje zmian administratora.
- **Wnioski:** lista wszystkich złożonych wniosków i zmiana statusu z notatką (obieg po stronie płatnika).
- API: `GET /api/admin/parameters`, `POST /api/admin/parameters/{key}/versions`,
  `DELETE /api/admin/parameters/{key}/versions/{valid_from}`, `GET /api/admin/applications`,
  `POST /api/admin/applications/{id}/status` (nagłówek `X-Admin-Token`).
