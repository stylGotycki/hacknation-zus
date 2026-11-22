# Scenariusz filmu demonstracyjnego (ok. 2:10)

Film nagrywa skrypt `scripts/demo/record_demo.py` (Playwright): uruchamia przeglądarkę, klika w aplikację i rysuje
napisy na ekranie (pomarańczowa kropka pokazuje kursor). Nie wymaga montażu.

```bash
make up                                   # albo: uruchom backend i frontend lokalnie
pip install playwright && playwright install chromium
python scripts/demo/record_demo.py        # -> scripts/demo/out/demo.mp4 (i demo.webm)
PACE=1.4 python scripts/demo/record_demo.py   # wolniej (więcej czasu na napisy / lektora)
BASE_URL=http://localhost python scripts/demo/record_demo.py
```

Konto w filmie: Karolina Wiśniewska (konto demonstracyjne, tuż przed porodem). Zmiana konta: tekst `Karolina`
w skrypcie. Napisy to pierwszy argument `say(...)` – edytuje się je w jednym miejscu. Jeśli nagrywasz głos, zostaw
napisy włączone (hałas na hackathonie) i czytaj poniższy tekst; `PACE` dopasuje długość.

| Czas | Scena | Napis na ekranie | Tekst dla lektora (opcjonalnie) |
| --- | --- | --- | --- |
| 0:00 | Strona startowa | Przewodnik rodzica: jedno miejsce na urlopy, zasiłki i wnioski dla świeżych rodziców | Rodzice dostają chaos: urlopy, zasiłki, wnioski, terminy. Przewodnik zbiera je w jednym miejscu. |
| 0:08 | Strona startowa | Wersja demonstracyjna: dane są symulowane, aplikacja nie ma AI ani OCR | To demo – dane są symulowane, a sama aplikacja nie używa AI ani OCR. |
| 0:14 | Stopka → logowanie | W stopce jest wejście do dema z gotowymi kontami; PESEL albo konto demo | W stopce jest wejście do dema. Można zalogować się własnym PESEL-em albo wybrać konto z gotowymi danymi. |
| 0:30 | Dane z ZUS | Dane o ubezpieczeniu pobieramy z symulowanego ZUS – nic nie trzeba przepisywać | Dane o ubezpieczeniu i podstawie wymiaru pobieramy z symulowanego ZUS – bez przepisywania. |
| 0:50 | Wynik | Silnik reguł liczy uprawnienia i kwoty według przepisów z dnia wyliczenia | Silnik reguł liczy uprawnienia i kwoty według przepisów z dnia wyliczenia. |
| 1:00 | Oś czasu | Pomarańczowa linia pokazuje dziś, to co minęło jest wyszarzone | Na osi czasu widać wszystko: urlopy mamy i taty, terminy, przelewy. Linia „dziś” oddziela przeszłość od przyszłości. |
| 1:12 | Szczegóły punktu | Każdy punkt ma szczegóły: kwoty, płatnika, dokumenty i podstawę prawną | Każdy punkt ma kwoty, płatnika, dokumenty i podstawę prawną. |
| 1:22 | Moje urlopy i zasiłki | Co zrobić teraz i do kiedy; ile wypłacono; ile dni wykorzystano i zostało | Ta strona odpowiada na pytanie „co teraz?”: terminy, pieniądze, wykorzystane i pozostałe dni urlopu. |
| 1:40 | Wnioski | System podpowiada, co złożyć, do kogo i w jakim terminie; formularz zgodny ze wzorem | Wnioski wypełniają się danymi z wyniku, są zgodne ze wzorami, a przed wysłaniem jest podsumowanie i oświadczenie. |
| 1:55 | Panel administratora | Liczby z przepisów i reguły to dane, nie kod; zmiana przepisu bez wdrożenia | Przepisy to dane. Gdy się zmienią, administrator zmienia parametr albo regułę – bez programisty i bez wdrożenia. |
| 2:08 | Zakończenie | Przewodnik rodzica – od pierwszego pytania do złożonego wniosku | Od pierwszego pytania do złożonego wniosku. Dziękujemy! |

Czasy są orientacyjne (zależą od szybkości aplikacji i `PACE`). Film pokazuje wejście do dema, kalkulację z danych ZUS, oś czasu,
konto, wniosek (wersja robocza → podsumowanie → wysłanie) i administratora; reszta (kalkulator ręczny, PESEL, becikowe)
można dokleić drugim nagraniem, np. `PACE=1.4`.
