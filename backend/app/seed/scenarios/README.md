# Scenariusze (E3)

Pliki `S1.json` … `S12.json` to persony zbudowane ręcznie na podstawie rodzajów spraw z `sprawy_wzory*.zip`
(skany – bez OCR; z nazw plików i formularzy wzięto typ świadczenia, dane są przykładowe).
Każdy plik: `id`, `title_pl`, `description_pl`, `tags` i gotowy `profile` rodziny.
Lista: `GET /api/scenarios`, strona: `/przyklady`, test: `test_scenarios_list_and_every_scenario_evaluates`.
Nowa persona = nowy plik `S<n>.json` (numeracja ciągła).
