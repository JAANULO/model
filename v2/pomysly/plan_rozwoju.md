# Podsumowanie i kolejność wdrażania ulepszeń

Twoje notatki są zbieżne z moimi obserwacjami! Masz bardzo celne pomysły. Cześć z nich, jak "Tryb ciemny / jasny toggle" oraz "Detekcja typu pytania i Ekstrakcja", masz zresztą **już świetnie wdrożone** w kodzie (`app.py`, `intencje.py`, nagłówek CSS). Pominiemy jest więc na tej liście by skupić sie na nowościach.

Po skonsolidowaniu naszych pomysłów, oto jednolita lista zmian ułożona **od najprostszego do najtrudniejszego**. Polecam implementować je od góry do dołu.

---

## 🟢 POZIOM ŁATWY (Minuty pracy, gigantyczny efekt)

**1. Zapis Historii Pomiędzy Sesjami (localStorage)** *(Z Twojej listy)*
*   **Zmiana:** W pliku `index.html` (linijce 602) zmieniasz `sessionStorage` na `localStorage`.
*   **Dlaczego:** Odświeżenie karty F5 nie skasuje już wypracowanej przez studenta historii na lewym boku. Genialne i zajmuje 10 sekund.

**2. Licznik znaków i minimalna długość pytania** *(Z Twojej listy)*
*   **Zmiana:** Masz w JavaScripcie barierę na 200 znaków (wyświetla na czerwono). Brakuje bariery w `wyslij()`, by pominąć pytania `< 3` znaki, zwracając info na czacie "Pytanie jest za krótkie".
*   **Dlaczego:** Chroni wektory BM25 przed zapytaniami z jednym spójnikiem. Zapobiegnie generacji absurdalnych odpowiedzi do bazy logów.

**3. Dynamiczne progi dopasowań (`PROG_PEWNOSCI`)** *(Z Twojej listy)*
*   **Zmiana:** W `app.py` masz twardą granicę `0.15`. Przepisz to tak: krótkie pytania obniżają wagę (bo brakuje słów do powiększenia Cosinus Similarity), a długie ją podnoszą. Np. `prog = 0.05 + len(tokeny) * 0.02`. 
*   **Dlaczego:** Lepsze rzemiosło - naturalnie zlikwiduje to problem uciętych wyników przy "krótkich strzałach" dwuwyrazowych.

**4. Ważenie pozycji słów (Pierwsze słowa cenniejsze)** *(Z Twojej listy)*
*   **Zmiana:** W funkcji `szukaj()` przy budowaniu i wektora pytania `wektor_pytania`, dodaj mnożnik pozycji. Im wcześniejsze słowo w liście `.split()`, tym wyższy mnożnik (np. `1.5`, a ostanie `1.0`).
*   **Dlaczego:** Ludzie zaczynają od sedna (Rzeczownik, Czasownik). BM25 od razu to doceni.

**5. Podświetlanie odpowiedzi `<mark>` markerem CSS** *(Połączony pomysł UX)*
*   **Zmiana:** Mając najlepsze zdanie wyciągnięte przez `intencje.py`, we `formatowanie.py` przy wysuwaniu "pokaż pełen paragraf", otocz to wybrane zdanie w kod `<mark>Zdanie</mark>`.
*   **Dlaczego:** Odciąża wzrok studenta - po prostu nie będzie musiał czytać całości i zrozumie skąd aplikacja wzięła "2 terminy".

---

## 🟡 POZIOM ŚREDNI (Wymaga nowej logiki i modyfikacji backendu)

**6. Kontekstowy "Boost" dla ostatnio przebywanego tematu** *(Z Twojej listy)*
*   **Zmiana:** Masz detekcję `jest_kontekstowe`, ale brakuje konkretnego mnożnika w algorytmie. Jeśli 2 paragrafy walczą na punkty matematycznie łeb-w-łeb, a drugie nawiązuje do tytułu z poprzedniego pytania -> wymnóż wynik tego paragrafu na końcu pętli `wyszukiwarka.py` (np. przez `x1.3`).

**7. "Boost" Tytułu zamiast "worka na tekst"** *(Mój pomysł)*
*   **Zmiana:** BM25 punktuje całą paczkę. Zmodyfikuj funkcje TF by tytuł wpadał ze zwiększonym limitem dopasowania (np. dodaj słowa z tytułu na koniec `tokenizuj` poczwórnie by zbudować wagi, lub rozdziel macierze).

**8. Automatyczne wykrywanie niepewnych zapytań** *(Z Twojej listy)*
*   **Zmiana:** Wyświetliłeś odpowiedź, gdzie `podobienstwo` cudem przebiło próg rzędu `0.16`. Skrypt puszczając taką odpowiedź, powinien po cichu wykonać Insert do nowej tabeli w `asystent.db: slabe_trafienia`.
*   **Dlaczego:** Jako admin wiesz dokładnie które zdania są dla silnika graniczne. Omijasz dzięki temu konieczność pisania logów do sztywnych plików `do_poprawy.txt` - masz to prosto jako encję w bazie.

**9. Sugestie powiązanych pytań (Related questions / Next steps)** *(Z Twojej listy)*
*   **Zmiana:** Zbuduj mały statyczny graf zależności słownikowych. Po renderze punktów na froncie, dopinamy tagi `<button>A może zapytasz o...?</button>`. Użytkownik zostanie w Twojej apliakcji znacznie dłużej ze wsparciem.

**10. Panel Admina 2.0 - z wewnątrz systemowym dodawaniem synonimów** *(Mój Pomysł)*
*   **Zmiana:** Dopnij route w pliku Flask, który podaje nowe klucze pod RAM. Zamiast otwierać plik Pythonowy, z palca poprzez przeglądarkę pod strone `/admin` dodasz mapowanie slangu.

**11. Endpoint od zrzutu CSV ze statystykami** *(Z Twojej listy)*
*   **Zmiana:** Import biblioteki `csv` w `app.py`, zebranie z bazy poprzez moduł `bd.py` logów, zapytanie odwraca listę i podaje `Response(mimetype="text/csv")`. Zawsze pomocne by przeanalizować dane w Excelu na lokalu.

---

## 🔴 POZIOM TRUDNY (Zmiana modeli architektonicznych i klasycznych "Problemów NP")

**12. Implementacja Bigramów i N-Gramów w Wyszukiwarce BM25** *(Z Twojej listy)*
*   **Zmiana:** Niesamowite jak bardzo zmieni to trafność. Trzeba zmodyfikować funkcje `tokenizuj` oraz pętle TF-IDF żeby dorzucały do słownika `słowo_A + "_" + słowo_B`. Od teraz masz w słowniku `egzamin_komisyjny` a nie tylko `egzamin`. Wymaga to jednak przestrojenia całych wag `idf`, re-cacheowania `.pkl` oraz uważania, żeby rozszerzać te rzeczy przy wpisywaniu uzytkownika. 

**13. Lepszy system oboczności (Lematyzacyjna poprawa rdzeni słowa)** *(Mój Pomysł)*
*   **Zmiana:** Plik `stemmer.py` jest za prosty, gubi wiele form. Trzeba by było dodać listę odchyleń koninkcyjnych specjalnie dla Polskiego PWr. (np. kolokwia -> kolokwium, studenci -> student), czyli to gdzie końcówki odcinane na sucho dają zły i tak odmieniony "rdzeń". Można to oprzeć o małe tablice hash. Zmiana fundamentalna dla wyliczania BM25.

**14. Przerzucenie Wyszukiwarki: Model N-D -> Odwrócony Indeks Mapy (Inverted Index)** *(Z Twojej listy)*
*   **Zmiana:** Porzucenie `for i, wf in enumerate(self.wektory):` na rzecz budowy Mapy Słownikowej (gdzie Słowu BM25 staje się powiązane od razu z macierzą i numerem dokumenty). Wyelimowanie liczenia wyników dla każdego przypadku z Zera. 
*   **Dlaczego Trudne:** Matematycznie jest to refaktor całkowity głównej `wyszukiwarka.py`. Chociaż baza ~40 paragrafów leci błyskawicznie, to dla setek stron regulaminu zacznie blokować całe obłożone requestami API, bo O(N) wyszukiwania zablokuje Gunicorna. **To trzeba zrobić skalując narzędzie pod szeroką publikę docelową**.
*   **Rekomendacja:** Polecam wprowadzić, ale dopiero gdy cała reszta projektu w ogóle uzyska akceptację wśród pierwszej garści testujących studentów (faza Optymalizacji Big-Tech).

**15. Testy A/B eksperymentalnych flag pytań** *(Z Twojej listy)*
*   **Dlaczego Trudne:** Zasadniczo najmniej potrzebna zmiana ze wszystkich, na dodatek silnie angażująca cały podsystem. System do analizy testów A/B wymaga potężnego flow danych i dużej próbki. Nie dawałby wymiernych wniosków przy relatywnie małym natężeniu trafiku. Polecam zostawić to absolutnie na sam koniec życia projektu po jego potężnym sukcesie.
