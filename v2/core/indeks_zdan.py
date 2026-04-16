"""
indeks_zdan.py – indeks BM25 na poziomie zdań, nie paragrafów.
Zamiast zwracać cały paragraf, zwraca konkretne zdanie z odpowiedzią.

Jak działa:
  Teraz:   pytanie → paragraf (300 słów) → wyciągnij zdania
  Po:      pytanie → konkretne zdanie (1-2 zdania) → gotowa odpowiedź
"""

import glob
import json
import os
import pickle
import re

try:
    from .wyszukiwarka import (
        oblicz_idf,
        oblicz_tf,
        podobienstwo_cosinusowe,
        tokenizuj,
        zbuduj_wektory,
    )
except ImportError:
    from wyszukiwarka import (
        oblicz_idf,
        oblicz_tf,
        podobienstwo_cosinusowe,
        tokenizuj,
        zbuduj_wektory,
    )


# ── podział paragrafu na zdania ───────────────────────────────────────────────

def podziel_na_zdania(tresc: str) -> list[str]:
    """
    Dzieli treść paragrafu na pojedyncze zdania.
    Ignoruje skróty typu "ust.", "pkt.", "art."
    """
    # usuń nagłówek paragrafu
    tresc = re.sub(r'^§\s*\d+\.\s*\S[^\n\.]{0,60}\.?\s*', '', tresc).strip()

    # podziel po kropce kończącej zdanie
    podzielony = re.sub(
        r'(?<!\bust)(?<!\bpkt)(?<!\bart)(?<!\bpoz)(?<!\bust)(?<!\bm\.in)\.\s+(?=[A-ZŁŚŻŹ\d])',
        '|||',
        tresc
    )
    zdania = []
    for z in podzielony.split('|||'):
        z = z.strip()
        z = re.sub(r'\s*Rozdział\s+[IVX]+[^.]*\.?', '', z).strip()
        z = re.sub(r'\s+', ' ', z)
        # minimalna długość – krótsze zdania nie mają wartości informacyjnej
        if len(z) > 40:
            zdania.append(z)
    return zdania


# ── główna klasa ──────────────────────────────────────────────────────────────

class IndeksZdan:
    """
    Buduje indeks BM25 na poziomie zdań.
    Każde zdanie z każdego paragrafu jest osobnym dokumentem.
    """

    def __init__(self, plik_bazy: str):

        if os.path.isdir(plik_bazy):
            data_dir = plik_bazy
            json_files = sorted(glob.glob(os.path.join(data_dir, '*.json')))
            cache = os.path.join(data_dir, 'baza_wiedzy_zdania_cache.pkl')
        else:
            data_dir = os.path.dirname(os.path.abspath(plik_bazy))
            json_files = [plik_bazy]
            cache = plik_bazy.replace('.json', '_zdania_cache.pkl')

        fragmenty = []
        aktywne_pliki = []
        for sciezka in json_files:
            try:
                with open(sciezka, encoding='utf-8') as f:
                    dane = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue

            if not isinstance(dane, list):
                continue

            nazwa_zrodla = os.path.basename(sciezka)
            licznik = 0
            for frag in dane:
                if not isinstance(frag, dict):
                    continue
                if 'tytul' not in frag or 'tresc' not in frag:
                    continue
                rekord = dict(frag)
                rekord['zrodlo'] = frag.get('zrodlo', nazwa_zrodla)
                fragmenty.append(rekord)
                licznik += 1

            if licznik > 0:
                aktywne_pliki.append(sciezka)

        if not fragmenty:
            raise FileNotFoundError(f"Nie znaleziono poprawnych fragmentow (tytul+tresc) w JSON: {plik_bazy}")

        baza_mtime = max(os.path.getmtime(p) for p in aktywne_pliki)
        if os.path.exists(cache) and os.path.getmtime(cache) > baza_mtime:
            with open(cache, 'rb') as f:
                self.zdania, self.idf, self.wektory = pickle.load(f)
            print(f"  Indeks zdań: {len(self.zdania)} zdań (z cache)")
            return

        # buduj indeks
        self.zdania = []  # lista słowników {tekst, tytul_paragrafu, tresc_paragrafu}
        for fragment in fragmenty:
            for zdanie in podziel_na_zdania(fragment['tresc']):
                self.zdania.append({
                    'tekst':            zdanie,
                    'tytul':            fragment['tytul'],
                    'tresc_paragrafu':  fragment['tresc'],
                    'zrodlo':           fragment.get('zrodlo'),
                })

        wszystkie_tokeny = [tokenizuj(z['tekst']) for z in self.zdania]
        self.idf     = oblicz_idf(wszystkie_tokeny)
        self.wektory = zbuduj_wektory(wszystkie_tokeny, self.idf)

        with open(cache, 'wb') as f:
            pickle.dump((self.zdania, self.idf, self.wektory), f)

        print(f"  Indeks zdań: {len(self.zdania)} zdań z {len(fragmenty)} paragrafów")

    def szukaj(self, pytanie: str, n_wynikow: int = 3) -> list[dict]:
        """
        Zwraca n najbardziej pasujących zdań do pytania.
        Każdy wynik zawiera zdanie + paragraf z którego pochodzi.
        """
        from .slowniki import ROZSZERZENIA
        try:
            from .wyszukiwarka import usun_polskie_znaki, popraw_literowke
        except ImportError:
            from wyszukiwarka import usun_polskie_znaki, popraw_literowke

        tokeny = tokenizuj(pytanie)
        if not tokeny:
            return []

        tokeny = [popraw_literowke(t, self.idf) for t in tokeny]

        # rozszerzenie zapytania
        rozszerzenie = []
        for tok in tokeny:
            if tok in ROZSZERZENIA:
                rozszerzenie.extend(tokenizuj(ROZSZERZENIA[tok]))
        pytanie_lower = usun_polskie_znaki(pytanie.lower())
        for fraza, rozszerzenie_frazy in ROZSZERZENIA.items():
            if ' ' in fraza and fraza in pytanie_lower:
                rozszerzenie.extend(tokenizuj(rozszerzenie_frazy))

        # dodatkowe rozszerzenia specyficzne dla indeksu zdań
        _ROZSZERZENIA_ZDAN = {
            "ile dni": "pieciodniowym odstepem drugi termin wyznacza",
            "miedzy terminami": "pieciodniowym odstepem drugi termin wyznacza",
            "powtarzac przedmiot": "trzecia realizacja dopuszcza druga trzecia",
            "ile razy powtarzac": "trzecia realizacja dopuszcza druga trzecia",
            "nie zdam": "niedostateczny nie przystapil zadnym terminow wystawia",
            "jak nie zdam": "niedostateczny nie przystapil zadnym terminow wystawia",
            "co jak nie": "niedostateczny nie przystapil zadnym terminow wystawia",
            "obleje": "niedostateczny nie przystapil zadnym terminow wystawia",
        }
        for fraza, rozszerzenie_frazy in _ROZSZERZENIA_ZDAN.items():
            if fraza in pytanie_lower:
                rozszerzenie.extend(tokenizuj(rozszerzenie_frazy))

        tokeny = tokeny + rozszerzenie
        tf = oblicz_tf(tokeny)
        wektor_pytania = {
            s: tf_val * self.idf.get(s, 0)
            for s, tf_val in tf.items()
        }

        wyniki = []
        for i, wf in enumerate(self.wektory):
            score = podobienstwo_cosinusowe(wektor_pytania, wf)
            wyniki.append((score, i))

        wyniki.sort(reverse=True)

        return [
            {
                'zdanie':           self.zdania[i]['tekst'],
                'tytul':            self.zdania[i]['tytul'],
                'tresc_paragrafu':  self.zdania[i]['tresc_paragrafu'],
                'zrodlo':           self.zdania[i].get('zrodlo'),
                'podobienstwo':     round(score, 4),
            }
            for score, i in wyniki[:n_wynikow]
            if score > 0.05
        ]