"""
wyszukiwarka.py - Krok 2 wersji 2.0
Algorytm TF-IDF napisany od zera.
Wyszukuje w bazie wiedzy fragment najbardziej pasujacy do pytania.
"""

import json
import math
import re
import os

PLIK_BAZY = os.path.join(os.path.dirname(__file__), '..', 'data', 'baza_wiedzy.json')


# ── Krok 1: przygotowanie tekstu ──────────────────────────────────────────────

def usun_polskie_znaki(tekst):
    """zamienia polskie litery na odpowiedniki bez ogonkow"""
    zamiana = str.maketrans(
        'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ',
        'acelnoszzACELNOSZZ'
    )
    return tekst.translate(zamiana)

SYNONIMY = {

    # ── egzamin ───────────────────────────────────────────────────────────────
    # odmiany
    "egzaminu":   "egzamin", "egzaminie":  "egzamin", "egzaminow":   "egzamin",
    "egzaminy":   "egzamin", "egzaminami": "egzamin",
    "egzaminacyjnej": "komisja",
    "egzaminacyjny": "komisja",
    # kolokwializmy i synonimy
    "zdac":       "egzamin", "zdawac":     "egzamin", "oblac":        "egzamin",
    "oblejesz":   "egzamin", "oblales":    "egzamin", "zdales":       "egzamin",
    "poprawka":   "egzamin", "poprawke":   "egzamin", "poprawki":     "egzamin",
    "kolokwium":  "egzamin", "kolos":      "egzamin", "kolosa":       "egzamin",
    "test":       "egzamin", "testy":      "egzamin", "testow":       "egzamin",
    "sprawdzian": "egzamin", "sprawdzianu":"egzamin",
    "sesja":      "egzamin", "sesji":      "egzamin", "sesje":        "egzamin",
    "termin":     "egzamin", "terminu":    "egzamin", "terminy":      "egzamin",
    "podejsc":    "egzamin", "podejde":    "egzamin", "podchodze":    "egzamin",

    # ── zaliczenie ────────────────────────────────────────────────────────────
    "zaliczenia":  "zaliczenie", "zaliczeniu":  "zaliczenie",
    "zaliczen":    "zaliczenie", "zaliczeniowy":"zaliczenie",
    "zaliczyc":    "zaliczenie", "zaliczylem":  "zaliczenie",
    "niezaliczony":"zaliczenie", "niezaliczone":"zaliczenie",
    "warunek":     "zaliczenie", "warunkowe":   "zaliczenie", "warunku": "zaliczenie",

    # ── urlop ─────────────────────────────────────────────────────────────────
    "urlopu":       "urlop", "urlopie":      "urlop", "urlopy":       "urlop",
    "dziekanski":   "urlop", "dziekanskiego":"urlop", "dziekanskim":  "urlop",
    "zdrowotny":    "urlop", "zdrowotnego":  "urlop", "zdrowotnym":   "urlop",
    "zawodowy":     "urlop", "zawodowego":   "urlop",
    "rodzicielski": "urlop", "rodzicielskiego":"urlop",
    "przerwa":      "urlop", "przerwy":      "urlop", "przerwe":      "urlop",
    "zawieszenie":  "urlop", "wstrzymanie":  "urlop",
    "wolne":        "urlop", "wolnego":      "urlop",
    "ciaza":        "urlop", "ciazy":        "urlop", "ciaze":        "urlop",
    "macierzynski": "urlop", "macierzynskiego":"urlop",

    # ── skreślenie ────────────────────────────────────────────────────────────
    "skreslic":     "skreslenie", "skreslanego":  "skreslenie",
    "skreslanym":   "skreslenie", "skreslonego":  "skreslenie",
    "skreslon":     "skreslenie", "skreslonej":   "skreslenie",
    "wydalenie":    "skreslenie", "wydalic":      "skreslenie",
    "wydalono":     "skreslenie", "wydalony":     "skreslenie",
    "usuniecie":    "skreslenie", "usuniety":     "skreslenie",
    "rezygnacja":   "skreslenie", "rezygnacji":   "skreslenie",
    "rezygnowac":   "skreslenie", "odejsc":       "skreslenie",
    "exmatrykulacja":"skreslenie",
    "wyrzucenie":   "skreslenie", "wyrzucony":    "skreslenie",
    "rzucic":       "skreslenie", "rzucam":       "skreslenie",
    "niezapisanie": "skreslenie",  # "co grozi za niezapisanie się"
    "niezapisanym": "skreslenie",
    "niepodjecie": "skreslenie",  # nie podjęcie studiów
    "niepodjecia": "skreslenie",
    "niezapisania": "skreslenie",
    "niezlozenia": "skreslenie",

    # ── wznowienie ────────────────────────────────────────────────────────────
    "wznowic":      "wznowienie", "wznowienia":   "wznowienie",
    "wznowieniu":   "wznowienie", "wznowil":      "wznowienie",
    "przywrocic":   "wznowienie", "przywrocenie": "wznowienie",
    "wrocic":       "wznowienie", "wracac":       "wznowienie",
    "powrot":       "wznowienie", "powrotu":      "wznowienie",
    "reaktywacja":  "wznowienie", "reaktywowac":  "wznowienie",
    "kontynuowac":  "wznowienie", "kontynuacja":  "wznowienie",

    # ── ocena ─────────────────────────────────────────────────────────────────
    "ocene":    "ocena", "oceny":    "ocena", "ocenom":   "ocena",
    "srednia":  "ocena", "sredniej": "ocena", "srednią":  "ocena",
    "wynikow":  "ocena", "wyniki":   "ocena", "wynik":    "ocena",
    "trojka":   "ocena", "czworka":  "ocena", "piatka":   "ocena",
    "dwojka":   "ocena", "jedynka":  "ocena",
    "stopien":  "ocena", "stopnia":  "ocena",
    "punkty":   "ocena", "punktow":  "ocena",
    "gpa":      "ocena",

    # ── praca dyplomowa ───────────────────────────────────────────────────────
    "dyplomowa":   "dyplom", "dyplomowej":  "dyplom", "dyplomowym":  "dyplom",
    "dyplomowe":   "dyplom", "dyplomowy":   "dyplom",
    "inzynierska": "dyplom", "inzynierskiej":"dyplom",
    "magisterska": "dyplom", "magisterskiej":"dyplom",
    "obrone":      "dyplom", "obrona":      "dyplom", "obrony":      "dyplom",
    "obronil":     "dyplom", "obronie":     "dyplom",
    "promotor":    "dyplom", "promotora":   "dyplom", "promotorem":  "dyplom",
    "recenzent":   "dyplom", "recenzenta":  "dyplom",
    "antyplagiat": "dyplom", "plagiat":     "dyplom",
    "teza":        "dyplom", "tezy":        "dyplom",
    "praca":       "dyplom", "pracy":       "dyplom", "prace":       "dyplom",
    "projekt":     "dyplom", "projektu":    "dyplom",

    # ── nieobecność ───────────────────────────────────────────────────────────
    "nieobecnosci":  "nieobecnosc", "nieobecnoscia": "nieobecnosc",
    "nieobecnych":   "nieobecnosc", "nieobecny":     "nieobecnosc",
    "opuscic":       "nieobecnosc", "opuszczac":     "nieobecnosc",
    "opoznienie":    "nieobecnosc", "spoznienie":    "nieobecnosc",
    "nie przysc":    "nieobecnosc", "nie pojsc":     "nieobecnosc",
    "ominac":        "nieobecnosc", "ominiety":      "nieobecnosc",
    "choroba":       "nieobecnosc", "choroby":       "nieobecnosc",
    "zwolnienie":    "nieobecnosc", "zwolnienia":    "nieobecnosc",
    "l4":            "nieobecnosc",
    "wagarowac":     "nieobecnosc", "wagary":        "nieobecnosc",

    # ── powtarzanie przedmiotu ────────────────────────────────────────────────
    "powtarzac":    "powtarzanie", "powtorzyc":    "powtarzanie",
    "powtarzania":  "powtarzanie", "powtarzal":    "powtarzanie",
    "powtarzany":   "powtarzanie", "powtarzanego": "powtarzanie",
    "drugi raz":    "powtarzanie", "po raz drugi": "powtarzanie",
    "ponownie":     "powtarzanie", "jeszcze raz":  "powtarzanie",
    "warunkowo":    "powtarzanie",

    # ── praktyki ──────────────────────────────────────────────────────────────
    "praktyk":      "praktyki", "praktyke":     "praktyki",
    "praktykant":   "praktyki", "praktykanta":  "praktyki",
    "staz":         "praktyki", "stazu":        "praktyki", "staze":      "praktyki",
    "praktyczne":   "praktyki", "praktycznego": "praktyki",
    "praca zawodowa":"praktyki","firmy":        "praktyki",

    # ── studia / organizacja ──────────────────────────────────────────────────
    "studiow":    "studia", "studiach":   "studia", "studiuje":  "studia",
    "kierunek":   "studia", "kierunku":   "studia", "kierunki":  "studia",
    "wydzial":    "studia", "wydzialu":   "studia",
    "semestrze":  "semestr", "semestru":  "semestr", "semestrow": "semestr",
    "etap":       "semestr", "etapu":     "semestr", "etapie":    "semestr",
    "rok":        "semestr", "roku":      "semestr", "rocznik":   "semestr",
    "tygodniu":   "tydzien", "tygodnie":  "tydzien", "tygodni":   "tydzien",
    "tygodniowy": "tydzien",

    # ── indywidualna organizacja studiów (IOS) ────────────────────────────────
    "ios":              "indywidualny", "indywidualnie":    "indywidualny",
    "indywidualnego":   "indywidualny", "indywidualnym":    "indywidualny",
    "elastyczny":       "indywidualny", "dostosowanie":     "indywidualny",

    # ── egzamin komisyjny ─────────────────────────────────────────────────────
    "komisyjny":    "komisyjny", "komisyjnego":  "komisyjny",
    "komisje":      "komisyjny", "komisji":      "komisyjny",
    "odwolanie":    "komisyjny", "odwolac":      "komisyjny",
    "kwestionowac": "komisyjny", "protest":      "komisyjny",
    "skarga":       "komisyjny", "skarzyc":      "komisyjny",
    "podwazyc":     "komisyjny", "zakwestionowac":"komisyjny",
    "obserwator":   "komisyjny",
    "obserwatora":  "komisyjny",
    "obserwatorem": "komisyjny",
    "wniosek":      "komisyjny",

    # ── ECTS / punkty ─────────────────────────────────────────────────────────
    "ects":       "punkty", "kredyty":    "punkty",
    "punktacja":  "punkty", "punktow":    "punkty",

    # ── stypendia ─────────────────────────────────────────────────────────────
    "stypendium":   "stypendium", "stypendialny":  "stypendium",
    "stypendysty":  "stypendium", "stypendystow":  "stypendium",
    "dofinansowanie":"stypendium", "zapomoga":     "stypendium",
    "socjalne":     "stypendium", "socjalnego":    "stypendium",
    "rektora":      "stypendium", "naukowe":       "stypendium",

    # ── dziekanat / administracja ─────────────────────────────────────────────
    "dziekanat": "dziekan", "dziekanatu": "dziekan",
    "dziekana": "dziekan", "dziekanem": "dziekan",
    "prodziekan": "dziekan", "prodziekana": "dziekan",
    "wniosku": "dziekan", "wnioski": "dziekan",
    "podanie": "dziekan", "podania": "dziekan",
    "zgoda": "dziekan", "zgody": "dziekan",
    "decyzja": "dziekan", "decyzji": "dziekan",
    # ── poprawki ──────────────────────────────────────────────────────────────
    #"egzamin komisyjny": "komisja komisyjny kwestionuje wniosek dziekan prodziekan przewodniczy obserwator trzech osob",
    #"obserwatora na egzaminie": "egzamin komisyjny komisja obserwator dziekan prodziekan przewodniczy",
    #"obserwatora": "komisja komisyjny obserwator dziekan prodziekan",
    "dni": "egzamin",
    "terminem": "egzamin",

}

ROZSZERZENIA_ZAPYTAN = {
    "egzamin": "dwukrotnego egzaminatorem terminie sesji unieważnienie",
    "egzaminu": "dwukrotnego egzaminatorem terminie sesji unieważnienie",
    "egzamni": "dwukrotnego egzaminatorem terminie sesji unieważnienie",
    "komisyjny": "komisyjny kwestionuje sposób warunki zakres wniosek egzaminatora dziekan zarządzi",
    "komisji": "komisyjny kwestionuje sposób warunki zakres wniosek egzaminatora dziekan zarządzi",
    "obserwator": "komisyjny kwestionuje sposób warunki zakres wniosek egzaminatora dziekan zarządzi",
    "procent": "skala ocen bardzo dobry dostateczny niedostateczny procent stopień opanowania",
    "piatke": "skala bardzo dobry piec dziewiecdziesiat sto procent stopień",
    "czworke": "skala dobry cztery siedemdziesiat siedemdziesiat dziewiec procent stopień",
    "trojke": "skala dostateczny trzy piecdziesiat piecdziesiat dziewiec procent stopień",
    "cztery i pol": "skala dobry plus cztery piec osiemdziesiat osiemdziesiat dziewiec procent",
    "rezygnacje": "skreśla rektor rezygnacji pisemne oświadczenie lista studentów",
    "rezygnacja": "skreśla rektor rezygnacji pisemne oświadczenie lista studentów",
    "niezapisanie": "skreśla rektor niepodjecia lista studentów zapisy rejestracja",
    "sesja letnia": "lipiec sesja egzaminacyjna konczy pietnastu tygodni kalendarz",
    "konczy sesja": "lipiec sesja egzaminacyjna konczy pietnastu tygodni kalendarz",
    "ile dni": "pieciodniowym odstepem drugi termin egzaminu",
    "urlop dziekanski": "urlop dziekanski dwoch etapow nieprzekraczajacym calym toku",
    "ile urlopow": "urlop dziekanski dwoch etapow nieprzekraczajacym calym toku",
    "zdac":        "dwukrotnego egzaminatorem terminie sesji",
    "zdawac":      "dwukrotnego egzaminatorem terminie sesji",
    "oblac":       "dwukrotnego egzaminatorem terminie sesji",
    "poprawka":    "dwukrotnego egzaminatorem terminie sesji",
    "podejsc":     "dwukrotnego egzaminatorem terminie sesji",
    "urlop":       "dziekanski zdrowotny zawodowy rodzicielski udzielony semestrów",
    "urlopu":      "dziekanski zdrowotny zawodowy rodzicielski udzielony semestrów",
    "dziekanski":  "urlop dziekanski zdrowotny zawodowy udzielony",
    "nieobecnosc": "nieobecnosci limit dopuszczalnych uczestniczenia zapisany zarejestrowany obowiazany",
    "dyplom": "dyplomowej promotor opiekun recenzent antyplagiat streszczenie pisemna",
    "praca": "dyplomowej promotor opiekun recenzent antyplagiat streszczenie pisemna",
    "dyplomowa": "dyplomowej promotor opiekun recenzent antyplagiat streszczenie pisemna",
    "wspolna": "dyplomowej promotor opiekun recenzent antyplagiat streszczenie pisemna",
    "wznowienie": "wznowienia przywrocenie harmonogramem semestralnej posrednictwem pisemny wniosek reaktywacja",
    "wznowic": "wznowienia przywrocenie harmonogramem semestralnej posrednictwem pisemny wniosek reaktywacja",
    "wznowic po": "wznowienia przywrocenie harmonogramem semestralnej pisemny wniosek",
    "wznowic studia": "wznowienia przywrocenie harmonogramem semestralnej pisemny wniosek",
    "skreslenie": "skresla rektor niepodjecia rezygnacji niezlozenia wydaleniem",
    "ocena": "skala bardzo dobry dostateczny niedostateczny procent prog",
    "oceny": "skala bardzo dobry dostateczny niedostateczny procent prog",
    "regulaminie": "skala bardzo dobry dostateczny niedostateczny procent prog",
    "powtarzanie": "niezaliczenia przedmiotu ponownego udzialu cyklu dydaktycznym zobowiazany",
    "powtorzyc": "niezaliczenia przedmiotu ponownego udzialu cyklu dydaktycznym zobowiazany",
    "powtarzac": "niezaliczenia przedmiotu ponownego udzialu cyklu dydaktycznym zobowiazany",
    "powtarzac semestr": "niezaliczenia przedmiotu ponownego udzialu cyklu dydaktycznym zobowiazany",
    "semestr": "tygodni kalendarz akademicki pazdziernika wrzesnia rektor",
    "semestru": "tygodni kalendarz akademicki pazdziernika wrzesnia rektor",
    "dlugo": "tygodni kalendarz akademicki pazdziernika wrzesnia rektor",
    "trwa": "tygodni kalendarz akademicki pazdziernika wrzesnia rektor",
    "komisja": "komisyjny kwestionuje sposob warunki zakres wniosek egzaminatora",
    "komisji egzaminacyjnej": "egzamin komisyjny dziekan prodziekan trzech osob obserwator",
    "komisyjny": "egzamin komisyjny kwestionuje ocene sposob warunki zakres wniosek dziekan prodziekan przewodniczacy komisji trzech osob obserwator",
    "obserwatora na egzaminie": "egzamin komisyjny obserwator komisja dziekan prodziekan",
    "egzamin komisyjny": "komisyjny wniosek kwestionuje ocene dziekan prodziekan komisja obserwator",

}


def levenshtein(a, b):
    """oblicza odległość edycyjną między dwoma słowami"""
    if len(a) < len(b):
        return levenshtein(b, a)
    if not b:
        return len(a)
    poprzedni = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        aktualny = [i + 1]
        for j, cb in enumerate(b):
            wstaw    = poprzedni[j + 1] + 1
            usun     = aktualny[j] + 1
            zamien   = poprzedni[j] + (ca != cb)
            aktualny.append(min(wstaw, usun, zamien))
        poprzedni = aktualny
    return poprzedni[-1]


def popraw_literowke(slowo, slownik, max_odleglosc=1):
    """
    jeśli słowo nie jest w słowniku, znajdź najbliższe przez Levenshteina.
    max_odleglosc=1 oznacza max 1 literówka – np. 'egzamni' → 'egzamin'
    """
    if slowo in slownik:
        return slowo
    kandydaci = [s for s in slownik if abs(len(s) - len(slowo)) <= max_odleglosc]
    najlepszy = min(kandydaci, key=lambda s: levenshtein(slowo, s), default=None)
    if najlepszy and levenshtein(slowo, najlepszy) <= max_odleglosc:
        return najlepszy
    return slowo


def normalizuj(slowo):
    """zamienia odmianę słowa na formę podstawową używając słownika synonimów"""
    return SYNONIMY.get(slowo, slowo)


def tokenizuj(tekst):
    """
    rozbija tekst na liste slow (tokenow).
    usuwa interpunkcje, zamienia na male litery,
    normalizuje polskie znaki zeby pytania bez ogonkow tez dzialaly.
    """
    tekst = tekst.lower()
    tekst = usun_polskie_znaki(tekst)
    tekst = re.sub(r'[^\w\s]', ' ', tekst)
    # zachowaj liczby jako tokeny – np. "3" z "mam 3 nieobecności"
    # (domyślnie \w już je zachowuje, ale usuwamy je przez len > 1 niżej)

    slowa = tekst.split()
    # stopwords - slowa ktore nic nie znacza dla wyszukiwania
    stopwords = {
        'i', 'w', 'z', 'do', 'na', 'ze', 'nie', 'sie', 'jest',
        'to', 'a', 'o', 'lub', 'oraz', 'po', 'przez', 'przy',
        'ten', 'ta', 'te', 'tego', 'tej', 'tym', 'tych', 'od',
        'za', 'jak', 'czy', 'co', 'kt', 'kto', 'ale', 'bo', 'by',
        'go', 'mu', 'jej', 'ich', 'im', 'je', 'dla', 'gdy', 'az',
        'tez', 'juz', 'jesli', 'ze', 'tego', 'tej', 'jego', 'jako'
    }
    return [normalizuj(s) for s in slowa if s not in stopwords and (len(s) > 1 or s.isdigit())]


# ── Krok 2: budowanie macierzy TF-IDF ────────────────────────────────────────

def oblicz_tf(slowa):
    """
    oblicza czestotliwosc kazdego slowa we fragmencie.
    wynik: slownik {slowo: wartosc_tf}
    """
    licznik = {}
    for slowo in slowa:
        licznik[slowo] = licznik.get(slowo, 0) + 1

    tf = {}
    for slowo, liczba in licznik.items():
        tf[slowo] = liczba / len(slowa)
    return tf

# ── BM25 (zastępuje TF-IDF) ───────────────────────────────────────────────────
# k1 = nasycenie: jak szybko kolejne wystąpienia słowa przestają podbijać wynik
# b  = normalizacja: jak bardzo długość dokumentu wpływa na wynik
# wartości standardowe z literatury — działają dobrze dla większości zbiorów
BM25_K1 = 1.5
BM25_B  = 0.75

def oblicz_idf_bm25(wszystkie_tokeny):
    """
    IDF w wersji BM25 — wzór Robertson/Sparck-Jones.
    Różnica vs klasyczne IDF: log((N - df + 0.5) / (df + 0.5))
    Słowa w ponad połowie dokumentów mogą dostać wynik ujemny (są za pospolite).
    """
    n = len(wszystkie_tokeny)
    idf = {}

    wszystkie_slowa = set()
    for tokeny in wszystkie_tokeny:
        wszystkie_slowa.update(tokeny)

    for slowo in wszystkie_slowa:
        df = sum(1 for tokeny in wszystkie_tokeny if slowo in tokeny)
        idf[slowo] = math.log((n - df + 0.5) / (df + 0.5) + 1)

    return idf


def oblicz_idf(wszystkie_tokeny):
    """zachowane dla kompatybilności — używa BM25"""
    return oblicz_idf_bm25(wszystkie_tokeny)

def zbuduj_wektory_bm25(wszystkie_tokeny, idf):
    """
    Buduje wektory BM25 zamiast TF-IDF.
    Kluczowa różnica: tf jest normalizowane przez długość dokumentu.
    Wzór: idf * (tf * (k1+1)) / (tf + k1 * (1 - b + b * dl/avgdl))
      dl    = długość bieżącego dokumentu
      avgdl = średnia długość dokumentu w całej bazie
    """
    avgdl = sum(len(t) for t in wszystkie_tokeny) / max(len(wszystkie_tokeny), 1)

    wektory = []
    for tokeny in wszystkie_tokeny:
        dl = len(tokeny)
        licznik = {}
        for slowo in tokeny:
            licznik[slowo] = licznik.get(slowo, 0) + 1

        wektor = {}
        for slowo, tf in licznik.items():
            idf_val = idf.get(slowo, 0)
            licznik_bm25 = tf * (BM25_K1 + 1)
            mianownik_bm25 = tf + BM25_K1 * (1 - BM25_B + BM25_B * dl / avgdl)
            wektor[slowo] = idf_val * (licznik_bm25 / mianownik_bm25)

        wektory.append(wektor)

    return wektory

def zbuduj_wektory(wszystkie_tokeny, idf):
    """zachowane dla kompatybilności — używa BM25"""
    return zbuduj_wektory_bm25(wszystkie_tokeny, idf)


# ── Krok 3: podobienstwo cosinusowe ──────────────────────────────────────────

def podobienstwo_cosinusowe(wektor_a, wektor_b):
    """
    mierzy jak bardzo dwa wektory sa do siebie podobne.
    wynik od 0 (brak podobienstwa) do 1 (identyczne).

    wzor: cos(theta) = (A . B) / (|A| * |B|)
    """
    # iloczyn skalarny - suma iloczynow wspolnych slow
    iloczyn = sum(
        wartosc * wektor_b[slowo]
        for slowo, wartosc in wektor_a.items()
        if slowo in wektor_b
    )
    dlugosc_a = math.sqrt(sum(v ** 2 for v in wektor_a.values()))
    dlugosc_b = math.sqrt(sum(v ** 2 for v in wektor_b.values()))

    if dlugosc_a == 0 or dlugosc_b == 0:
        return 0.0

    return iloczyn / (dlugosc_a * dlugosc_b)


# ── Glowna klasa wyszukiwarki ─────────────────────────────────────────────────

class Wyszukiwarka:

    def __init__(self, plik_bazy):
        import pickle, os
        cache = plik_bazy.replace(".json", "_cache.pkl")

        print("Ladowanie bazy wiedzy...")
        with open(plik_bazy, 'r', encoding='utf-8') as f:
            self.fragmenty = json.load(f)

        # użyj cache jeśli baza się nie zmieniła
        baza_mtime = os.path.getmtime(plik_bazy)
        if os.path.exists(cache) and os.path.getmtime(cache) > baza_mtime:
            print("Wczytywanie indeksu z cache...")
            with open(cache, 'rb') as f:
                self.idf, self.wektory, self.wszystkie_tokeny = pickle.load(f)
        else:
            print("Budowanie indeksu TF-IDF...")
            self.wszystkie_tokeny = [tokenizuj(f['tresc']) for f in self.fragmenty]
            self.idf     = oblicz_idf(self.wszystkie_tokeny)
            self.wektory = zbuduj_wektory(self.wszystkie_tokeny, self.idf)
            with open(cache, 'wb') as f:
                pickle.dump((self.idf, self.wektory, self.wszystkie_tokeny), f)
            print("   Zapisano cache")

        print(f"   Zaindeksowano {len(self.fragmenty)} fragmentow")
        print(f"   Slownik: {len(self.idf)} unikalnych slow\n")

    def szukaj(self, pytanie, n_wynikow=1):
        """
        dla podanego pytania zwraca n najbardziej pasujacych fragmentow.
        """
        tokeny_pytania = tokenizuj(pytanie)
        if not tokeny_pytania:
            return []
        # korekta literówek – każde słowo porównywane ze słownikiem IDF
        tokeny_pytania = [popraw_literowke(t, self.idf) for t in tokeny_pytania]

        # rozszerzanie zapytania – doklejamy unikalne słowa z właściwego paragrafu
        rozszerzenie = []
        for tok in tokeny_pytania:
            if tok in ROZSZERZENIA_ZAPYTAN:
                dodatkowe = tokenizuj(ROZSZERZENIA_ZAPYTAN[tok])
                rozszerzenie.extend(dodatkowe)
        # sprawdź frazy dwuwyrazowe
        pytanie_lower = usun_polskie_znaki(pytanie.lower())
        for fraza, rozszerzenie_frazy in ROZSZERZENIA_ZAPYTAN.items():
            if ' ' in fraza and fraza in pytanie_lower:
                rozszerzenie.extend(tokenizuj(rozszerzenie_frazy))
        tokeny_pytania = tokeny_pytania + rozszerzenie

        tf_pytania    = oblicz_tf(tokeny_pytania)
        wektor_pytania = {
            slowo: tf_val * self.idf.get(slowo, 0)
            for slowo, tf_val in tf_pytania.items()
        }

        wyniki = [
            (podobienstwo_cosinusowe(wektor_pytania, wf), i)
            for i, wf in enumerate(self.wektory)
        ]
        wyniki.sort(reverse=True)

        return [
            {
                "tytul":        self.fragmenty[i]['tytul'],
                "tresc":        self.fragmenty[i]['tresc'],
                "podobienstwo": round(podobienstwo, 4)
            }
            for podobienstwo, i in wyniki[:n_wynikow]
        ]


# ── Test ──────────────────────────────────────────────────────────────────────

def main():
    w = Wyszukiwarka(PLIK_BAZY)

    pytania_testowe = [
        "ile razy mozna powtarzac egzamin",
        "kiedy mozna wziac urlop dziekanski",
        "jak oblicza sie srednia ocen",
        "co grozi za nieobecnosci na zajeciach",
        "kiedy mozna zostac skreslanym z listy studentow",
        "ile semestrów trwają studia inzynierskie",
        "jak wyglada praca dyplomowa",
    ]

    for pytanie in pytania_testowe:
        print(f"Pytanie: {pytanie}")
        wyniki = w.szukaj(pytanie, n_wynikow=1)
        if wyniki:
            w1 = wyniki[0]
            print(f"  Paragraf:     {w1['tytul']}")
            print(f"  Podobienstwo: {w1['podobienstwo']}")
            print(f"  Fragment:     {w1['tresc'][:200]}...")
        print()


if __name__ == "__main__":
    main()
