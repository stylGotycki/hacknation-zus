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
│       ├── rules/            # E1 – silnik reguł (czyste funkcje, bez bazy i HTTP)
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

## Parametry prawne

Żadna liczba z przepisów (tygodnie urlopu, stawki, progi) nie jest wpisana w kod.
Wszystkie leżą w tabeli `legal_parameter` z okresem obowiązywania (`valid_from`/`valid_to`).
Gdy przepis się zmienia, dodajemy nowy wiersz – stare sprawy liczą się według starych wartości.
Seed: `backend/app/seed/parameters_2026.py` (dla przykładu jest też płaca minimalna z 2025 r.).

## Stack

Next.js (App Router, TypeScript, Tailwind CSS, shadcn/ui) · FastAPI · SQLAlchemy 2 ·
PostgreSQL 16 · nginx · Docker Compose.
