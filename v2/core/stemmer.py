"""
stemmer.py – prosty stemmer dla języka polskiego
Obcina końcówki fleksyjne według reguł gramatycznych.
Nie używa żadnych bibliotek – czyste reguły.

Przykłady:
  egzaminów   → egzamin
  urlopowi    → urlop
  zaliczyłem  → zalicz
  nieobecności → nieobecnosc
"""

# Końcówki posortowane od najdłuższych – ważne!
# Najpierw sprawdzamy dłuższe żeby nie obciąć za dużo
# np. "owania" przed "nia" żeby "zaliczowania" → "zalic" a nie "zalicowan"
KONCOWKI = [
    # czasowniki – długie końcówki najpierw
    "owałem", "owałam", "owałeś", "owałaś", "owaliśmy", "owałyśmy",
    "owania", "owanie", "owaniu", "owac",
    "ałem", "ałam", "ałeś", "ałaś", "aliśmy", "ałyśmy",
    "ując", "uję", "ujesz", "ujemy", "ujecie", "ują",
    "yłem", "yłam", "iłem", "iłam",
    "ąc", "ac", "ec", "yc", "ic",

    # rzeczowniki – długie końcówki najpierw
    "osciach", "osciami", "osciom",
    "osci", "ości",
    "iach", "iami", "iom",
    "aniu", "enia", "enie", "aniu",
    "aniu", "owaniu",

    # WAŻNE: "u" na końcu rzeczowników – "przedmiotu" → "przedmiot"
    "owi", "owa", "owe", "owego", "owej", "owym",
    "ami", "ach", "om",
    "ow", "ów",
    "ie",
    "u",   # przedmiotu→przedmiot, urlopu→urlop

    # przymiotniki
    "owego", "owej", "owym",
    "ego", "emu", "iej", "ej",

    # liczba mnoga
    "ym", "im",
    "a", "e",
    "i", "y",
]

# Minimalna długość rdzenia po obcięciu
# Chroni przed obcięciem całego słowa np. "om" → ""
MIN_RDZEN = 4


def stemuj(slowo: str) -> str:
    """
    Zwraca rdzeń słowa po obcięciu końcówki.
    Jeśli żadna końcówka nie pasuje – zwraca słowo bez zmian.
    """
    slowo = slowo.lower().strip()

    for koncowka in KONCOWKI:
        if slowo.endswith(koncowka):
            rdzen = slowo[: -len(koncowka)]
            if len(rdzen) >= MIN_RDZEN:
                return rdzen

    return slowo


def stemuj_liste(slowa: list) -> list:
    """Stemuje całą listę słów."""
    return [stemuj(s) for s in slowa]


# ── test ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    testy = [
        ("egzaminów",    "egzamin"),
        ("egzaminie",    "egzamin"),
        ("egzaminowi",   "egzamin"),
        ("urlopowi",     "urlop"),
        ("urlopów",      "urlop"),
        ("nieobecności", "nieobecnosc"),
        ("zaliczyłem",   "zalicz"),
        ("zaliczenia",   "zaliczen"),
        ("studenta",     "student"),
        ("studentów",    "student"),
        ("skreślenia",   "skreslen"),
        ("wznowienia",   "wznowien"),
    ]

    print("Test stemmera:\n")
    ok = 0
    for slowo, oczekiwany in testy:
        wynik = stemuj(slowo)
        status = "✓" if wynik == oczekiwany else "✗"
        if wynik == oczekiwany:
            ok += 1
        print(f"  {status}  {slowo:20} → {wynik:15} (oczekiwano: {oczekiwany})")

    print(f"\n{ok}/{len(testy)} poprawnych")