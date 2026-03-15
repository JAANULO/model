"""
test.py – automatyczne testy wyszukiwarki
Uruchom: python test.py
Sprawdza czy 20 pytań trafia w właściwy paragraf.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.wyszukiwarka import Wyszukiwarka

TESTY = [
    ("ile razy mozna podejsc do egzaminu",        "Egzamin"),
    ("co zrobic jak nie zdam egzaminu",            "Egzamin"),
    ("kiedy mozna wziac urlop dziekanski",         "Urlop"),
    ("urlop zdrowotny jak dostac",                 "Urlop"),
    ("kiedy mozna zostac skreslanym",              "Skreśl"),
    ("jak wznowic studia po skreslanym",           "Wznow"),
    ("jak oblicza sie srednia ocen",               "Skala ocen"),
    ("jakie sa oceny w regulaminie",               "Skala ocen"),
    ("co grozi za nieobecnosci", "Realizacja"),
    ("ile nieobecnosci mozna miec", "Realizacja"),
    ("jak wyglada praca dyplomowa",                "Dyplom"),
    ("ile osob moze pisac wspolna prace",          "Dyplom"),
    ("jak dlugo trwa semestr",                     "Organ"),
    ("ile tygodni ma semestr",                     "Organ"),
    ("co to jest powtarzanie przedmiotu",          "Powtarz"),
    ("kiedy mozna powtarzac semestr",              "Powtarz"),
    ("jak wyglada praktyka zawodowa",              "Praktyk"),
    ("egzamni",                                    "Egzamin"),   # literówka
    ("urlop?",                                     "Urlop"),     # krótkie
    ("mam 3 nieobecnosci czy to duzo",             "Realizacja"),   # cyfra
]

def main():
    BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
    w = Wyszukiwarka(os.path.join(BASE_DIR, "data", "baza_wiedzy.json"))
    ok = 0
    bledy = []

    for pytanie, oczekiwany_fragment in TESTY:
        wyniki = w.szukaj(pytanie, n_wynikow=1)
        if not wyniki:
            bledy.append((pytanie, oczekiwany_fragment, "BRAK WYNIKÓW"))
            continue
        tytul = wyniki[0]['tytul']
        if oczekiwany_fragment.lower() in tytul.lower():
            ok += 1
        else:
            bledy.append((pytanie, oczekiwany_fragment, tytul))

    print(f"\nWyniki: {ok}/{len(TESTY)} testów zaliczonych")
    if bledy:
        print("\nNiezaliczone:")
        for p, ocz, got in bledy:
            print(f"  ✗ '{p}'")
            print(f"      oczekiwano: '{ocz}'")
            print(f"      otrzymano:  '{got}'")
    else:
        print("Wszystkie testy zaliczone ✓")

if __name__ == "__main__":
    main()