"""
test.py – automatyczne testy wyszukiwarki
Uruchom: python test.py
Sprawdza czy 20 pytań trafia w właściwy paragraf.
"""
import sys
import os

try:
    # gdy uruchamiasz z katalogu v2 (pakiet widoczny)
    from core.wyszukiwarka import Wyszukiwarka
except ImportError:
    # fallback: gdy uruchamiasz plik bezpośrednio z tests/
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from core.wyszukiwarka import Wyszukiwarka

TESTY_LATWE = [
    # § 18 Egzaminy
    ("ile razy mozna podejsc do egzaminu",          "Egzamin"),
    ("co zrobic jak nie zdam egzaminu",             "Egzamin"),
    ("czy moge zdawac egzamin przed sesja",         "Egzamin"),
    ("ile dni miedzy pierwszym a drugim terminem",  "Egzamin"),
    ("kto moze uniewaznic egzamin",                 "Egzamin"),
    ("czy moge poprawic egzamin",                   "Egzamin"),
    ("kiedy jest poprawka egzaminu",                "Egzamin"),
    ("egzamni",                                     "Egzamin"),   # literówka

    # § 20 Egzamin komisyjny
    ("co to jest egzamin komisyjny",                "komisyjny"),
    ("ile mam czasu na wniosek komisyjny",          "komisyjny"),
    ("kto jest w komisji egzaminacyjnej",           "komisyjny"),
    ("czy moge miec obserwatora na egzaminie",      "komisyjny"),

    # § 16 Realizacja zajęć / nieobecności
    ("co grozi za nieobecnosci",                    "Realizacja"),
    ("ile nieobecnosci mozna miec",                 "Realizacja"),
    ("mam 3 nieobecnosci czy to duzo",              "Realizacja"),
    ("jak usprawiedliwic nieobecnosc",              "Realizacja"),
    ("kto ustala limit nieobecnosci",               "Realizacja"),

    # § 19 Skala ocen
    ("jakie sa oceny w regulaminie",                "Skala"),
    ("ile procent na piatke",                       "Skala"),
    ("ile procent na czworke",                      "Skala"),
    ("ile procent na trojke",                       "Skala"),
    ("ile procent na cztery i pol",                 "Skala"),
    ("jaka jest najnizsza ocena zaliczajaca",       "Skala"),

    # § 27 Urlopy
    ("kiedy mozna wziac urlop dziekanski",          "Urlop"),
    ("urlop zdrowotny jak dostac",                  "Urlop"),
    ("czy moge wziac urlop bo jestem w ciazy",      "Urlop"),
    ("ile urlopow dziekanskich moge wziac",         "Urlop"),
    ("czy podczas urlopu mam prawa studenta",       "Urlop"),
    ("urlop?",                                      "Urlop"),     # krótkie

    # § 33 Skreślenia
    ("kiedy mozna zostac skreslanym",               "Skreśl"),
    ("jak zlozyc rezygnacje ze studiow",            "Skreśl"),
    ("co grozi za niezapisanie sie na zajecia",     "Skreśl"),

    # § 34 Wznowienia
    ("jak wznowic studia po skreslanym",            "Wznow"),
    ("ile razy mozna wznowic studia",               "Wznow"),
    ("ile mam czasu na wznowienie studiow",         "Wznow"),
    ("jak wznowic studia",                          "Wznow"),

    # § 22 Powtarzanie przedmiotu
    ("co to jest powtarzanie przedmiotu",           "Powtarz"),
    ("ile razy mozna powtarzac przedmiot",          "Powtarz"),
    ("czy powtarzanie jest platne",                 "Powtarz"),
    ("kiedy mozna powtarzac semestr",               "Powtarz"),

    # § 35 Praca dyplomowa
    ("jak wyglada praca dyplomowa",                 "Dyplom"),
    ("ile osob moze pisac wspolna prace",           "Dyplom"),
    ("czy praca jest sprawdzana antyplagiatem",     "Dyplom"),
    ("w jakim jezyku pisze sie prace dyplomowa",    "Dyplom"),
    ("kto to jest promotor",                        "Dyplom"),

    # § 11 Organizacja roku
    ("jak dlugo trwa semestr",                      "Organ"),
    ("ile tygodni ma semestr",                      "Organ"),
    ("kiedy konczy sie sesja letnia",               "Organ"),
    ("ile dni trwa sesja egzaminacyjna",            "Organ"),

    # § 38 Oceny za studia
    ("jak oblicza sie srednia ocen",                "Skala ocen"),
    ("kiedy dostane wyróznienie",                   "Oceny za"),

    # § 23 Praktyki
    ("jak wyglada praktyka zawodowa",               "Praktyk"),
    ("czy moge zaliczyc praktyke bez odbywania",    "Praktyk"),
]


# Pytania bardziej potoczne / z literowkami
TESTY_TRUDNE = [
    ("egzamni",                                     "Egzamin"),
    ("ak liczona jest ocena koncowa studiow",       "Oceny za"),
    ("ile wazy ocena z pracy dyplomowej",           "Oceny za"),
    ("jak policzyc koncowy wynik studiow",          "Oceny za"),
    ("czy da sie miec obserwatora na egzaminie",    "komisyjny"),
    ("co grozi jak nie chodze na zajecia",          "Realizacja"),
    ("jak dlugo trwa semestr",                      "Organ"),
    ("urlop?",                                      "Urlop"),
    ("jak wznowic studia po skresleniu",            "Wznow"),
    ("czy praca dyplomowa ma antyplagiat",          "Dyplom"),
]


# Testy graniczne: paragrafy, ktore model czesto myli
TESTY_REGRESYJNE = [
    # 19 vs 38
    ("jaka jest skala ocen",                        "Skala"),
    ("ile procent na piatke",                       "Skala"),
    ("jak liczona jest ocena koncowa studiow",      "Oceny za"),
    ("czy ocena pracy dyplomowej liczy sie do wyniku", "Oceny za"),

    # 18 vs 20
    ("ile dni miedzy terminami egzaminu",           "Egzamin"),
    ("co to jest egzamin komisyjny",                "komisyjny"),
    ("kto jest w komisji egzaminacyjnej",           "komisyjny"),

    # 16 vs 33
    ("co grozi za nieobecnosci",                    "Realizacja"),
    ("co grozi za niezapisanie sie na zajecia",     "Skreśl"),
]


# Wybierz zakres testow:
# TESTY = TESTY_LATWE
# TESTY = TESTY_LATWE + TESTY_TRUDNE
TESTY = TESTY_LATWE + TESTY_TRUDNE + TESTY_REGRESYJNE

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