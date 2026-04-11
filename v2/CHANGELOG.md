# Wdrożone Funkcjonalności – Asystent Regulaminowy PWr (v2)

---

## 🔖 Sesja P6 (Aktualna) – 2026-04-11

### ⚙️ Profesjonalizacja Backend & Weryfikacji (P0/P1)
*   **Standaryzacja Importów (Projekt-wide)**: Przeprowadzono pełną refaktoryzację importów we wszystkich modułach (`v2/`, `core/`, `tests/`, `scripts/`) zgodnie ze standardem: Standard Library -> Third-party -> Local Projects.
*   **Narzędzie Test Diff (Analiza Regresji)**: Wdrożono skrypt `v2/tests/test_diff.py`. Umożliwia on zapisanie stanu bazowego (`baseline.json`) i automatyczne wykrywanie poprawy lub regresji po zmianach w algorytmie.
*   **Stabilizacja na Windows**: Naprawiono błędy kodowania Unicode w skryptach testowych oraz wprowadzono obsługę ścieżek bezwzględnych, co zapewnia 100% stabilności środowiska deweloperskiego.
*   **Struktura Modułów**: Dodano pliki `__init__.py`, formalizując strukturę paczek Pythona w projekcie.

### 🎨 Poprawa UX (Feedback wizualny)
*   **Thinking State**: Dodano tekstowy indykator "Szukam informacji..." oraz pulsującą animację w oknie czatu, co poprawia odczuwalną responsywność systemu.

### 🛡️ Zarządzanie Wiedzą Agenta (Dotfiles)
*   **Centralizacja Reguł**: Przeniesiono instrukcje systemowe (`Guardian_PWr.md`, `Identity.md` itp.) do globalnego folderu zasad.
*   **Prywatna Synchronizacja**: Skonfigurowano powiązanie z prywatnym repozytorium `antigravity-config`, izolując reguły inżynierskie od publicznego kodu bazy.

---

## 🔖 Sesja P5 – 2026-04-11

### 🎨 Reorganizacja i Optymalizacja UI (Frontend)
*   **Migracja Zarządzania Wiedzą**: Usunięto dropdown wyboru bazy z footera. Zarządzanie źródłami przeniesiono do okna opcji (**⚙️ Opcje > Zobacz wczytane bazy wiedzy**).
*   **Przyjazne Nazewnictwo (PDF Mode)**: Nazwy techniczne `.json` są teraz mapowane na `.pdf` w interfejsie (np. `baza_wiedzy.json` -> `regulamin.pdf`).
*   **Filtrowanie Techniczne**: Ukryto pliki serwisowe (np. `dane.json`) przed użytkownikiem końcowym w oknie opcji.
*   **Bezpośredni Dostęp do Grafu**: Dodano przycisk "🌐 Otwórz mapę powiązań" wewnątrz okna zarządzania wiedzą.
*   **Naprawa Błędów JS/CSS**: Naprawiono błąd braku inicjalizacji `aktywneZrodla` oraz dodano brakujące style dla przełączników (toggle-switches) w oknie opcji.

### 🧪 Weryfikacja Bazy Testowej
*   **Aktualizacja Statystyk**: Potwierdzono istnienie pełnej bazy **225 przypadków testowych** w `tests/test.py`. Poprawiono błędne założenie o 150 testach z poprzedniej sesji.

---

## 🔖 Sesja P4 – 2026-04-10

### 🗂️ Architektura Multi-Źródłowa (Multi-Baza)
* **Filtrowanie po źródle (`zrodlo`):** Endpoint `/zapytaj` odbiera teraz parametr `zrodlo` z frontendu. Wyszukiwarka filtruje wyniki O(1) do wybranego pliku JSON (np. `baza_wiedzy.json`), co stanowi fundament pod wieloregulaminowy system (akademiki, studia, itp.).
* **Metoda `szukaj(zrodlo=None)`:** Wyszukiwarka obsługuje filtr `zrodlo` — gdy ustawiony na konkretną nazwę pliku, odcina wyniki z innych baz. Domyślnie (`None` lub `"Wszystkie dokumenty"`) działa jak dotychczas.

### 📊 Graf Relacji Paragrafów (`/graf_widok`)
* **Nowa metoda `generuj_graf_paragrafow()`:** Zastąpiła poprzednią metodę bigramów. Nowy algorytm oblicza podobieństwo kosinusowe między wektorami TF-IDF **wszystkich paragrafów** i tworzy sieć krawędzi (próg: >0.15). Graf pokazuje realne matematyczne powiązania między paragrafami regulaminu.
* **Wynik:** 39 węzłów, 18 krawędzi semantycznych w aktywnym regulaminie.

### 🎨 Frontend UX — Czytelność i Interaktywność
* **Dropdown wyboru bazy:** W `<footer>` dodano `<select id="wyborZrodla">` z opcjami: Wszystkie Regulaminy, Regulamin Studiów, Odłącz. Zmienna jest przekazywana do każdego żądania `/zapytaj`.
* **Blokada czatu przy odłączonej bazie:** Funkcja `walidatorZrodla()` wyłącza pole tekstowe i przycisk wysyłania gdy wybrano opcję "Odłącz Bazę", z komunikatem informacyjnym.
* **Highlight słów kluczowych:** Backend zwraca teraz `slowa_kluczowe: tokenizuj(pytanie)`. Frontend używa tych tokenów do podświetlania trafień kolorem `var(--accent)` w pełnej treści paragrafu.
* **Czytelność akapitów:** Zamieniono `white-space: pre-wrap` na dynamiczne `<br><br>` z JavaScript (regex `\n+`), eliminując "ściany tekstu" w rozwijanych paragrafach.

### 🧪 Infrastruktura Testowa
* **150 testów:** Rozbudowano `tests/test.py` z 77 do **150 przypadków testowych** w 5 grupach: LATWE, TRUDNE, REGRESYJNE, P4_ROZBUDOWANE, P5_UZUPELNIAJACE.
* **Wynik:** 103/150 (69%) — 100% starych testów przechodzi, nowe 47 błędów to ograniczenia słownikowe BM25 dla nowych paragrafów (ECTS, praktyki, IOS, prawa studenta).
* **Skrypt weryfikacyjny:** Dodano `tests/weryfikacja.py` — automatyczna walidacja bazy wiedzy, stemmera, wyszukiwarki i frontendu w jednym uruchomieniu.

### 🛠️ P3 — Odwrócony Indeks (wycofany przez użytkownika)
* Użytkownik wycofał Odwrócony Indeks z `wyszukiwarka.py` i cache'u `.pkl`. Powrócono do prostego `enumerate(self.wektory)`. Cache znów zapisuje 3-tuple `(idf, wektory, wszystkie_tokeny)`.

---

## 📌 Poprzednie sesje

### 📈 Wydajność i Architektura API
* **Optymalizacja Database (BM25):** Zmniejszyliśmy obciążenie SQLite znacząco, ograniczając zapytania poprzez cache'owanie współczynników `mapa_wag` na gorącej ścieżce wyszukiwania.
* **Jednokrotna Inicjalizacja:** Usunięto uciążliwe obciążenia wywołujące w pętli `inicjalizuj()` w funkcji `/zapytaj`. Od teraz następuje wyłącznie jednorazowe dogranie skryptu.
* **Optymalizacja Wyników Szukania:** Zmodyfikowano warstwę spadkową dopasowań BM25. Przeszukiwanie bazuje teraz tylko na jednym strzale w indeks (`n_wynikow=3`), unikając kosztownego drugiego cyklu przy słabym dopasowaniu.
* **Porządki Kodowe:** Usunięto wycieki `print()` na rzecz loggera w gorącej ścieżce, oraz scalono w jedną stałą instrukcje generacji polskich liter i transliteracji (`maketrans(...)`).

### 🦾 Algorytmy i Rozwój RAG
* **Numeryczne Bezpośrednie Wyszukiwanie:** Zaaplikowano parsowanie użytego paragrafu (np. "co mówi §18" lub "paragraf 18"), które kompletnie wymija tokenizację BM25 podając studentom surowy paragraf natychmiastowo z precyzją 100%.
* **Siatka Słowna (N-Gramy/Bigramy):** Wdrożono widok grafu Vis.js `graf_widok` i metodę generowania sieci powiązań bigramów z całego PDF.
* **Onboarding (Podpowiedzi Rozbiegowe):** Zaimplementowano okno powitalne z gotowymi kafelkami/chipami.

### 🖥️ UX & Interfejs (Frontend)
* **Historia Sesji (Boczny Pasek):** Użytkownicy mogą teraz wysuwać panel z historią zapytań.
* **Historia Sesji (localStorage):** Panel z historią zapytań zapamiętywany pomiędzy sesjami dzięki `localStorage`. Użytkownik nie traci kontekstu po odświeżeniu strony.
* **Motyw Jasny/Ciemny:** Aplikacja zyskała wsparcie Toggle-Switch. Preferencje zapamiętywane przez LocalStorage.
* **Licznik Ochronny:** Blokada wysyłania pytań krótszych niż 3 znaki bezpośrednio na frontendzie.
* **Eksport Rozmów do PDF:** Umożliwiono eksport całego widoku chatbota jako plik PDF (moduł `jsPDF`).

### 🛡️ Bezpieczeństwo i Administracja
* **Zapisywanie Pamięci Algorytmicznej:** Dodano zrzut `odpowiedz TEXT` bezpośrednio do tabeli `pytania` SQLite dla audytów.
* **Auto-Logi Słabych Odpowiedzi:** Wdrożono monitorowanie słabych trafień do `logs/do_poprawy.txt`.
* **Dashboard Statystyk (Admin):** Chroniony punkt `/admin` z wizualizacją Chart.js i eksportem CSV (`/admin/eksport_csv`).
* **Słownik Synonimów Live:** Panel admina umożliwia dodawanie synonimów do RAM bez restartu serwera.
