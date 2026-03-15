"""
asystent.py - Krok 3 wersji 2.0
Glowny program - interfejs rozmowy z asystentem regulaminowym.
Laczy parser (baza_wiedzy.json) z wyszukiwarka (TF-IDF).
"""

import os
import json
import logging
from datetime import datetime
from core.wyszukiwarka import Wyszukiwarka
from core.formatowanie import formatuj_odpowiedz


BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
PLIK_BAZY = os.path.join(BASE_DIR, "data", "baza_wiedzy.json")
PLIK_LOG  = os.path.join(BASE_DIR, "logs", "log.txt")
PROG_PEWNOSCI = 0.11

os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

# konfiguracja logowania
logging.basicConfig(
    filename=PLIK_LOG,
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)

def main():

    # sprawdź czy baza istnieje i nie jest pusta
    if not os.path.exists(PLIK_BAZY):
        print(f"\n  ❌ Błąd: nie znaleziono '{PLIK_BAZY}'")
        print(f"     Uruchom najpierw: python parser.py\n")
        logging.error(f"Brak pliku bazy: {os.path.abspath(PLIK_BAZY)}")
        return

    if os.path.getsize(PLIK_BAZY) < 10:
        print(f"\n  ❌ Błąd: plik '{PLIK_BAZY}' jest pusty.")
        print(f"     Uruchom ponownie: python parser.py\n")
        logging.error(f"Plik bazy jest pusty: {os.path.abspath(PLIK_BAZY)}")
        return

    try:
        with open(PLIK_BAZY, encoding="utf-8") as f:
            json.load(f)
    except json.JSONDecodeError:
        print(f"\n  ❌ Błąd: plik '{PLIK_BAZY}' jest uszkodzony.")
        print(f"     Uruchom ponownie: python parser.py\n")
        logging.error(f"Plik bazy uszkodzony: {os.path.abspath(PLIK_BAZY)}")
        return


    print("\n" + "="*55)
    print("  ASYSTENT REGULAMINOWY – Politechnika Wrocławska")
    print("="*55)
    print("  Zadaj pytanie o regulamin studiów.")
    print("  Wpisz 'koniec' aby wyjść, '/pomoc' dla komend.")
    print("="*55 + "\n")

    try:
        w = Wyszukiwarka(PLIK_BAZY)
    except Exception as e:
        print(f"\n  ❌ Błąd podczas ładowania bazy: {e}")
        logging.error(f"Błąd ładowania bazy: {e}")
        return

    historia = []
    logging.info("=== Sesja rozpoczęta ===")

    while True:
        try:
            print()
            pytanie = input("  Ty: ").strip()

        except (KeyboardInterrupt, EOFError):
            logging.info("=== Sesja przerwana ===\n")
            print("\n  Do widzenia!")
            break

        if not pytanie:
            continue

        if pytanie.lower() == "koniec":
            print("\n  Do widzenia!")
            logging.info("=== Sesja zakończona ===\n")
            break

        elif pytanie.lower() == "/pomoc":
            print("""
        Komendy:
    /szukaj <pytanie>  – pokaż 3 najlepsze paragrafy
    /historia          – pokaż historię rozmowy
    /zapomnij          – wyczyść historię
    /info              – informacje o bazie
    /pomoc             – ta lista
    koniec             – zakończ
            """)

        elif pytanie.lower().startswith("/szukaj "):
            zapytanie = pytanie[8:].strip()
            wyniki    = w.szukaj(zapytanie, n_wynikow=3)
            print(f"\n  Znalezione paragrafy:")
            for i, wyn in enumerate(wyniki, 1):
                print(f"  [{i}] {wyn['tytul']} ({int(wyn['podobienstwo']*100)}%)")

        elif pytanie.lower() == "/historia":
            if not historia:
                print("\n  (brak historii)\n")
            else:
                print("\n  📜 Historia rozmowy:")
                for i, (p, _) in enumerate(historia, 1):
                    print(f"  {i}. {p}")
                print()

        elif pytanie.lower() == "/zapomnij":
            historia.clear()
            print("\n  🗑️  Historia wyczyszczona.\n")

        elif pytanie.lower() == "/info":
            print(f"\n  Fragmentów w bazie: {len(w.fragmenty)}")
            print(f"  Słów w słowniku:    {len(w.idf)}\n")

        else:
            ROZSZERZENIA = {
                # egzamin
                "wznow":         "wznowienie studiów przywrócenie praw studenta",
                "drugi raz":     "egzamin termin dwukrotnie składanie",
                "poprawka":      "egzamin termin dwukrotnie składanie",
                "podejsc":       "egzamin termin dwukrotnie składanie",
                "podchodzic":    "egzamin termin dwukrotnie składanie",
                "kolos":         "egzamin zaliczenie termin",
                "obleje":        "egzamin niezdany termin poprawkowy",
                "nie zdam":      "egzamin niezdany termin poprawkowy",
                "nie zdalam":    "egzamin niezdany termin poprawkowy",
                "komisyjny":     "egzamin komisja kwestionowanie oceny",
                "odwolanie":     "egzamin komisja kwestionowanie oceny",
                # zaliczenie / warunek
                "warunek":       "zaliczenie warunkowe powtarzanie przedmiotu",
                "warunkowo":     "zaliczenie warunkowe powtarzanie przedmiotu",
                "niezaliczony":  "zaliczenie powtarzanie przedmiotu",
                # urlop
                "przerwa":       "urlop dziekański semestr zawieszenie",
                "ciaza":         "urlop zdrowotny rodzicielski ciąża",
                "macierzynski":  "urlop rodzicielski ciąża student",
                "wolne":         "urlop dziekański zawieszenie",
                # skreślenie
                "skresla":       "skreślenie lista studentów rezygnacja",
                "wyrzuc":        "skreślenie wydalenie lista studentów",
                "rzucic":        "skreślenie rezygnacja lista studentów",
                "rezygnacja":    "skreślenie rezygnacja lista studentów",
                # czas trwania
                "ile tygodni":   "tygodnie semestr zajęcia kalendarz",
                "ile semestr":   "tygodnie semestr zajęcia kalendarz",
                "tygodni":       "tygodnie semestr zajęcia kalendarz",
                "jak dlugo":     "tygodnie semestr zajęcia kalendarz",
                "ile trwa":      "tygodnie semestr czas trwania",
                # praca dyplomowa
                "promotor":      "praca dyplomowa promotor opiekun",
                "antyplagiat":   "praca dyplomowa plagiat antyplagiat",
                "obron":         "praca dyplomowa obrona egzamin dyplomowy",
                "temat pracy":   "praca dyplomowa temat zmiana",
                # nieobecność
                "choroba":       "nieobecność usprawiedliwienie zwolnienie",
                "l4":            "nieobecność usprawiedliwienie zwolnienie lekarskie",
                "wagary":        "nieobecność zajęcia opuszczenie",
                # stypendia
                "stypendium":    "stypendium socjalne naukowe rektora",
                "zapomoga":      "stypendium zapomoga pomoc finansowa",
                # administracja
                "wniosek":       "dziekan podanie wniosek zgoda",
                "podanie":       "dziekan podanie wniosek zgoda",
                "ios":           "indywidualna organizacja studiów plan",
                # ECTS
                "ects":          "punkty kredyty zaliczenie przedmiot",
                "kredyty":       "punkty ects zaliczenie przedmiot",
            }

            pytanie_do_szukania = pytanie
            for fraza, rozszerzenie in ROZSZERZENIA.items():
                if fraza in pytanie.lower():
                    pytanie_do_szukania = pytanie + " " + rozszerzenie
                    break

            # krótkie pytania (1-2 słowa) – rozszerz o kontekst ze słownika synonimów
            if len(pytanie.split()) <= 2:
                from core.wyszukiwarka import SYNONIMY
                slowo_bazowe = pytanie.strip().lower().rstrip('?!')
                pasujace = [v for k, v in SYNONIMY.items() if slowo_bazowe in k]
                if pasujace:
                    pytanie_do_szukania = pytanie + " " + " ".join(set(pasujace))


            wyniki = w.szukaj(pytanie_do_szukania, n_wynikow=1)
            wynik  = wyniki[0] if wyniki else None

            # drugi paragraf – pokazuj tylko gdy podobieństwo bliskie pierwszemu
            wynik2 = None
            if len(wyniki) == 2:
                roznica = wyniki[0]['podobienstwo'] - wyniki[1]['podobienstwo']
                if roznica < 0.05 or len(pytanie.split()) >= 8:
                    wynik2 = wyniki[1]

            if not wynik or wynik['podobienstwo'] < PROG_PEWNOSCI:
                print()
                print("  ❓ Nie znalazłem informacji na ten temat w regulaminie.")
                print("     Spróbuj zapytać inaczej lub użyj /szukaj aby przejrzeć paragrafy.")
                print()
                logging.warning(f"Brak odpowiedzi: '{pytanie}' (najlepsze: {wynik['podobienstwo'] if wynik else 0:.2f})")
                continue

            odp = formatuj_odpowiedz(pytanie, wynik)
            print()

            if isinstance(odp, dict):
                print(f"  {odp['wstep']}")
                for p in odp['punkty']:
                    print(f"  • {p}")
                print(f"\n  📖 Źródło: {odp['tytul']}")
                if odp['zacheta']:
                    print(f"  💡 {odp['zacheta']}")
            else:
                print(odp)

            if wynik2:
                print()
                print("  📎 Powiązany paragraf:")
                odp2 = formatuj_odpowiedz(pytanie, wynik2)
                print(odp2)

            historia.append((pytanie, odp))
            logging.info(f"P: {pytanie}")
            logging.info(f"O: {wynik['tytul']} ({int(wynik['podobienstwo'] * 100)}%)")


if __name__ == "__main__":
    main()
