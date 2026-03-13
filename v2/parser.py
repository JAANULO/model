"""
parser.py - Krok 1 wersji 2.0
Wczytuje regulamin PDF i dzieli go na fragmenty (paragrafy).
"""

import pdfplumber
import json
import re
import os

PLIK_PDF = "regulamin.pdf"
PLIK_WYJSCIOWY = "baza_wiedzy.json"


def wczytaj_pdf(sciezka):
    """wczytuje caly tekst z pdf strona po stronie, pomija pierwsze 2 strony (spis tresci)"""
    pelny_tekst = ""
    with pdfplumber.open(sciezka) as pdf:
        for i, strona in enumerate(pdf.pages):
            if i < 2:  # pomij strone tytulowa i spis tresci
                continue
            tekst = strona.extract_text()
            if tekst:
                pelny_tekst += tekst + "\n"
    return pelny_tekst


def wyczysc_tekst(tekst):
    """usuwa naglowki stron i nadmiarowe biale znaki"""
    tekst = re.sub(r'Strona \d+ z \d+', '', tekst)
    # usun linie z samymi kropkami lub cyframi (pozostalosci spisu tresci)
    linie = tekst.split('\n')
    linie = [l for l in linie if not re.match(r'^[\s.\d]+$', l)]
    tekst = '\n'.join(linie)
    tekst = re.sub(r'[ \t]+', ' ', tekst)
    tekst = re.sub(r'\n{3,}', '\n\n', tekst)
    return tekst.strip()


def podziel_na_fragmenty(tekst):
    """dzieli tekst na fragmenty wedlug paragralow regulaminu"""
    fragmenty = []
    wzorzec = r'(?:(?<=\n)|(?<=\n\n))(?=§\s*\d+\.\s+(?!ust\.|pkt)\S)'
    czesci = re.split(wzorzec, tekst)

    for czesc in czesci:
        czesc = czesc.strip()
        if len(czesc) < 80:
            continue
        linie = czesc.split('\n')
        tytul = linie[0].strip()

        # akceptuj tylko paragrafy z nazwą własną
        if not re.match(r'^§\s*\d+\.\s+(?!ust\.|pkt|ust$)\S', tytul) and \
           not re.match(r'^Rozdział\s+[IVX]+', tytul):
            continue

        tresc = re.sub(r'\s+', ' ', ' '.join(linie).strip())
        fragmenty.append({"tytul": tytul, "tresc": tresc})

    return fragmenty


def zapisz_baze(fragmenty, sciezka):
    """zapisuje fragmenty do pliku json"""
    with open(sciezka, 'w', encoding='utf-8') as f:
        json.dump(fragmenty, f, ensure_ascii=False, indent=2)


def main():
    print("Wczytywanie PDF...")
    tekst = wczytaj_pdf(PLIK_PDF)
    print(f"   Wczytano {len(tekst)} znakow")

    print("Czyszczenie tekstu...")
    tekst = wyczysc_tekst(tekst)

    print("Dzielenie na fragmenty...")
    fragmenty = podziel_na_fragmenty(tekst)
    print(f"   Podzielono na {len(fragmenty)} fragmentow\n")

    print("Przykladowe fragmenty:")
    for i, f in enumerate(fragmenty[:5]):
        print(f"\n  [{i}] Tytul: {f['tytul'][:70]}")
        print(f"       Tresc: {f['tresc'][:200]}...")

    print(f"\nZapisywanie do {PLIK_WYJSCIOWY}...")
    zapisz_baze(fragmenty, PLIK_WYJSCIOWY)
    print("Gotowe!")

    #for f in fragmenty:
        #if '34' in f['tytul']:
            #print(f"§34 długość: {len(f['tresc'])}")
            #print(f"§34 treść: {f['tresc'][:200]}")

    print("Zapisano do:", os.path.abspath(PLIK_WYJSCIOWY))
    return fragmenty


if __name__ == "__main__":
    main()
