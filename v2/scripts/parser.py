"""
parser.py - Krok 1 wersji 2.0
Wczytuje regulamin PDF i dzieli go na fragmenty (paragrafy).
"""

import glob
import json
import os
import re

import pdfplumber

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PLIK_PDF = os.path.join(DATA_DIR, "regulamin.pdf")
PLIK_WYJSCIOWY = os.path.join(DATA_DIR, "baza_wiedzy.json")


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


def przetworz_pdf(sciezka_pdf: str):
    nazwa_pdf = os.path.basename(sciezka_pdf)
    nazwa_json = os.path.splitext(nazwa_pdf)[0] + ".json"
    sciezka_json = os.path.join(DATA_DIR, nazwa_json)

    print(f"\nWczytywanie PDF: {nazwa_pdf}")
    tekst = wczytaj_pdf(sciezka_pdf)
    print(f"   Wczytano {len(tekst)} znakow")

    print("Czyszczenie tekstu...")
    tekst = wyczysc_tekst(tekst)

    print("Dzielenie na fragmenty...")
    fragmenty = podziel_na_fragmenty(tekst)
    print(f"   Podzielono na {len(fragmenty)} fragmentow")

    for frag in fragmenty:
        frag["zrodlo"] = nazwa_json

    zapisz_baze(fragmenty, sciezka_json)
    print(f"Zapisano do: {os.path.abspath(sciezka_json)}")
    return nazwa_pdf, fragmenty


def main():
    pdf_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.pdf")))
    if not pdf_files:
        raise FileNotFoundError(f"Brak plikow PDF w katalogu: {DATA_DIR}")

    wszystkie_fragmenty = []
    for sciezka_pdf in pdf_files:
        nazwa_pdf, fragmenty = przetworz_pdf(sciezka_pdf)
        wszystkie_fragmenty.extend(fragmenty)

        if nazwa_pdf.lower() == "regulamin.pdf":
            # Kompatybilność wsteczna dla starszych skryptów.
            zapisz_baze(fragmenty, PLIK_WYJSCIOWY)
            print("Zapisano kompatybilny plik:", os.path.abspath(PLIK_WYJSCIOWY))

    print(f"\nGotowe. Łącznie zaindeksowano {len(wszystkie_fragmenty)} fragmentów z {len(pdf_files)} dokumentów.")
    return wszystkie_fragmenty


if __name__ == "__main__":
    main()
