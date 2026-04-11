"""
wyszukiwarka.py - Krok 2 wersji 2.0
Algorytm TF-IDF napisany od zera.
Wyszukuje w bazie wiedzy fragment najbardziej pasujacy do pytania.
"""

import glob
import json
import math
import os
import pickle
import re
import time
from collections import Counter

try:
    from core.bd import pobierz_wspolczynniki_zbiorczo
    from core.slowniki import ROZSZERZENIA, SYNONIMY
    from core.stemmer import stemuj
except ImportError:
    from .bd import pobierz_wspolczynniki_zbiorczo
    from .slowniki import ROZSZERZENIA, SYNONIMY
    from .stemmer import stemuj

PLIK_BAZY = os.path.join(os.path.dirname(__file__), '..', 'data', 'baza_wiedzy.json')
MAPA_WAG_TTL = 60
_mapa_wag_cache = {"ts": 0.0, "data": {}}
def _pobierz_mapa_wag_cached():
    obecny_czas = time.time()
    if obecny_czas - _mapa_wag_cache["ts"] <= MAPA_WAG_TTL:
        return _mapa_wag_cache["data"]
    
    _mapa_wag_cache["data"] = pobierz_wspolczynniki_zbiorczo()
    _mapa_wag_cache["ts"] = obecny_czas
    return _mapa_wag_cache["data"]

# ── Krok 1: przygotowanie tekstu ──────────────────────────────────────────────

MAPA_ZNAKOW = str.maketrans('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ')
def usun_polskie_znaki(tekst):
    """zamienia polskie litery na odpowiedniki bez ogonkow"""
    return tekst.translate(MAPA_ZNAKOW)

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


# Cache korekcji literówek – raz obliczone, zapamiętane na całą sesję
_cache_literowek: dict = {}

def popraw_literowke(slowo, slownik, max_odleglosc=1):
    """
    jeśli słowo nie jest w słowniku, znajdź najbliższe przez Levenshteina.
    Wynik jest cachowany – to samo słowo nie jest przeliczane ponownie.
    """
    if slowo in slownik:
        return slowo
    if slowo in _cache_literowek:
        return _cache_literowek[slowo]
    # filtruj kandydatów po długości PRZED Levenshteinem (duże przyspieszenie)
    kandydaci = [s for s in slownik
                 if abs(len(s) - len(slowo)) <= max_odleglosc and s[0] == slowo[0]]
    najlepszy = min(kandydaci, key=lambda s: levenshtein(slowo, s), default=None)
    wynik = najlepszy if (najlepszy and levenshtein(slowo, najlepszy) <= max_odleglosc) else slowo
    _cache_literowek[slowo] = wynik
    return wynik


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

    slowa = tekst.split()
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

        if os.path.isdir(plik_bazy):
            self.data_dir = plik_bazy
            json_files = sorted(glob.glob(os.path.join(self.data_dir, "*.json")))
            cache = os.path.join(self.data_dir, "baza_wiedzy_multi_cache.pkl")
        else:
            self.data_dir = os.path.dirname(os.path.abspath(plik_bazy))
            json_files = [plik_bazy]
            cache = plik_bazy.replace(".json", "_cache.pkl")

        if not json_files:
            raise FileNotFoundError(f"Brak plikow JSON do indeksowania w: {plik_bazy}")

        print("Ladowanie bazy wiedzy... (Wersja z szybkimi paragrafami!)")
        self.fragmenty = []
        aktywne_pliki = []
        for sciezka in json_files:
            try:
                with open(sciezka, 'r', encoding='utf-8') as f:
                    dane = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue

            if not isinstance(dane, list):
                continue

            nazwa_zrodla = os.path.basename(sciezka)
            fragmenty_z_pliku = 0
            for frag in dane:
                if not isinstance(frag, dict):
                    continue
                if "tytul" not in frag or "tresc" not in frag:
                    continue
                rekord = dict(frag)
                rekord["zrodlo"] = frag.get("zrodlo", nazwa_zrodla)
                self.fragmenty.append(rekord)
                fragmenty_z_pliku += 1

            if fragmenty_z_pliku > 0:
                aktywne_pliki.append(sciezka)

        if not self.fragmenty:
            raise FileNotFoundError(f"Nie znaleziono poprawnych fragmentow (tytul+tresc) w JSON: {plik_bazy}")

        # użyj cache jeśli żaden plik źródłowy nie jest nowszy
        baza_mtime = max(os.path.getmtime(p) for p in aktywne_pliki)
        if os.path.exists(cache) and os.path.getmtime(cache) > baza_mtime:
            print("Wczytywanie indeksu z cache...")
            with open(cache, 'rb') as f:
                self.idf, self.wektory, self.wszystkie_tokeny = pickle.load(f)
        else:
            print("Budowanie indeksu TF-IDF...")
            self.wszystkie_tokeny = []
            for f in self.fragmenty:
                # Ważenie tytułów: Powielenie tytułu 3x w tekście sztucznie podnosi mu wektory w BM25
                sklejka = (f['tytul'] + " ") * 3 + f['tresc']
                self.wszystkie_tokeny.append(tokenizuj(sklejka))

            self.idf     = oblicz_idf(self.wszystkie_tokeny)
            self.wektory = zbuduj_wektory(self.wszystkie_tokeny, self.idf)
            with open(cache, 'wb') as f:
                pickle.dump((self.idf, self.wektory, self.wszystkie_tokeny), f)
            print("   Zapisano cache")


        print(f"   Zaindeksowano {len(self.fragmenty)} fragmentow")
        print(f"   Slownik: {len(self.idf)} unikalnych slow\n")

    @staticmethod
    def wykryj_numer_paragrafu(pytanie):
        """Wykrywa numer paragrafu z pytania (np. §18, paragraf 18)."""
        pytanie_czyste = usun_polskie_znaki(pytanie.lower())
        dopasowanie = re.search(r'(?:§\s*|paragraf(?:ie|u|em|owi|ach)?\s+)(\d+)', pytanie_czyste)
        return dopasowanie.group(1) if dopasowanie else None

    def generuj_graf_slow(self, top_k=70):
        """Mapuje całą rozpiętość merytoryczną dokumentu w pary skojarzeń na podstawie sąsiedztwa."""
        
        # Cache na poziomie instancji - graf generujemy ZAWSZE TYLKO RAZ!
        cache_key = f"_graf_cache_{top_k}_dziala"
        if hasattr(self, cache_key):
            return getattr(self, cache_key)
            
        bigramy = Counter()
        wystapienia_wezlow = Counter()
        
        # Mielenie całych akapitów wyraz po wyrazie
        for tokeny in self.wszystkie_tokeny:
            for i in range(len(tokeny) - 1):
                A, B = tokeny[i], tokeny[i+1]
                if len(A) < 3 or len(B) < 3: 
                    continue # śmieci i przyimki
                if A == B:
                    continue # Odrzuca błąd samotnej wyspy (słowo łączące się same ze sobą)
                # Sortowanie, żeby kolejność słów (A->B czy B->A) nie grała roli
                para = tuple(sorted([A, B]))
                bigramy[para] += 1
                
        najczestsze = bigramy.most_common(top_k)
        
        wezly_set = set()
        edges = []
        for (A, B), waga in najczestsze:
            if waga < 2: continue # Odrzucamy przypadek pojedynczy asocjacji
            wystapienia_wezlow[A] += waga
            wystapienia_wezlow[B] += waga
            wezly_set.add(A)
            wezly_set.add(B)
            edges.append({
                "from": A, "to": B, "value": waga, 
                "color": {"color": "rgba(200,200,200,0.3)", "highlight": "#ff3b30"}
            })
            
        nodes = []
        for wezel in wezly_set:
            # Im więcej powiązań przechodzi przez słowo, tym kółko jest potężniejsze 
            wielkosc = 10 + min(wystapienia_wezlow[wezel] * 1.5, 40)
            nodes.append({
                "id": wezel, "label": wezel, "shape": "dot", "size": wielkosc, "color": "#007aff",
                "font": {"color": "#888", "size": max(10, min(14, wielkosc))}
            })
            
        wynik = {"nodes": nodes, "edges": edges}
        
        setattr(self, cache_key, wynik)
        return wynik


    def pobierz_paragraf_po_numerze(self, numer):
        """Zwraca fragment paragrafu po numerze lub None, bez liczenia BM25."""
        numer = str(numer)
        for frag in self.fragmenty:
            liczby_w_tytule = re.findall(r'\d+', frag['tytul'])
            if liczby_w_tytule and liczby_w_tytule[0] == numer:
                return {
                    "tytul": frag['tytul'],
                    "tresc": frag['tresc'],
                    "podobienstwo": 1.0,
                    "zrodlo": frag.get('zrodlo'),
                }
        return None

    def generuj_graf_paragrafow(self):
        """Generuje siatkę relacji między paragrafami na podstawie podobieństwa wektorowego."""
        cache_key = "_graf_paragrafow_cache"
        if hasattr(self, cache_key):
            return getattr(self, cache_key)

        nodes = []
        for frag in self.fragmenty:
            etykieta = frag['tytul'][:35].rstrip() + ("..." if len(frag['tytul']) > 35 else "")
            nodes.append({"id": frag['tytul'], "label": etykieta, "shape": "dot", "size": 18, "color": "#007aff",
                          "font": {"color": "#aaa", "size": 11}})

        edges = []
        for i in range(len(self.wektory)):
            for j in range(i + 1, len(self.wektory)):
                pod = podobienstwo_cosinusowe(self.wektory[i], self.wektory[j])
                if pod > 0.15:
                    edges.append({
                        "from": self.fragmenty[i]['tytul'],
                        "to":   self.fragmenty[j]['tytul'],
                        "value": round(pod, 3),
                        "color": {"color": "rgba(200,255,0,0.3)", "highlight": "#c8ff00"}
                    })

        wynik = {"nodes": nodes, "edges": edges}
        setattr(self, cache_key, wynik)
        return wynik

    def szukaj(self, pytanie, n_wynikow=1, zrodlo=None):
        """
        Dla podanego pytania zwraca n najbardziej pasujacych fragmentow.
        Parametr zrodlo filtruje wyniki do wybranej bazy (dropdown z GUI).
        """
        # Szybka ścieżka: zapytanie o konkretny paragraf bez BM25
        numer_paragrafu = self.wykryj_numer_paragrafu(pytanie)
        if numer_paragrafu:
            trafienie = self.pobierz_paragraf_po_numerze(numer_paragrafu)
            if trafienie:
                return [trafienie]

        # tokenizuj BEZ stemmera – żeby ROZSZERZENIA mogły dopasować klucze
        tokeny_pytania = tokenizuj(pytanie)
        if not tokeny_pytania:
            return []
        tokeny_pytania = [popraw_literowke(t, self.idf) for t in tokeny_pytania]

        rozszerzenie = []
        for tok in tokeny_pytania:
            if tok in ROZSZERZENIA:
                dodatkowe = tokenizuj(ROZSZERZENIA[tok])
                rozszerzenie.extend(dodatkowe)

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

        # Słownik zbiorczy nazywamy 'mapa_wag'
        mapa_wag = _pobierz_mapa_wag_cached()
        wyniki = []

        for i, wf in enumerate(self.wektory):
            podstawa = podobienstwo_cosinusowe(wektor_pytania, wf)
            tytul = self.fragmenty[i]['tytul']

            # Ciągłe uczenie: modyfikujemy wynik na podstawie historii bazy SQLite
            mnoznik = mapa_wag.get(tytul, 1.0)
            wynik_koncowy = podstawa * mnoznik

            wyniki.append((wynik_koncowy, i))

        wyniki.sort(reverse=True)

        kandydaci = [
            {
                "tytul":        self.fragmenty[i]['tytul'],
                "tresc":        self.fragmenty[i]['tresc'],
                "podobienstwo": round(podobienstwo, 4),
                "zrodlo":       self.fragmenty[i].get('zrodlo'),
            }
            for podobienstwo, i in wyniki
            if podobienstwo > 0
        ]

        # Filtrowanie po zrodle (dropdown z frontendu)
        if zrodlo and zrodlo not in ("Wszystkie dokumenty", "odlacz", "", None):
            kandydaci = [k for k in kandydaci if k.get('zrodlo') == zrodlo]

        return kandydaci[:n_wynikow]


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
