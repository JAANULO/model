# Plan: Laboratorium Regulaminowe (Tryb Symulacji)

Abyś mógł w pełni zrozumieć i kontrolować "matematyczne serce" projektu, proponuję stworzenie dedykowanego modułu **Laboratorium**, który pozwoli na symulowanie zmian parametrów algorytmu bez wpływania na działanie publicznej wersji asystenta.

## User Review Required

> [!IMPORTANT]
> Tryb symulacji będzie obciążał procesor (uruchamia wiele testów naraz), dlatego zostanie zoptymalizowany pod kątem szybkości poprzez użycie „próbki reprezentatywnej” (np. 30 zróżnicowanych pytań zamiast pełnych 150).

## Proposed Changes

### 1. Rozbudowa Silnika o "Virtual Params" (Backend)
Modyfikacja `v2/core/wyszukiwarka.py`, aby umożliwić przekazywanie parametrów w locie (ad-hoc).

#### [MODIFY] [wyszukiwarka.py](file:///c:/Users/atona/Documents/GitHub/model/v2/core/wyszukiwarka.py)
- Refaktoryzacja metody `szukaj`, aby mogła przyjmować opcjonalny słownik `virtual_params`.
- Obsługa parametrów: `synonym_weight` (siła wpływu synonimów), `confidence_threshold` (częstość "Nie wiem"), `bm25_k1` i `bm25_b`.

### 2. Dashboard Symulacji (Frontend)
Stworzenie nowej strony w panelu administracyjnym.

#### [NEW] [lab.html](file:///c:/Users/atona/Documents/GitHub/model/v2/templates/lab.html)
- **Suwaki (Sliders)**: Do interaktywnej zmiany parametrów (Wagi synonimów, Progi, K1, B).
- **Wykresy Liniowe (Continuous Lines)**:
    - **Porównanie z Baseline**: Wykres będzie zawsze pokazywał dwie linie: białą/szarą (stan "surowy" - oryginalny) oraz neonową (rezultat Twoich zmian na suwakach).
    - **Delta Skuteczności**: Wykazanie różnicy w % trafności względem stanu bazowego.

### 4. System Eksportu i Weryfikacji
- **Eksport JSON/TXT**: Przycisk pozwalający pobrać aktualnie ustawione na suwakach parametry do pliku tekstowego (abyś mógł je później ręcznie wpisać do kodu, jeśli uznasz je za genialne).
- **Modyfikacja test.py**: Umożliwienie skryptowi testowemu przyjmowania parametrów z zewnątrz dla szybkich symulacji.

## Verification Plan

### Automated Tests
- Testowanie, czy zmiana `virtual_params` faktycznie zmienia listę wyników (bez trwałego nadpisywania zmiennych globalnych).

### Manual Verification
- Przejście suwakiem "Waga synonimów" od 0 do 2.0 i obserwacja na wykresie, jak zmienia się liczba punktów trafienia dla pytania o "egzamni" (literówka).

## Open Questions
- Czy preferujesz, aby wykresy były liniowe (ciągłe zmiany) czy słupkowe (porównanie stanów)?
- Czy chciałbyś mieć możliwość „zapisania” najlepszych parametrów z symulatora jako oficjalnych ustawień systemu?
