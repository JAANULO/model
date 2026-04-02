# Optymalizacja projektu v2 - konkretne zmiany do wdrozenia

Ten dokument zbiera konkretne, bezpieczne usprawnienia wydajnosci i jakosci kodu dla projektu `v2`.
Kolejnosc jest ustawiona od najwiekszego efektu do najmniejszego.

---

## Priorytet P0 (najwiekszy zysk, niski koszt)

## 1) Zmniejsz liczbe zapytan do bazy podczas wyszukiwania [zrobione]

**Problem:**
W `v2/core/wyszukiwarka.py` funkcja `szukaj()` przy kazdym zapytaniu pobiera `mapa_wag` przez `pobierz_wspolczynniki_zbiorczo()`.
To powoduje dodatkowy koszt DB dla kazdego pytania uzytkownika.

**Gdzie:**
- `v2/core/wyszukiwarka.py`

**Co zmienic:**
- Dodaj cache `mapa_wag` w pamieci z TTL, np. 30-60 sekund.
- Odswiezaj cache tylko po wygasnieciu TTL.

**Proponowany plan implementacji:**
1. Na poziomie modulu dodaj stale:
   - `MAPA_WAG_TTL = 60`
   - `_mapa_wag_cache = {"ts": 0.0, "data": {}}`
2. Dodaj funkcje pomocnicza `_pobierz_mapa_wag_cached()`:
   - jesli `time.time() - ts <= MAPA_WAG_TTL` -> zwroc cache,
   - inaczej pobierz z DB i odswiez cache.
3. W `szukaj()` podmien:
   - `mapa_wag = pobierz_wspolczynniki_zbiorczo()`
   - na: `mapa_wag = _pobierz_mapa_wag_cached()`.

**Efekt:**
- Znacznie mniej zapytan do DB przy duzej liczbie pytan.
- Mniejsze opoznienia odpowiedzi.

**Jak sprawdzic:**
- Porownaj czas odpowiedzi `/zapytaj` przed/po.
- Dodaj tymczasowo licznik wywolan `pobierz_wspolczynniki_zbiorczo()` i sprawdz spadek.

---

## 2) Usun wielokrotne `inicjalizuj()` z hot-path `/zapytaj` [zrobione]

**Problem:**
W `v2/app.py` `inicjalizuj()` jest odpalane wielokrotnie w `zapytaj()`, mimo ze baza jest juz inicjalizowana przy starcie.

**Gdzie:**
- `v2/app.py`

**Co zmienic:**
- Zostaw `inicjalizuj()` tylko przy starcie aplikacji.
- Usun wywolania `inicjalizuj()` z wnętrza `zapytaj()` (przed `zapisz_pytanie(...)`).

**Miejsca do poprawy:**
- galez obslugi bezposredniego paragrafu,
- galez braku trafienia,
- galez standardowej odpowiedzi.

**Efekt:**
- Mniej kosztownych operacji na request.
- Czystszy przeplyw i mniej ryzyka lagow.

**Jak sprawdzic:**
- Uruchom `v2/tests/test.py` i porownaj czas wykonania.

---

## 3) Nie wyszukuj dwa razy przy slabym dopasowaniu [zrobione]

**Problem:**
W `v2/app.py` najpierw jest `szukaj(..., n_wynikow=2)`, a potem w fallback ponownie `szukaj(..., n_wynikow=3)`.

**Gdzie:**
- `v2/app.py`, funkcja `zapytaj()`

**Co zmienic:**
- Od razu pobieraj `n_wynikow=3`.
- Uzyj tej samej listy wynikow:
  - `wynik = wyniki[0]`,
  - propozycje fallback z `wyniki[:3]`.

**Efekt:**
- Mniej pracy CPU i mniej zapytan do DB (bo `szukaj()` wykonuje tez logike wag).

**Jak sprawdzic:**
- Sprawdz logi czasu odpowiedzi endpointu `/zapytaj`.

---

## Priorytet P1 (stabilnosc i produkcja)

## 4) Dodaj pooling polaczen PostgreSQL [nie zrobione]

**Problem:**
W `v2/core/bd.py` dla Postgresa tworzysz nowe polaczenie przy kazdym wywolaniu `polacz()`.

**Gdzie:**
- `v2/core/bd.py`

**Co zmienic:**
- Uzyj `psycopg2.pool.SimpleConnectionPool` lub `ThreadedConnectionPool`.
- `polacz()` powinno pobierac polaczenie z puli.
- Dodaj bezpieczny zwrot polaczenia do puli (np. helper/context manager).

**Efekt:**
- Stabilniejsze dzialanie na Render/Supabase.
- Mniejszy narzut i mniej timeoutow.

**Jak sprawdzic:**
- Test obciazeniowy: seria zapytan do `/zapytaj` i brak skokow latencji.

---

## 5) Usprawnij logike debug [zrobione]

**Problem:**
W `v2/app.py` sa `print(...)` w goracej sciezce requestu (np. kontekst/intencje).

**Gdzie:**
- `v2/app.py`

**Co zmienic:**
- Zastap `print(...)` przez `logger.debug(...)`.
- Dodaj poziom logowania przez env (np. `LOG_LEVEL`).

**Efekt:**
- Czystsze logi produkcyjne i mniejszy narzut I/O.

**Jak sprawdzic:**
- W trybie produkcyjnym (`INFO`) debugi nie pojawiaja sie.

---

## 6) Ujednolic transliteracje polskich znakow [zrobione]

**Problem:**
Kilka miejsc tworzy `str.maketrans(...)` dynamicznie.

**Gdzie:**
- `v2/app.py`
- `v2/core/wyszukiwarka.py`

**Co zmienic:**
- Zdefiniuj jedna stala translacji na poziomie modulu.
- Uzywaj jej wszedzie zamiast budowac mapowanie od nowa.

**Efekt:**
- Troche mniejszy narzut CPU i mniej duplikacji kodu.

---

## Priorytet P2 (porzadki i jakosc kodu)

## 7) Uspokój ostrzezenia IDE (nie sa krytyczne) [nie zrobione]

**Problem:**
IDE pokazuje ostrzezenia dot. nieuzywanych importow i SQL inspections.

**Gdzie:**
- `v2/main.py`
- `v2/core/bd.py`

**Co zmienic:**
- Usun nieuzywane importy w `v2/main.py` i `v2/core/bd.py`.
- Dla `try/except ImportError` ustaw bezpieczne fallbacki zmiennych.
- W IDE skonfiguruj Data Source SQL lub wylacz inspekcje SQL dla stringow.

**Efekt:**
- Czystszy editor, mniej falszywych alarmow.

---

## 8) Drobne porzadki w endpointach [zrobione]

**Problem:**
W `v2/app.py` import `pobierz_ostatnie_pytania` jest poprawny, ale warto dopilnowac spojnosc endpointow i nazewnictwa payloadow.

**Co zmienic:**
- Trzymaj jednolity format payload (np. zawsze `odpowiedz` albo zawsze `wstep` + `punkty`).
- Rozwaz dodanie prostego pola `version` w odpowiedziach API.

**Efekt:**
- Latwiejszy frontend i mniej warunkow po stronie UI.

---

## Proponowana kolejnosc wdrozenia

1. P0-1: cache `mapa_wag` w `wyszukiwarka.py`.
2. P0-2: usuniecie `inicjalizuj()` z `zapytaj()`.
3. P0-3: jedno wyszukiwanie (`n_wynikow=3`) zamiast dwoch.
4. P1-4: pooling Postgresa w `bd.py`.
5. P1-5 i P1-6: logi + transliteracja.
6. P2: porzadki ostrzezen IDE i kosmetyka API.

---

## Checklista po kazdej zmianie

- [ ] `python -m compileall -q v2`
- [ ] `python v2/tests/test.py`
- [ ] test reczny `/zapytaj` (zwykle pytanie + pytanie kontekstowe + `paragraf 18`)
- [ ] test `/admin?token=...` i wykresow
- [ ] test `/graf_widok` i `/graf_wektorowy`

---

## Kryteria akceptacji (minimum)

- Brak regresji jakosci: testy nadal zaliczone.
- Sredni czas odpowiedzi `/zapytaj` nizszy niz przed zmianami.
- Brak nowych bledow runtime w logach Render.
- Brak problemow z DB (timeout, auth, reconnect).

