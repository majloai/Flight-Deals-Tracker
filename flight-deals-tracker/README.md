# ✈️ Flight Deals Tracker

Automatyczny program śledzący ceny lotów z RZE i KRK, wykrywający okazje
(nowe rekordy najniższej ceny dla danej trasy) i publikujący wyniki jako
stronę internetową (GitHub Pages).

## Jak to działa

1. **GitHub Actions** uruchamia `scripts/fetch_prices.py` codziennie o 6:00 UTC
   (i na żądanie, przycisk "Run workflow" w zakładce **Actions**).
2. Skrypt pobiera oferty z **Travelpayouts API** dla lotnisk i widełek dat
   podanych w `config.yml`, filtruje je i porównuje z historią zapisaną
   w `data/history.json`.
3. Jeśli aktualna cena jest równa lub niższa niż najniższa dotąd
   zaobserwowana dla danej trasy — trasa jest oznaczana jako **okazja**.
4. `scripts/build_page.py` generuje `docs/index.html` z listą okazji
   i tabelą wszystkich śledzonych tras.
5. Zmiany są commitowane z powrotem do repo, a GitHub Pages automatycznie
   publikuje zaktualizowaną stronę.

## Konfiguracja

Edytuj plik [`config.yml`](./config.yml), żeby zmienić:
- lotniska wylotu,
- listę kierunków (pusta lista = szeroki, automatyczny zestaw),
- widełki dat wylotu,
- długość pobytu,
- inne parametry (waluta, liczba przesiadek itd.)

Zmiany wchodzą w życie przy następnym uruchomieniu workflow.

## Jednorazowa konfiguracja repo (do zrobienia raz)

1. **Dodaj token API jako Secret:**
   Settings → Secrets and variables → Actions → New repository secret
   → nazwa: `TRAVELPAYOUTS_TOKEN`, wartość: Twój token z Travelpayouts.

2. **Włącz GitHub Pages:**
   Settings → Pages → Source: wybierz branch `main`, folder `/docs` → Save.
   Po chwili strona będzie dostępna pod adresem podanym w tej sekcji
   (zwykle `https://<twoja-nazwa>.github.io/Flight-Deals-Tracker/`).

3. **Uruchom workflow ręcznie po raz pierwszy:**
   Zakładka Actions → "Update Flight Deals" → Run workflow.
   (Pierwsze uruchomienie tylko buduje bazową historię cen — okazje
   zaczną się pojawiać od drugiego/trzeciego uruchomienia, gdy program
   będzie miał już z czym porównywać nowe ceny.)

## Struktura plików

```
config.yml                     # ustawienia (edytuj tutaj)
requirements.txt                # zależności Python
scripts/fetch_prices.py         # pobiera dane, aktualizuje historię
scripts/build_page.py           # generuje stronę HTML
data/history.json               # baza historyczna cen (rośnie z czasem)
data/latest.json                # wynik ostatniego uruchomienia
docs/index.html                 # strona publikowana przez GitHub Pages
.github/workflows/update.yml    # harmonogram automatyzacji
```
