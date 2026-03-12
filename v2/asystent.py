"""
asystent.py - Krok 3 wersji 2.0
Glowny program - interfejs rozmowy z asystentem regulaminowym.
Laczy parser (baza_wiedzy.json) z wyszukiwarka (TF-IDF).
"""

import os
import json
from wyszukiwarka import Wyszukiwarka


PLIK_BAZY  = "baza_wiedzy.json"
PROG_PEWNOSCI = 0.05   # minimalny wynik podobienstwa zeby odpowiedziec


# ── Formatowanie odpowiedzi ───────────────────────────────────────────────────

def formatuj_odpowiedz(wynik):
    """
    formatuje znaleziony fragment regulaminu jako odpowiedz.
    pokazuje tytul paragrafu i jego tresc.
    """
    tytul = wynik['tytul']
    tresc = wynik['tresc']
    podobienstwo = wynik['podobienstwo']

    # skroc tresc do 600 znakow zeby nie zalewac ekranu
    if len(tresc) > 600:
        tresc = tresc[:600] + "..."

    odpowiedz  = f"\n{'='*60}\n"
    odpowiedz += f"Paragraf: {tytul}\n"
    odpowiedz += f"{'─'*60}\n"
    odpowiedz += f"{tresc}\n"
    odpowiedz += f"{'─'*60}\n"
    odpowiedz += f"Pewnosc dopasowania: {int(podobienstwo * 100)}%\n"
    odpowiedz += f"{'='*60}\n"

    return odpowiedz


def formatuj_kilka_wynikow(wyniki):
    """
    gdy uzytkownik pyta /szukaj, pokazuje kilka najlepszych wynikow.
    """
    tekst = f"\n{'='*60}\n"
    tekst += f"Znaleziono {len(wyniki)} pasujacych fragmentow:\n"
    for i, w in enumerate(wyniki, 1):
        tekst += f"\n  [{i}] {w['tytul']} "
        tekst += f"(pewnosc: {int(w['podobienstwo']*100)}%)\n"
        tekst += f"      {w['tresc'][:150]}...\n"
    tekst += f"{'='*60}\n"
    return tekst


# ── Glowna petla rozmowy ──────────────────────────────────────────────────────

def pokaz_pomoc():
    print("""
Komendy specjalne:
  /szukaj <pytanie>  - pokaz 3 najlepsze wyniki dla pytania
  /info              - informacje o bazie wiedzy
  /pomoc             - ta lista komend
  koniec             - zakoncz program
    """)


def pokaz_info(wyszukiwarka):
    print(f"""
Informacje o bazie wiedzy:
  Fragmentow w bazie:  {len(wyszukiwarka.fragmenty)}
  Slow w slowniku:     {len(wyszukiwarka.idf)}
  Plik bazy:           {PLIK_BAZY}
    """)


def main():
    # sprawdz czy baza istnieje
    if not os.path.exists(PLIK_BAZY):
        print(f"Blad: nie znaleziono pliku '{PLIK_BAZY}'")
        print("Najpierw uruchom: python parser.py")
        return

    print("\n" + "="*60)
    print("  ASYSTENT REGULAMINOWY - Politechnika Wroclawska")
    print("="*60)
    print("Zadaj pytanie o regulamin studiow.")
    print("Wpisz '/pomoc' aby zobaczyc komendy, 'koniec' aby wyjsc.")

    # zaladuj wyszukiwarke
    w = Wyszukiwarka(PLIK_BAZY)

    # petla glowna
    while True:
        try:
            print()
            pytanie = input("Ty: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nDo widzenia!")
            break

        # ignoruj puste wejscie
        if not pytanie:
            continue

        # komendy specjalne
        if pytanie.lower() == "koniec":
            print("Do widzenia!")
            break

        elif pytanie.lower() == "/pomoc":
            pokaz_pomoc()

        elif pytanie.lower() == "/info":
            pokaz_info(w)

        elif pytanie.lower().startswith("/szukaj "):
            zapytanie = pytanie[8:].strip()
            wyniki = w.szukaj(zapytanie, n_wynikow=3)
            if wyniki:
                print(formatuj_kilka_wynikow(wyniki))
            else:
                print("Nie znaleziono zadnych wynikow.")

        else:
            # zwykle pytanie - znajdz najlepszy fragment
            wyniki = w.szukaj(pytanie, n_wynikow=1)

            if not wyniki or wyniki[0]['podobienstwo'] < PROG_PEWNOSCI:
                print("\nAsystent: Nie znalazlem informacji na ten temat")
                print("          w regulaminie studiow PWr.")
                print("          Sprobuj zapytac inaczej lub uzyj /szukaj")
            else:
                print("\nAsystent:")
                print(formatuj_odpowiedz(wyniki[0]))


if __name__ == "__main__":
    main()
