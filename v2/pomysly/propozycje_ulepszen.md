# Propozycje rozwoju: Asystent Regulaminowy PWr

Jeżeli Twoim celem jest wypuszczenie projektu na produkcję i udostępnienie go studentom, istnieje kilka rewelacyjnych technik optymalizacji, które zaufają Twojej filozofii "zera zewnętrznych, gotowych bibliotek AI".

Skupiłem się na dwóch filarach: polepszeniu samego systemu "szukania odpowiedzi" (żeby mniej się mylił) oraz polepszeniu zadowolenia użytkownika (UX/UI).

---

## 🛠 1. Lepsza poprawność odpowiedzi (Ulepszenia Algorytmiczne)

### A. Metoda "N-Gramów" (Wyszukiwanie Frzeologiczne) [troche zrobione]
*   **Problem:** Obecnie algorytm BM25 i tokenizacja rozbija text na pojedyncze słowa tzw. *Bag of Words*. Kiedy zapytasz o "urlop dziekański", algorytm szuka słowa "urlop" i słowa "dziekański". Jeśli bardzo długi i nieistotny dokument będzie posiadał masę słów "urlop", może przeskoczyć ten poprawny.
*   **Rozwiązanie:** Podczas budowy bazy w `wyszukiwarka.py`, twórz tzw. *Bigramy* (pary słów). Jeśli w tekście występuje "urlop dziekański", wrzuć do wektora pojedyncze słowa ["urlop", "dziekański"] oraz sklejkę `["urlop_dziekanski"]`.
*   **Zysk:** Jeśli użytkownik wpisze "urlop dziekański", uderzenie macierzy w wektor `urlop_dziekanski` podbije punktację o kilkaset procent względem innych dokumentów, całkowicie odrzucając te pudła, które miały obok siebie te słowa zupełnie przypadkiem.

### B. Izolacja WAG - Podwójny System Ocen (Tytuł vs Treść) [nie zrobione]
*   **Problem:** Obecnie punktacja BM25 zlicza słowa z tytułu i tekstu razem jako jeden worek tekstowy (wyciągając całe `self.wszystkie_tokeny`).
*   **Rozwiązanie:** Odseparuj tytuły paragrafów od treści. Przeszukuj zapytanie po tytule oddzielnie od treści regulaminu i wymnóż. Np. Dopasowanie w tytule to x3 pkt, a dopasowanie w tekście to x1 pkt.
*   **Zysk:** Zapytania wprost o nazwy paragrafu (np. "Egzamin dyplomowy", "Poprawki") zawsze przebiją gigantyczne paragrafy w których o poprawkach tylko wspominano na dnie.

### C. Pseudo-Relevance Feedback (Algorytm Rocchio) [troche zrobione]
*   **Problem:** Student może zadać pytanie dziwnymi słowami, użyć slangu albo nie zapytać merytorycznie poprawnie.
*   **Rozwiązanie (Dwu-stopniowe szukanie):** Program przyjmuje wpisane przez studenta bardzo ogólnikowe zapytanie -> robi błyskawiczne "ciche wyszukiwanie BM25" na serwerze i wyłania zwycięski paragraf pierwszej iteracji. Serwer pobiera wtedy 3 kluczowe, mocne i mądre słowa z najlepszego paragrafu (których nie było w zapytaniu!) -> dokleja je do pierwotnego pytania studenta -> odpala szukanie jeszcze raz, tym razem by dać ostateczną odpowiedź. 
*   **Zysk:** System w inteligentny sposób dopowiada sobie o co chodziło, zupełnie tak jak robiłby to ChatGPT "planując poszerzenie poszukiwań", tyle że Ty dokonasz tego zwykłym połączeniem stringów.

### D. Polepszenie Oboczności (Rozbudowa Stemmera) [troche zrobione]
*   W pliku `stemmer.py` masz tylko najpopularniejsze przyrostki (`owanie`, `ach`). Język polski to morze wyjątków (oboczności): np. *studenci* -> *student*, *psa* -> *pies*.
*   Dopisz mały słownik (hash-mapę ręczną) na powtarzające się formy na uczelni, np. "kolos", "kolokwia" ucinając zawsze do formy "kolokwi". Pozbędzie to algorytm wielu kłopotów z wyłapywaniem sensu tam, gdzie w rdzeniu zmieniła się literka (np. "zdał" vs "zda").

---

## 🎓 2. Gotowość do Rynku: Zadowolenie Użytkownka (Złoty UX/UI)

### A. Okno Uściślania Wątpliwości (Disambiguation) [troche zrobione]
*   **Pomysł:** Często algorytm staje przed wyborem np. czy pokazać §15 Urlop Zdrowotny czy §16 Urlop Dziekański (podobne wyniki różniące się o `0.02` współczynnika ufności). Zamiast zgadywać dając w ciemno §15, zwróć frontendowi podwójną odpowiedź. Zrób na stronie czat, w którym Asystent PWr spyta: **"Och! Wygląda na to, że Regulamin dzieli urlopy. Wybierz, o który Ci chodzi:"** i podaj mu dwa przyciski pod spodem: `Urlop Dziekański`, `Urlop Zdrowotny`.
*   **Dlaczego To Ważne?** Pokazuje to studentowi, że nawiguje po rzetelnym "katalogu wiedzy", a nie gadającym bzdury bocie!

### B. Highlighting Zdania W Pełnym Treści [nie zrobione]
*   **Pomysł:** W module `formatowanie.py` podajesz użytkownikowi `pelna_tresc` w wysuwanym okienku źródłowym, a w widoku z główną odpowiedzią pokazujesz zdanie kluczowe (skrót/najlepsze zdanie z RAG-u). Ustaw w JavaScript podświetlenie markerem (Żółte Tło CSS) dla dokładnego "ciągu znaków" będącego *najlepszym zdaniem*!
*   **Dlaczego To Ważne?** Student sprawdzający np. Prawa Egzaminacyjne ma przed oczami litanię tekstu, do którego odesłał go asystent na źródłach. Wzrok naturalnie poleci na "marker", natychmiastowo autoryzując, że Asystent wylosował właściwy dół paragrafu, a użytkownik potwierdzi to oceniając to Kciukiem w górę.

### C. Podpowiedzi Rozbiegowe (Onboarding Starter Pack) [zrobione]
*   **Pomysł:** Otwierasz stronę i wita Cię goła "lupka wyszukiwania". To często paraliżujące - "o co zapytać asystenta?". Stwórz tzw. "pigułki pod lupą", 3 lub 4 klikalne guziki/kafelki np.:
    * *"Czego dotyczy praca dyplomowa?"*
    * *"Co w sytuacji braku zaliczenia?"*
    * *"Jak liczona jest średnia?"*
*   **Dlaczego To Ważne?** Użytkownik widzi po wejściu "co ten Asystent PWr potrafi robić". 

### D. System Szybkiego Dopisywania Słowników z Ciemni (Admin Panel) [troche zrobione]
*   Posiadasz genialną rzecz: Moduł bazy danych oceniający kciuki użykowników oraz zapisywanie złych odpowiedzi do logów `logs/do_poprawy.txt`.
*   **Pomysł:** Wykorzystaj to! Przerób plik tekstowy na odczyt z bazy w nowej zakłądce z tabelą `admin.html`. Dodaj tam małe pole input. Jeżeli widzisz log błędu "Student pytał o ITS (Indywiudalny Tok Studiów), przypisało złą kategorię!", wpisujesz w panelu Admina w pole Synonimy: `ITS = Indywiudalny Tok Studiow` – po kliknięciu wyślij, słownik w RAM odświeża się bez ponownego uruchamiania skryptu! System natychmiast poprawia się "na żywo", budując mocny i elastyczny serwer we Flasku. Wtedy wypuszczenie tego w świat to kwestia kilku godzin dopieszczeń i dbałość administracyjna o zapytania będzie banalna.
