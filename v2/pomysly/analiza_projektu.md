# Analiza Projektu: Asystent Regulaminowy PWr

Projekt ten to autorski system nawigacji po regulaminie studiów Politechniki Wrocławskiej. Został zbudowany od podstaw przy użyciu czystego Pythona, unikając gotowych rozwiązań (jak zewnętrzne wektorowe bazy danych czy frameworki NLP do RAGa typu LangChain lub LlamaIndex) na rzecz własnych implementacji algorytmów.

## 🏗 Architektura Projektu

Projekt dzieli się na dwie główne sekcje:
1. **Wersja 1 (Mini-GPT):** Edukacyjna implementacja architektury Transformer i modelu generatywnego od zera z użyciem PyTorch.
2. **Wersja 2 (Asystent Regulaminowy PWr - v2):** Aktualnie działająca główna sekcja zawierająca customowy silnik RAG (Retrieval-Augmented Generation bez typowego powiększenia LLMem).

### Kluczowe komponenty backendu (wersja v2):
- **`app.py`:** Aplikacja napisana we Flasku służąca jako interfejs webowy i API. Zarządza wątkami zapytań użytkownika, obsługuje wbudowany system pamięci podręcznej odpowiedzi (uruchamianej jako zmienna `CACHE_ODPOWIEDZI` o globalnym stanie z TTL 1h i zrzutem LRU), zapisuje feedback i komunikuje się z pozostałymi paczkami.
- **`core/wyszukiwarka.py`:** Główny silnik wyszukujący paragrafy. Wykorzystuje **BM25** (ulepszona dystrybuanta TF-IDF używana chociażby w Elasticsearch) połączone z wektorami, wyliczając **podobieństwo cosinusowe** pomiędzy zapytaniem a wektorem z dokumentów regulaminu. Dodatkowo zawiera moduł auto-korekcji uwzględniający pomyłki w pisowni z wykorzystaniem odległości edycyjnej **Levenshteina**.
- **`core/intencje.py`:** Prosty parser rozróżniający naturalne NLP. Rozróżnia intencje użytkownika na `LICZBA`, `TERMIN`, `TAK_NIE`, `SKUTEK`, `PROCEDURA`. Po wyłuskaniu intencji, system stosuje dedykowane moduły wyszukiwania we wnętrzu znalezionego paragrafu (np. `wyciagnij_liczbe` przekuwające opis słowny na cyfrę, a potem łączące to w dedykowany krótki tekst używając funkcji `generuj_skrot`).
- **`core/formatowanie.py`:** Praca na zebranym tekście. Moduł usuwa luki i buduje odpowiedź prezentowaną z przyjaznym nagłówkiem tematycznym i konkretnymi wyciągniętymi punktami. Wzbogacony słownikami pozwalającymi określić powtarzające się zwroty (np. dedykowana tabelka na skale ocen).
- **`core/bd.py`:** Przechowywanie stanów, logów i danych opartych o lokalną bazę `SQLite` (`asystent.db`). Zbiera oceny od użytkowników "kciuk w górę/w dół", przez co system zapisuje na ich podstawie globalne wagi `mapa_wag` służące potem jako prymitywny algorytm douczania.

### Działanie systemu RAG na przykładzie zapytania
1. **Normalizacja wejścia:** System tokenizuje pytanie, czyści ze znaków interpunkcyjnych i stop-words (poważne uproszczenie do rdzenia zdania). 
2. **Rozszerzanie słownikowe:** Wykorzystując `slowniki.py`, moduł stosuje synonimy sprawiając, że zapytanie o kolokwializm zostaje poprawnie zmapowane na formalny termin regulaminu (np. "dziekanka" -> "urlop dziekański").
3. **Kontekstualizacja:** Aplikacja analizuje poprzednie zapytanie. Jeśli jest to pytanie nawiązujące ("a co jeśli...", "co wtedy"), system wykorzystuje globalną wiedzę sesyjną i dodaje do wyszukiwania fragment ostatnio wyswietlanego paragrafu by poprawić poprawność kontekstową BM25.
4. **Ranking przez BM25 & Levenshtein:** Macierz TF-IDF jest mapowana za pomocą równania BM25. Baza danych przeszukuje cache i wylicza Cosinus Similarity względem wpisanego zadania. Jeśli podobieństwo jest wyższe niż próg minimalnej ufności (`0.15`), pobiera najlepszy lub dwa najlepsze paragrafy regulaminu.
5. **Generacja / Intencja zdania:** Po pobraniu paragrafu, aplikacja w zależności od tematu próbuje zawęzić celność do konkretnej sentencji. Pozyskane w ten sposób konkretne dane, jak "2", formuje w przyjazny dla oka skrót: **"Odpowiedź: 2 terminy"** połączony na froncie z opisowym paragrafem.

## Mocne Strony Projektu:
*   **Całkowita niezależność:** Wszystkie kluczowe algorytmy NLP napisane od zera w środowisku edukacyjnym, co pozwala ominąć wagowo i zależnościowo koszty tradycyjnego RAG/TensorFlow.
*   **Wydajność:** Oprogramowanie cache'uje odpowiednio pliki TF-IDF BM25 do formatu `*_cache.pkl` z wykorzystaniem `pickle`, co zapewnia ultraszybkie parsowanie pytań rzędu `< 50ms`. Dodatkowy in-memory cache we Flasku do 500 wpisów.
*   **Rozsądny System Intencji i Reguł:** Przejęcie ciężaru logiki przez regułowe Parsowanie/Regex w powiązaniu z wektorem BM25 chroni asystenta przed *halucynacjami*, co w przestrzeni formalnych uczelnianych procedur jest kluczową przewagą nad powszechnymi LLM-ami bez "guardraili".

## Propozycje rozwoju na przyszłość:
1. Przeniesienie konfiguracji słowników i stop-words z klasycznych słowników po stronie kodu Pythona do plików .yml lub .json poprawiłoby elastyczność w zarządzaniu modelem i dodałoby pewnej bezwarunkowości kodu.
2. Migracja Flask -> FastAPI: Dałoby asynchroniczne obsłużenie ruchu, co powiązałoby się bezpośrednio ze zwydajniejszym ruchem API (zwłaszcza zapytania do SQLite). Wymagałoby to wyczyszczenia "globalnych" stanów `indeks_zdan` po stronie modułu webowego.
3. System cache jest trzymany lokalnie we Flasku na pamięci globalnej/heapie (np. `CACHE_ODPOWIEDZI`). Do wdrożeń produkcyjnych na serwerach wielowątkowych (Gunicorn/WSGI), lepszą opcją byłoby przeniesienio tego pod usługę w rodzaju Redis.
