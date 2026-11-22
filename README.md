# Przewodnik rodzica

Aplikacja dla przyszłych i świeżych rodziców: podpowiada, jakie świadczenia im przysługują
(urlop macierzyński, rodzicielski, ojcowski, zasiłki, becikowe), liczy ich wysokość, rozpisuje urlopy na osi czasu
i prowadzi przez wnioski krok po kroku.

Projekt hackathonowy (HackNation 2026, zadanie ZUS). Nie jest oficjalnym serwisem ZUS. AI było używane wyłącznie
w procesie tworzenia kodu – sama aplikacja nie korzysta z AI i **nie ma OCR** (dane wpisuje się ręcznie albo
pobiera z symulowanego ZUS).

## Spis treści

1. [Szybki start](#szybki-start)
2. [Dokumentacja](#dokumentacja)
3. [Co potrafi aplikacja](#co-potrafi-aplikacja)
4. [Architektura i struktura repozytorium](#architektura-i-struktura-repozytorium)
5. [Silnik reguł i parametry prawne](#silnik-reguł-i-parametry-prawne)
6. [Adresy stron](#adresy-stron)
7. [Konwencje](#konwencje)
8. [Założenia i ograniczenia](#założenia-i-ograniczenia)

## Szybki start

Wymagany Docker z Docker Compose.

```bash
cp .env.example .env    # opcjonalnie – domyślne wartości działają od razu
make up
```

| Adres | Co jest |
| --- | --- |
| http://localhost | aplikacja (w stopce: „Wejście do dema aplikacji”) |
| http://localhost/admin | panel administratora (hasło demo: `admin`, zmienna `ADMIN_TOKEN`) |
| http://localhost/api/docs | dokumentacja API (Swagger) |
| http://localhost/api/health | `{"status":"ok"}` |

Port 80 zajęty? Ustaw `HTTP_PORT=8080` w `.env`.

| Komenda | Działanie |
| --- | --- |
| `make up` / `make down` | uruchamia / zatrzymuje (dane w bazie zostają) |
| `make logs` | logi wszystkich usług |
| `make test` | testy backendu (SQLite w pamięci, bez stosu) |
| `make check-routes` | zgodność tabeli adresów: nginx, `routes.ts`, foldery stron |
| `make seed` | ponowny seed parametrów, reguł i kont demo |
| `make reset-db` | czyści bazę i startuje od zera (po zmianie modelu) |
| `make fmt` | formatowanie i lint backendu (ruff) |
| `make shell-db` | konsola `psql` |

Kod jest podmontowany do kontenerów – zmiany w `backend/app` i `frontend/src` widać bez przebudowy.

### Konta demo i logowanie

`/logowanie` symuluje mObywatela. Można:

- **zalogować się własnym PESEL-em** (dowolny numer z poprawną sumą kontrolną, np. `44051401359`) – konto jest puste,
  dane rodziny wpisuje się w kalkulatorze,
- **wybrać jedno z 3 kont demonstracyjnych** (`backend/app/mocks/personas.py`) z gotowymi danymi z ZUS, wersjami
  roboczymi i wnioskami w różnych statusach: Aneta Nowak (początek ciąży), Karolina Wiśniewska (tuż przed porodem),
  Joanna Zielińska (po porodzie, wnioski rozpatrzone i po terminie).

Bez logowania widać kalkulator, oś czasu i **sugestie** wniosków, ale nie można ich wypełniać ani wysyłać
(przyciski prowadzą do logowania, API zwraca 401).

## Dokumentacja

| Dokument | O czym |
| --- | --- |
| [`docs/instrukcja-uzytkownika.md`](docs/instrukcja-uzytkownika.md) | samouczek dla rodzica: krok po kroku przez cały system |
| [`docs/instrukcja-admina.md`](docs/instrukcja-admina.md) | panel administratora: parametry, reguły, test na profilu |
| [`docs/baza-danych.md`](docs/baza-danych.md) | schemat bazy (diagram ER, tabele, kolumny JSON); generowany: `python scripts/gen_db_schema.py` |
| [`docs/reguly.md`](docs/reguly.md) | katalog reguł; generowany: `python scripts/gen_rules_doc.py` |
| [`docs/maszyna-stanow.md`](docs/maszyna-stanow.md) | scenariusze i maszyna stanów (diagramy Mermaid + PNG w `docs/diagramy/`) |
| [`docs/zrodla-prawne.md`](docs/zrodla-prawne.md) | skąd pochodzą przepisy (6 źródeł konkursu) |
| [`CLAUDE.md`](CLAUDE.md) | konwencje dla asystenta AI używanego przy tworzeniu kodu |

## Co potrafi aplikacja

| Funkcja | Adres | Opis |
| --- | --- | --- |
| Kalkulator | `/kalkulator` | kreator: sytuacja → dziecko → rodzina → praca mamy/taty → szczególne sytuacje → plan → wynik (uprawnienia, kwoty brutto, dokumenty, ryzyka) |
| Oś czasu | `/os-czasu` | urlopy mamy i taty, terminy, złożone wnioski i miesięczne przelewy; linia „Dziś” rozdziela przeszłość (wyszarzona) od przyszłości |
| Moje urlopy i zasiłki | `/moje-swiadczenia` | „Co teraz”, kwoty wypłacone i oczekiwane, wykorzystane i pozostałe dni każdego urlopu, becikowe |
| Wnioski | `/wnioski` | sugestie, formularze zgodne ze wzorami, wersje robocze, podsumowanie i oświadczenie przed wysłaniem, historia statusów |
| Dane z ZUS | `/dane-zus` | symulacja: ubezpieczenie, zadłużenie, e-ZLA, pytanie do PUE, „policz z danych ZUS” |
| Pomoc | `/pomoc` | oficjalne odnośniki i organizacje wsparcia (`frontend/src/content/support.ts`) |
| Panel administratora | `/admin` | parametry prawne, reguły (edycja, historia, test), decyzje płatnika |

Szczegóły działania i zrzuty ekranu: [`docs/instrukcja-uzytkownika.md`](docs/instrukcja-uzytkownika.md).

## Architektura i struktura repozytorium

```
przeglądarka ──► nginx :80 ──┬── /api/*  ──► backend  (FastAPI :8000) ──► PostgreSQL
                             └── /*      ──► frontend (Next.js :3000)
```

Jeden adres dla frontendu i API, więc nie trzeba konfigurować CORS. Polskie adresy działają też bez nginx
(rewrites w `frontend/next.config.ts`, wystarczy do wdrożenia np. na Vercel).

```
├── docker-compose.yml, Makefile, .env.example
├── infra/nginx/default.conf     # /api → backend, reszta → frontend; tłumaczenie URL-i PL ↔ EN
├── scripts/                     # check_routes.py, gen_db_schema.py, gen_rules_doc.py
├── docs/                        # dokumentacja (patrz wyżej)
├── backend/app/
│   ├── main.py                  # FastAPI; przy starcie tworzy tabele i robi seed
│   ├── core/                    # config (env), db (silnik, sesja)
│   ├── models/                  # tabele: legal_parameter, rule, family, draft, application
│   ├── api/                     # endpointy: rules, applications, mocks, admin, admin_rules, scenarios, parameters
│   ├── engine/                  # silnik reguł: expressions, facts, runtime, service, store (bez logiki prawnej)
│   ├── rules/                   # typy API silnika (FamilyProfile, EvaluationResult)
│   ├── forms/                   # definicje formularzy wniosków i wstępne wypełnianie
│   ├── mocks/                   # mObywatel, dane ZUS, e-ZLA, PUE, konta demo (personas)
│   ├── seed/
│   │   ├── parameters_2026.py   # parametry prawne z okresami obowiązywania
│   │   ├── rules/               # reguły jako dane – jeden plik na obszar (macierzyński, rodzicielski, terminy…)
│   │   └── scenarios/           # 15 scenariuszy testowych
│   └── tests/                   # pytest
└── frontend/src/
    ├── app/                     # strony: (guide)/… z ramką zus.pl, admin/ z własnym układem
    ├── components/
    │   ├── calculator/          # form-model (stan, profil), form-steps (kroki), calculator-form, calculator-results
    │   ├── timeline/            # model, style, events (budowa osi), graph, event-details, advice-panel, vertical-timeline
    │   ├── account/             # „Moje urlopy i zasiłki”
    │   ├── applications/, mocks/, admin/, help/, zus/ (ramka), ui/ (shadcn)
    ├── lib/
    │   ├── api/                 # klient API: client, rules, applications, mocks, admin (index re-eksportuje)
    │   ├── routes.ts, nav.ts    # tabela adresów i menu
    │   └── session.ts, last-result.ts, my-benefits.ts, format.ts, …
    └── content/support.ts       # treści strony Pomoc
```

## Silnik reguł i parametry prawne

Reguły nie są w kodzie. Leżą w tabeli `rule` (seed: `backend/app/seed/rules/`) i powstały **wyłącznie** z sześciu
źródeł zadania: Kodeks pracy (KP), ustawa zasiłkowa (UZ), rozporządzenie o dokumentach do zasiłków (RZ),
rozporządzenie o wnioskach (RW), Poradnik ZUS 2026 (PR), załącznik o podstawie wymiaru (ZAL). Każda reguła ma
podstawę prawną i kod źródła. Jedyny wyjątek to becikowe (źródło `SR`, patrz niżej).

Reguła to wyrażenie w prostym, bezpiecznym języku (`app/engine/expressions.py`, polskie nazwy funkcji: `jesli`,
`dodaj_dni`, `param`, `tabela`…) nad danymi rodziny (`facts.py`: `dziecko.*`, `mama.*`, `tata.*`, `plan.*`) i innymi
regułami. Zależności silnik odczytuje sam, liczy reguły w porządku topologicznym i odrzuca cykle.

| Rodzaj | Co robi |
| --- | --- |
| `wartosc` | nazwana wartość (np. `mama_uprawniona`) |
| `okres` | urlop / zasiłek na osi czasu: początek, dni, stawka, osoba, płatnik |
| `swiadczenie` | karta wyniku: status, opis z `{wyrażeniami}`, okresy |
| `dokument`, `termin`, `ryzyko`, `informacja`, `zalozenie` | treści wyniku (termin ma też `late_text_pl` – poradę po terminie) |
| `walidacja` | warunek prawdziwy → plan odrzucony (HTTP 422) |

Liczby z przepisów (tygodnie, stawki, progi) to **parametry** w tabeli `legal_parameter` z okresem obowiązywania.
Gdy przepis się zmienia, dodaje się nowy wiersz – stare sprawy liczą się według starych wartości (złożony wniosek
zapisuje `params_snapshot` i `rules_version`). Kwoty są brutto (podatku nie liczymy, bo nie wynika ze źródeł).

Przelewy: silnik dzieli każdy okres zasiłku na miesiące (kwota proporcjonalna do dni, suma = suma świadczenia),
data przelewu = parametr `payout_day` następnego miesiąca.

## Adresy stron

Foldery i trasy w kodzie są po angielsku, adresy w przeglądarce po polsku; tłumaczy je nginx
(`/kalkulator` → trasa `/calculator`, a `/calculator` przekierowuje 301 na `/kalkulator`).

| Adres | Folder w `frontend/src/app/` | Menu |
| --- | --- | --- |
| `/` | `(guide)/page.tsx` | strona główna |
| `/kalkulator` | `(guide)/calculator/` | Sprawdź uprawnienia i policz zasiłek |
| `/os-czasu` | `(guide)/timeline/` | Plan urlopów – oś czasu |
| `/moje-swiadczenia` | `(guide)/account/` | Moje urlopy i zasiłki |
| `/wnioski` | `(guide)/applications/` | Wnioski |
| `/dane-zus` | `(guide)/zus/` | Dane z ZUS |
| `/pomoc` | `(guide)/help/` | Pomoc i wsparcie |
| `/logowanie` | `(guide)/login/` | Zaloguj przez mObywatel |
| `/admin` | `admin/` | Panel administratora |

Dodając stronę: folder w `src/app/`, wpis w `src/lib/routes.ts`, po jednym wierszu w obu tabelach `map` w nginx,
wpis w `nav.ts`. `make check-routes` sprawdza zgodność.

## Konwencje

- Kod (identyfikatory, pliki, trasy, tabele, komentarze, komunikaty API) jest po angielsku; po polsku jest treść dla
  użytkownika i dokumentacja. Pełne zasady: `CLAUDE.md`.
- Żadnych liczb prawnych w kodzie – tylko `legal_parameter`. Reguły jako dane, silnik bez logiki prawnej.
- Brak migracji: schemat = modele + `create_all`; po zmianie modelu `make reset-db`.
- Do backendu tylko przez `api()` z `frontend/src/lib/api/`; typy odpowiedzi odwzorowują schematy backendu.
- Mobile first (ekrany działają od 390 px). Wygląd zus.pl: tokeny w `frontend/src/app/globals.css`, ramka w
  `components/site-header.tsx`, `components/zus/`, `components/site-footer.tsx`.
- Przed zakończeniem pracy: `make test` i `npm run build` w `frontend/`.

## Założenia i ograniczenia

- **Becikowe** (1 000 zł na dziecko, wniosek do gminy w ciągu 12 mies.) wynika z ustawy o świadczeniach rodzinnych
  (art. 15b) i gov.pl, czyli **spoza sześciu źródeł konkursu**. Jest oznaczone w treści reguły (źródło `SR`) i edytowalne
  w panelu administratora.
- **Dzień przelewu zasiłku** (`payout_day`, domyślnie 10.) to założenie planera, nie przepis; zmienia się w panelu.
- Logowanie mObywatel, dane ZUS, e-ZLA i PUE to **symulacje** – żaden wniosek nie trafia do pracodawcy ani do ZUS.
- Brak OCR: dokumentów się nie skanuje, dane wpisuje się ręcznie lub pobiera z symulowanego ZUS.
- Tożsamość to nagłówek `X-Owner-Id` (mock), nie prawdziwe uwierzytelnianie.
- Logo ZUS w nagłówku (`frontend/public/brand/logo-zus.svg`) pochodzi z oficjalnego pliku udostępnionego do projektu.

## Stack

Next.js (App Router, TypeScript, Tailwind CSS, shadcn/ui) · FastAPI · SQLAlchemy 2 · PostgreSQL 16 · nginx · Docker Compose.
