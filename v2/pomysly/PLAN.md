# Plan Rozwoju i Audyt Architektury – Asystent PWr (v2)

Ten dokument zawiera wizję rozwoju projektu, uporządkowaną według poziomu trudności implementacji oraz aktualnego statusu prac.

### 📋 Zasady kategoryzacji zadań:
1.  **Kolejność**: Zadania są ułożone od najprostszych (P0) do najbardziej złożonych (P5).
2.  **Statusy**:
    - `📅 DO ZROBIENIA` – Zadanie zaplanowane, czeka na rozpoczęcie.
    - `⏳ W TRAKCIE`    – Trwają prace nad implementacją lub dokumentacją techniczną.
    - `✅ ZREALIZOWANE` – Zadanie ukończone (przenoszone do CHANGELOG.md).

---

## 🟢 Priorytet P0 (Stabilność i Weryfikacja) – ✅ ZAKOŃCZONE

### 1. ✅ ZREALIZOWANE: Naprawa skryptów weryfikacyjnych (Windows / Unicode)
*   **Status**: Testy działają stabilnie na Windows (UTF-8, ścieżki bezwzględne).

### 2. ✅ ZREALIZOWANE: Test Diff Tool (Analiza Regresji)
*   **Status**: Narzędzie `v2/tests/test_diff.py` gotowe. baseline.json wygenerowany.

### 3. ✅ ZREALIZOWANE: Wizualny feedback "Thinking" (UI)
*   **Status**: Dodano pulsujący tekst "Szukam informacji..." i odświeżono animację dots.

---

## 🟡 Priorytet P1 (Średnie - Wydajność i Infrastruktura)

### 1. ✅ ZREALIZOWANE: Bezpieczeństwo i Konfiguracja (.env)
*   **Cel**: Usunięcie sekretów z kodu źródłowego.
*   **Szczegóły**: Migracja `ADMIN_TOKEN` oraz ścieżek baz danych do pliku `.env` (python-dotenv).

### 2. 📅 DO ZROBIENIA: Asynchroniczne logowanie statystyk
*   **Cel**: Wykorzystanie `threading` do zapisu danych do SQLite bez blokowania odpowiedzi użytkownika.

### 3. ✅ ZREALIZOWANE: Standaryzacja Importów (PEP 8 Policy)
*   **Status**: Cały projekt (core, app, scripts, tests) przeszedł refaktoryzację importów.

---

## 🟠 Priorytet P2 (Algorytmy i UX: Laboratorium)

### 1. ⏳ W TRAKCIE: Laboratorium Regulaminowe (Tryb Symulacji)
*   **Cel**: Interaktywne badanie wpływu parametrów na wykresach liniowych (Baseline vs Delta).
*   **Specyfikacja techniczna**:
    - **Backend**: Refaktoryzacja `Wyszukiwarka.szukaj`, aby przyjmowała `virtual_params` (ad-hoc).
    - **Obsługiwane parametry**: `synonym_weight` (siła synonimów), `confidence_threshold` (próg pewności), `bm25_k1` oraz `bm25_b` (czułość na długość tekstu).
    - **Frontend (`lab.html`)**: Dashboard z suwakami i Chart.js. Dwie linie na wykresie: szara (oryginalna) i neonowa (symulacja).
    - **Eksport**: Przycisk pobierania aktualnej konfiguracji suwaków do pliku JSON/TXT.

Odniesienie poboczne: [symulacja.md](symulacja.md)

### 2. 📅 DO ZROBIENIA: Poprawa słownika (§ECTS, §Praktyki)
*   **Cel**: Rozbudowa synonimów dla nowych, trudnych paragrafów regulaminu.

---

## 🔴 Priorytet P3 (Złożone - Architektura i Use Cases)

### 1. 📅 DO ZROBIENIA: Refaktoryzacja na Use Cases
*   **Cel**: Separacja logiki biznesowej od Flaska (Folder `domain/use_cases/`).

### 2. 📅 DO ZROBIENIA: Algorytmiczny "Did you mean?"
*   **Cel**: Inteligentne sugestie oparte na Grafie Relacji przy niskiej pewności wyników.

---

## 🔵 Priorytet P5 (Najtrudniejsze - Rozszerzenie Systemu)

### 1. 📅 DO ZROBIENIA: GUI do zarządzania regulaminami (PDF -> JSON)
*   **Cel**: Automatyzacja dodawania nowych dokumentów przez interfejs przeglądarkowy.

---

## 📂 Dokumenty Powiązane
- [PLAN.md](PLAN.md) - Główna mapa drogowa.
- [CHANGELOG.md](../CHANGELOG.md) - Historia zrealizowanych zmian.
- [usprawnienie_pracy.md](usprawnienie_pracy.md) - Instrukcja prywatnej synchronizacji ustawień (Dotfiles).

> [!IMPORTANT]
> Projekt jest rozwijany z **całkowitym wyłączeniem gotowych modeli AI** (No NLP Libraries).
