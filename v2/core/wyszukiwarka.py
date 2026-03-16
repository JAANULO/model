"""
wyszukiwarka.py - Krok 2 wersji 2.0
Algorytm TF-IDF napisany od zera.
Wyszukuje w bazie wiedzy fragment najbardziej pasujacy do pytania.
"""

import json
import math
import re
import os
try:
    from .slowniki import SYNONIMY, ROZSZERZENIA  # uruchomienie jako pakiet
except ImportError:
    from slowniki import SYNONIMY, ROZSZERZENIA   # uruchomienie pliku bezpośrednio

PLIK_BAZY = os.path.join(os.path.dirname(__file__), '..', 'data', 'baza_wiedzy.json')


# ── Krok 1: przygotowanie tekstu ──────────────────────────────────────────────

def usun_polskie_znaki(tekst):
    """zamienia polskie litery na odpowiedniki bez ogonkow"""
    zamiana = str.maketrans(
        'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ',
        'acelnoszzACELNOSZZ'
    )
    return tekst.translate(zamiana)

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
            if tok in ROZSZERZENIA:
                dodatkowe = tokenizuj(ROZSZERZENIA[tok])
                rozszerzenie.extend(dodatkowe)
            # sprawdź frazy dwuwyrazowe
        pytanie_lower = usun_polskie_znaki(pytanie.lower())
        for fraza, rozszerzenie_frazy in ROZSZERZENIA.items():
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
