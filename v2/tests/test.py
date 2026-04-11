"""
test.py – automatyczne testy wyszukiwarki
Uruchom: python test.py
Sprawdza czy 20 pytań trafia w właściwy paragraf.
"""
import os
import sys

try:
    from core.wyszukiwarka import Wyszukiwarka
except ImportError:
    # Fallback dla uruchamiania bezpośredniego z folderu tests/
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
    ("co grozi jak nie chodze na zajecia",          "Realizacja"),
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
    ("jak liczona jest ocena koncowa studiow",      "Oceny za"),
    ("ile wazy ocena z pracy dyplomowej",           "Oceny za"),
    ("jak policzyc koncowy wynik studiow",          "Oceny za"),
    ("czy ocena pracy dyplomowej liczy sie do wyniku", "Oceny za"),

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

# Dodatkowy pakiet do skanowania bazy wiedzy o nietypowych ułożeniach słowotwórczych (P4)
TESTY_P4_ROZBUDOWANE = [
    # Rejestracje semestralne i Punkty ECTS
    ("ile trzeba miec ects zeby zdac", "Deficyt"),
    ("jaki jest dopuszczalny deficyt punktowy", "Deficyt"),
    ("co jak zabraknie mi punktow ects", "Deficyt"),
    ("czy moge przejsc na kolejny semestr z dlugiem ects", "Deficyt"),
    ("kiedy jest wpis na semestr", "Warunki i tryb zali"),
    
    # Skreślenie i Opłaty
    ("kiedy dziekan moze mnie skreslic", "Skreślenie"),
    ("nie zaplacilem za warunek co teraz", "Skreślenie"),
    ("za co uiszcza sie oplaty", "Opłaty"),
    ("czy powtarzanie semestru jest platne", "Opłaty"),
    ("czy odwolanie od skreslenia jest darmowe", "Skreślenie"),
    
    # Kwestie Pracy Dyplomowej
    ("jak zmienic promotora pracy", "Dyplom"),
    ("kto recenzuje prace dyplomowa", "Dyplom"),
    ("kiedy wolno zdawac egzamin dyplomowy", "Dyplom"),
    ("co jesli recenzent wystawi ocene niedostateczna z dyplomu", "Dyplom"),
    ("kiedy mozna przedluzyc termin zlozenia dyplomu", "Dyplom"),
    ("ile czasu trwa egzamin inzynierski", "Egzamin dypl"),
    
    # Wznowienia i Urlopy
    ("skreslili mnie rok temu czy moge wrocic", "Wznowienia"),
    ("na ile mozna wziac urlop bez podania przyczyny", "Urlop"),
    ("jak napisać podanie o urlop dziekanski", "Urlop"),
    ("czy moge zrezygnowac ze studiow na pierwszym semestrze i wrocic za rok", "Wznowien"),
    
    # Trudne do wymowy lub literówki
    ("ectsys", "Deficyt"),
    ("srednia stypedndiowa", "Skala ocen"),
    ("wznwienie studjuf", "Wznowien"),
    ("dzikanka z powodu choroby", "Urlop"),
    
    # Kwestie Wykładowców i Zaliczeń
    ("czy prowadzacy musi dac sylabus", "Realizacja"),
    ("kto ustanawia kryteria zaliczenia", "Realizacja"),
    ("ile lat ma sie na ukonczenie studiow inzynierskich", "Okres nauki"),
    ("jak usprawiedliwic nieobecnosc w 24 godziny", "Realizacja"),
    ("kto w ustala harmonogram sesji", "Organizacja"),
    ("kto moze byc obecny na warunku", "komisyjny"),
    ("kiedy nastepuje zamkniecie indeksu", "Oceny")
]

# P5: Uzupełnienie do 150 testów – szersze pokrycie paragrafów
TESTY_P5_UZUPELNIAJACE = [
    # § 4: Przyjęcie na studia
    ("jak zostac studentem pwr",                     "Przyjęcie na studia"),
    ("jak sie zapisac na studia",                    "Przyjęcie na studia"),

    # § 6-7: Prawa i obowiązki
    ("jakie sa prawa studenta",                      "Prawa studenta"),
    ("co student moze robic na uczelni",             "Prawa studenta"),
    ("jakie sa obowiazki studenta",                  "Obowiązki studenta"),
    ("co grozi za niewywiazywanie sie z obowiazkow", "Obowiązki studenta"),

    # § 9: Program studiów i etapy
    ("czym jest etap studiow",                       "etapy studiów"),
    ("ile etapow ma studia inzynierskie",            "Program studiów"),
    ("czym jest plan studiow",                       "Program studiów"),

    # § 10: Punkty ECTS
    ("ile punktow ects ma rok studiow",              "Punkty ECTS"),
    ("co to jest punkt ects",                        "Punkty ECTS"),
    ("ile ects mam zrobic zeby zdac rok",            "Punkty ECTS"),

    # § 11: Organizacja roku
    ("kiedy zaczyna sie rok akademicki",             "Organizacja roku"),
    ("ile trwa rok akademicki",                      "Organizacja roku"),
    ("ile tygodni trwa semestr zimowy",              "Organizacja roku"),

    # § 12: Opłaty
    ("czy studia stacjonarne sa platne",             "Odpłatność"),
    ("jak uiszcza sie oplaty za studia",             "Odpłatność"),

    # § 14: Zapisy na zajęcia
    ("jak sie zapisac na przedmiot",                 "Zapisy"),
    ("co to jest rejestracja na zajecia",            "Zapisy"),

    # § 15: Przenoszenie przedmiotów
    ("czy mozna zaliczyc przedmiot z innej uczelni", "Przenoszenie"),
    ("jak przeniesc zaliczenie z innego wydzialu",   "Przenoszenie"),

    # § 17: Zaliczanie przedmiotu
    ("co to jest zaliczenie bez oceny",              "Zaliczanie przedmiotu"),
    ("ile razy mozna poprawiac zaliczenie",          "Zaliczanie przedmiotu"),

    # § 22: Powtarzanie przedmiotu
    ("ile razy moge powtarzac ten sam przedmiot",    "Powtarzanie przedmiotu"),

    # § 23: Praktyki zawodowe
    ("ile tygodni trwaja praktyki zawodowe",         "Praktyki zawodowe"),
    ("kto moze zwolnic z praktyk",                   "Praktyki zawodowe"),
    ("czy praca zawodowa zalicza sie jako praktyka", "Praktyki zawodowe"),

    # § 25: Rozliczanie etapu
    ("jak sie rozlicza semestr",                     "Rozliczanie etapu"),

    # § 29: IOS
    ("co to jest ios na studiach",                   "Indywidualna organizacja"),
    ("kto moze wnioskowac o indywidualny plan",     "Indywidualna organizacja"),

    # § 30: Przeniesienia
    ("czy mozna przeniesc sie z innej uczelni",      "Przeniesienia z innej"),
    ("jak zmienic uczelnie w trakcie studiow",       "Przeniesienia z innej"),

    # § 38: Oceny za studia
    ("jak sie oblicza ostateczny wynik studiow",     "Oceny za studia"),
    ("jak liczona jest srednia na dyplomie",         "Oceny za studia"),

    # § 39: Ukończenie studiów
    ("kiedy dostaje dyplom ukonczenia",              "Ukończenie studiów"),
    ("co zawiera dyplom ukonczenia studiow",         "Ukończenie studiów"),
    ("kiedy mozna odebrac dyplom",                   "Ukończenie studiów"),
    ("ile trwa wydanie dyplomu",                     "Ukończenie studiów"),

    # § 2: Słownik pojęć
    ("co to jest tok studiow",                       "Słownik"),
    ("co oznacza pojecie student w regulaminie",     "Słownik"),
    ("czym jest absolwent w rozumieniu regulaminu",  "Słownik"),

    # § 5: Systemy komunikacji
    ("co to jest edukacja cl na pwr",                "Systemy komunikacji"),
]



# Wybierz zakres testow:

# TESTY = TESTY_LATWE
# TESTY = TESTY_LATWE + TESTY_TRUDNE
TESTY = TESTY_LATWE + TESTY_TRUDNE + TESTY_REGRESYJNE + TESTY_P4_ROZBUDOWANE + TESTY_P5_UZUPELNIAJACE


def main():
    # Użycie ścieżek bezwzględnych dla stabilności na Windows
    SKRYPT_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(SKRYPT_DIR)
    PLIK_BAZY = os.path.join(BASE_DIR, "data", "baza_wiedzy.json")

    if not os.path.exists(PLIK_BAZY):
        print(f"Blad: Nie znaleziono pliku bazy w {PLIK_BAZY}")
        return

    w = Wyszukiwarka(PLIK_BAZY)
    ok = 0
    bledy = []

    print(f"Rozpoczynam testy ({len(TESTY)} przypadkow)...")

    for pytanie, oczekiwany_fragment in TESTY:
        wyniki = w.szukaj(pytanie, n_wynikow=1)
        if not wyniki:
            bledy.append((pytanie, oczekiwany_fragment, "BRAK WYNIKOW"))
            continue
        
        tytul = wyniki[0]['tytul']
        if oczekiwany_fragment.lower() in tytul.lower():
            ok += 1
        else:
            bledy.append((pytanie, oczekiwany_fragment, tytul))

    print(f"\nWyniki: {ok}/{len(TESTY)} testow zaliczonych")
    
    if bledy:
        print("\nNiezaliczone:")
        for p, ocz, got in bledy:
            # Używamy bezpiecznych znaków ASCII zamiast Unicode
            print(f"  [X] '{p}'")
            print(f"      oczekiwano: '{ocz}'")
            print(f"      otrzymano:  '{got}'")
    else:
        print("Wszystkie testy zaliczone [OK]")

if __name__ == "__main__":
    # Wymuszenie UTF-8 dla strumieni wyjściowych na Windows
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    main()