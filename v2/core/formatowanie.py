"""
formatowanie.py - przyjazne odpowiedzi na podstawie fragmentu regulaminu
"""

import re
import random


# ── słowa kluczowe do wykrywania tematu pytania ───────────────────────────────

TEMATY = {
    "egzamin": [
        "egzamin", "egzaminu", "egzaminie", "zdać", "zdawać", "oblać",
        "podejść", "termin", "poprawka", "sesja", "nie zdam", "nie zdałem"
    ],
    "zaliczenie": [
        "zaliczenie", "zaliczyć", "zaliczenia", "kolokwium", "sprawdzian"
    ],
    "urlop": [
        "urlop", "urlopu", "urlopie", "dziekański", "zdrowotny", "przerwa"
    ],
    "skreślenie": [
        "skreślenie", "skreślić", "wydalenie", "skreślony", "skreslanym"
    ],
    "praca_dyplomowa": [
        "praca", "dyplomowa", "dyplomowej", "inżynierska", "magisterska",
        "dyplom", "antyplagiat", "obron"
    ],
    "ocena": [
        "ocena", "oceny", "ocenę", "średnia", "wynik", "pięć", "cztery",
        "trzy", "niedostateczny", "oblicza"
    ],
    "nieobecność": [
        "nieobecność", "nieobecności", "opuścić", "opuszczać", "nie przyjść",
        "opuściłem", "byłem chory"
    ],
    "powtarzanie": [
        "powtarzać", "powtórzyć", "powtarzanie", "drugi raz", "ponownie"
    ],
    "wznowienie": [
        "wznowić", "wznowienie", "wznowienia", "wznowieniu",
        "przywrócenie", "przywrócić", "po skreśleniu"
    ],
}

WSTEPY = {
    "egzamin":         "📝 W sprawie egzaminów regulamin mówi:\n",
    "zaliczenie":      "📝 W kwestii zaliczeń regulamin mówi:\n",
    "urlop":           "🏖️ Jeśli chodzi o urlopy studenckie:\n",
    "skreślenie":      "⚠️ W sprawie skreślenia z listy studentów:\n",
    "praca_dyplomowa": "📄 Jeśli chodzi o pracę dyplomową:\n",
    "ocena":           "📊 W kwestii ocen i wyników:\n",
    "nieobecność":     "📅 Jeśli chodzi o nieobecności na zajęciach:\n",
    "powtarzanie":     "🔄 W kwestii powtarzania przedmiotów:\n",
    "domyślny":        "📋 Zgodnie z regulaminem studiów PWr:\n",
    "wznowienie": "🔄 W sprawie wznowienia studiów regulamin mówi:\n",
}

ZACHETY = [
    "Jeśli masz dodatkowe pytania – pytaj!",
    "Możesz zapytać bardziej szczegółowo.",
    "W razie wątpliwości warto też zapytać w dziekanacie.",
    "Pamiętaj że w sprawach formalnych dziekanat zawsze pomoże.",
]


# ── funkcje pomocnicze ────────────────────────────────────────────────────────

def wykryj_temat(pytanie):
    """wykrywa temat pytania na podstawie słów kluczowych"""
    pytanie_lower = pytanie.lower()
    for temat, slowa in TEMATY.items():
        if any(s in pytanie_lower for s in slowa):
            return temat
    return "domyślny"


def wyciagnij_zdania(tresc, max_zdan=3, szukaj=None):
    # usuń nagłówek paragrafu – np. "§ 18. Egzaminy" lub "§ 11. Organizacja..."
    tresc = re.sub(r'^§\s*\d+\.\s*\S[^\n\.]{0,60}\.?\s*', '', tresc).strip()
    tresc = re.sub(r'\s+\d+\.\s+', ' CIĘCIE ', tresc)
    tresc = re.sub(r'^\d+\.\s+', '', tresc)
    czesci = tresc.split('CIĘCIE')

    if szukaj:
        trafione = [z for z in czesci if any(s in z.lower() for s in szukaj)]
        czesci = trafione + [z for z in czesci if z not in trafione]

    wynik = []
    for z in czesci:
        # usuń nagłówki rozdziałów sklejone z końcem zdania
        z = re.sub(r'\s*Rozdział\s+[IVX]+[^.]*\.?', '', z)
        z = z.strip().rstrip('.,;: ')
        z = re.sub(r'\([^)]{0,80}\)', '', z).strip()
        z = re.sub(r'\s+\d+$', '', z).strip()
        z = re.sub(r'\s+', ' ', z)
        # pomiń za krótkie i za długie

        if 30 < len(z):
            wynik.append(z[:150].rsplit(' ', 1)[0] + ('…' if len(z) > 150 else ''))

        if len(wynik) >= max_zdan:
            break

    return wynik

def wyciagnij_skale_ocen(tresc):
    """specjalna obsługa – wyciąga tabelę ocen jako czytelne punkty"""
    oceny = [
        ("5,0", "bardzo dobry",    "90–100%"),
        ("4,5", "dobry plus",      "80–89%"),
        ("4,0", "dobry",           "70–79%"),
        ("3,5", "dostateczny plus","60–69%"),
        ("3,0", "dostateczny",     "50–59%"),
        ("2,0", "niedostateczny",  "0–49%"),
    ]
    linie = ["  Ocena   Słownie               Próg"]
    linie.append("  " + "─" * 38)
    for cyfra, slowo, prog in oceny:
        linie.append(f"  {cyfra:<8} {slowo:<22} {prog}")
    return "\n".join(linie)

# ── główna funkcja ────────────────────────────────────────────────────────────

def formatuj_odpowiedz(pytanie, wynik_wyszukiwarki):
    """
    tworzy przyjazną odpowiedź na podstawie pytania i wyniku z wyszukiwarki.

    przykład wyjścia:
      📝 W sprawie egzaminów regulamin mówi:
        • Masz prawo do dwóch terminów egzaminu
        • Drugi termin musi być co najmniej 5 dni po pierwszym

      📖 Źródło: § 18. Egzaminy
      💡 Jeśli masz dodatkowe pytania – pytaj!
    """
    if not wynik_wyszukiwarki:
        return (
            "Nie znalazłem informacji na ten temat w regulaminie.\n"
            "Spróbuj zapytać inaczej lub zajrzyj do dziekanatu."
        )

    tytul        = wynik_wyszukiwarki['tytul']
    tresc        = wynik_wyszukiwarki['tresc']
    podobienstwo = wynik_wyszukiwarki['podobienstwo']

    # za niskie dopasowanie
    if podobienstwo < 0.08:
        return (
            "Nie jestem pewien czy mam dokładną odpowiedź na to pytanie.\n"
            f"Najbliższy temat jaki znalazłem to: {tytul}\n\n"
            "Sprawdź w dziekanacie lub przejrzyj pełny regulamin."
        )

    # dobierz wstęp do tematu pytania
    temat = wykryj_temat(pytanie)
    wstep = WSTEPY[temat]

    # wyciągnij kluczowe zdania i sformatuj jako punkty
    #zdania = wyciagnij_zdania(tresc, max_zdan=3)

    SLOWA_KLUCZOWE = {
        "tygodni":    ["tygodni", "tygodnie", "15", "piętnaście"],
        "wznow":      ["wznowi", "ubiegać", "skreśloną", "wniosek"],
        "skresla": ["skreśla", "rezygnacji", "niepodjęcia", "niezłożenia", "niepodjęcia studiów"],
        "egzamin":    ["dwukrotnego", "termin", "prawo do"],
        "urlop":      ["urlop zdrowotny", "urlop dziekański", "udziela"],
    }

    zdania = None
    if 'Skala ocen' in tytul or 'skala ocen' in tytul:
        zdania = [wyciagnij_skale_ocen(tresc)]
    else:
        slowa = None
        for fraza, kluczowe in SLOWA_KLUCZOWE.items():
            if fraza in pytanie.lower():
                slowa = kluczowe
                break
        zdania = wyciagnij_zdania(tresc, max_zdan=3, szukaj=slowa)

    zacheta = random.choice(ZACHETY) if podobienstwo > 0.2 else None

    return {
        "wstep":    wstep.strip(),
        "punkty":   zdania if zdania else [tresc[:150]],
        "tytul":    tytul,
        "zacheta":  zacheta,
        "podobienstwo": podobienstwo,
        "pelna_tresc":  tresc,
    }


# ── test ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from wyszukiwarka import Wyszukiwarka

    w = Wyszukiwarka("baza_wiedzy.json")

    pytania = [
        "co mam zrobić jak nie zdam egzaminu",
        "ile razy mozna powtarzac egzamin",
        "kiedy mozna wziac urlop dziekanski",
        "jak oblicza sie srednia ocen",
        "co grozi za nieobecnosci",
        "kiedy mozna zostac skreslanym z listy",
        "jak wyglada praca dyplomowa",
        "ile osob moze pisac wspolna prace",
    ]

    for pytanie in pytania:
        wyniki = w.szukaj(pytanie, n_wynikow=1)
        wynik  = wyniki[0] if wyniki else None
        odp    = formatuj_odpowiedz(pytanie, wynik)
        print(f"{'='*55}")
        print(f"❓ {pytanie}")
        print(f"{'─'*55}")
        print(odp)
        print()
