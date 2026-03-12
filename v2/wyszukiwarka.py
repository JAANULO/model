"""
wyszukiwarka.py - Krok 2 wersji 2.0
Algorytm TF-IDF napisany od zera.
Wyszukuje w bazie wiedzy fragment najbardziej pasujacy do pytania.
"""

import json
import math
import re


PLIK_BAZY = "baza_wiedzy.json"


# ── Krok 1: przygotowanie tekstu ──────────────────────────────────────────────

def usun_polskie_znaki(tekst):
    """zamienia polskie litery na odpowiedniki bez ogonkow"""
    zamiana = str.maketrans(
        'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ',
        'acelnoszzACELNOSZZ'
    )
    return tekst.translate(zamiana)


def tokenizuj(tekst):
    """
    rozbija tekst na liste slow (tokenow).
    usuwa interpunkcje, zamienia na male litery,
    normalizuje polskie znaki zeby pytania bez ogonkow tez dzialaly.
    """
    tekst = tekst.lower()
    tekst = usun_polskie_znaki(tekst)
    tekst = re.sub(r'[^\w\s]', ' ', tekst)
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
    return [s for s in slowa if s not in stopwords and len(s) > 1]


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


def oblicz_idf(wszystkie_tokeny):
    """
    oblicza idf dla kazdego slowa w calej bazie.
    rzadkie slowa dostaja wysoki wynik, pospolite niski.
    wynik: slownik {slowo: wartosc_idf}
    """
    n = len(wszystkie_tokeny)
    idf = {}

    wszystkie_slowa = set()
    for tokeny in wszystkie_tokeny:
        wszystkie_slowa.update(tokeny)

    for slowo in wszystkie_slowa:
        liczba_fragmentow = sum(
            1 for tokeny in wszystkie_tokeny if slowo in tokeny
        )
        idf[slowo] = math.log(n / (1 + liczba_fragmentow))

    return idf


def zbuduj_wektory(wszystkie_tokeny, idf):
    """
    dla kazdego fragmentu buduje wektor tf-idf.
    wektor to slownik {slowo: wartosc_tfidf}
    """
    wektory = []
    for tokeny in wszystkie_tokeny:
        tf = oblicz_tf(tokeny)
        wektor = {slowo: tf_val * idf.get(slowo, 0)
                  for slowo, tf_val in tf.items()}
        wektory.append(wektor)
    return wektory


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
        print("Ladowanie bazy wiedzy...")
        with open(plik_bazy, 'r', encoding='utf-8') as f:
            self.fragmenty = json.load(f)

        print("Budowanie indeksu TF-IDF...")
        self.wszystkie_tokeny = [
            tokenizuj(f['tresc']) for f in self.fragmenty
        ]
        self.idf     = oblicz_idf(self.wszystkie_tokeny)
        self.wektory = zbuduj_wektory(self.wszystkie_tokeny, self.idf)

        print(f"   Zaindeksowano {len(self.fragmenty)} fragmentow")
        print(f"   Slownik: {len(self.idf)} unikalnych slow\n")

    def szukaj(self, pytanie, n_wynikow=1):
        """
        dla podanego pytania zwraca n najbardziej pasujacych fragmentow.
        """
        tokeny_pytania = tokenizuj(pytanie)
        if not tokeny_pytania:
            return []

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
