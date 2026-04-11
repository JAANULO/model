"""
formatowanie.py - przyjazne odpowiedzi na podstawie fragmentu regulaminu
"""

import os
import random
import re
import sys

try:
    from core.slowniki import ROZSZERZENIA
    from core.wyszukiwarka import tokenizuj as _tokenizuj
except ImportError:
    from .slowniki import ROZSZERZENIA
    from .wyszukiwarka import tokenizuj as _tokenizuj


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

def _score_zdanie(zdanie: str, tokeny_pytania: list) -> int:
    """Liczy ile tokenów pytania pojawia się w zdaniu – im więcej, tym lepiej."""
    zdanie_lower = zdanie.lower()
    return sum(1 for t in tokeny_pytania if t in zdanie_lower)


def _score_zdanie(zdanie, tokeny_pytania):
    """Liczy ile tokenów pytania pojawia się w zdaniu."""
    zdanie_lower = zdanie.lower()
    return sum(1 for t in tokeny_pytania if t in zdanie_lower)


def wyciagnij_zdania(tresc, max_zdan=3, szukaj=None, pytanie_tokeny=None):
    tresc = re.sub(r'^§\s*\d+\.\s*\S[^\n\.]{0,60}\.?\s*', '', tresc).strip()
    tresc_split = re.sub(r'(?<!\bust)(?<!\bpkt)(?<!\bart)(?<!\bpoz)\.\s+(?=[A-ZŁŚŻŹ\d])', '|||', tresc)
    czesci = [c.strip() for c in tresc_split.split('|||') if len(c.strip()) > 30]

    oczyszczone = []
    for z in czesci:
        z = re.sub(r'\s*Rozdział\s+[IVX]+[^.]*\.?', '', z)
        z = z.strip().rstrip('.,;: ')
        z = re.sub(r'\([^)]{0,80}\)', '', z).strip()
        z = re.sub(r'\s+\d+$', '', z).strip()
        z = re.sub(r'\s+', ' ', z)
        if len(z) > 30:
            oczyszczone.append(z)

    # sortuj zdania po dopasowaniu do pytania – najlepsze na górę
    if pytanie_tokeny:
        oczyszczone.sort(
            key=lambda z: _score_zdanie(z, pytanie_tokeny),
            reverse=True
        )
    elif szukaj:
        oczyszczone.sort(
            key=lambda z: sum(1 for s in szukaj if s in z.lower()),
            reverse=True
        )

    wynik = []
    for z in oczyszczone[:max_zdan]:
        # pokaż całe zdanie – urwane zdanie jest gorsze niż długie
        wynik.append(z)

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

def formatuj_odpowiedz(pytanie, wynik_wyszukiwarki, najlepsze_zdanie=None, skrot=None, tylko_jedno=False):
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

    # dobierz wstęp: najpierw po pytaniu, potem skoryguj po faktycznym tytule paragrafu
    temat = wykryj_temat(pytanie)
    wstep = WSTEPY.get(temat, WSTEPY["domyślny"])

    tytul_lower = tytul.lower()
    if "oceny za studia" in tytul_lower or "ostateczny wynik studiow" in tytul_lower:
        wstep = "🎓 W kwestii oceny końcowej studiów regulamin mówi:\n"
    elif "skala ocen" in tytul_lower:
        wstep = "📊 W kwestii skali ocen regulamin mówi:\n"

    # wyciągnij kluczowe zdania i sformatuj jako punkty
    #zdania = wyciagnij_zdania(tresc, max_zdan=3)

    SLOWA_KLUCZOWE = {
        "tygodni":    ["tygodni", "tygodnie", "15", "piętnaście"],
        "wznow":      ["wznowi", "ubiegać", "skreśloną", "wniosek"],
        "skresla": ["skreśla", "rezygnacji", "niepodjęcia", "niezłożenia", "niepodjęcia studiów"],
        "egzamin":    ["dwukrotnego", "termin", "prawo do"],
        "urlop":      ["urlop zdrowotny", "urlop dziekański", "udziela"],
    }

    tokeny_pyt = _tokenizuj(pytanie)
    if 'Skala ocen' in tytul or 'skala ocen' in tytul:
        zdania = [wyciagnij_skale_ocen(tresc)]
    else:
        slowa = None
        for fraza, kluczowe in SLOWA_KLUCZOWE.items():
            if fraza in pytanie.lower():
                slowa = kluczowe
                break
        tokeny_pyt = _tokenizuj(pytanie)
        zdania = wyciagnij_zdania(tresc, max_zdan=3, szukaj=slowa, pytanie_tokeny=tokeny_pyt)

    zacheta = random.choice(ZACHETY) if podobienstwo > 0.2 else None

    # Pokaż "pełny paragraf" tylko jeśli punkty to < 40% treści
    pokaz_pelna = len(" ".join(zdania if zdania else [])) < len(tresc) * 0.4

    if najlepsze_zdanie and najlepsze_zdanie not in (zdania or []):
        if tylko_jedno:
            punkty = [najlepsze_zdanie]
        else:
            drugie = None
            if zdania:
                tokeny_pyt = pytanie.lower().split()
                for z in zdania:
                    if z != najlepsze_zdanie and sum(1 for t in tokeny_pyt if t in z.lower()) >= 2:
                        drugie = z
                        break
            punkty = [najlepsze_zdanie] + ([drugie] if drugie else [])
    else:
        punkty = zdania[:1] if tylko_jedno else (zdania[:2] if zdania else [tresc[:200]])

    return {
        "wstep":        skrot if skrot else wstep.strip(),
        "punkty":       [] if skrot else punkty,
        "tytul":        tytul,
        "zacheta":      zacheta,
        "podobienstwo": podobienstwo,
        "pelna_tresc":  tresc,
        "najlepsze_zdanie": najlepsze_zdanie if najlepsze_zdanie else (punkty[0] if punkty else None)
    }


# ── test ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(BASE_DIR, ".."))
    from core.wyszukiwarka import Wyszukiwarka

    w = Wyszukiwarka(os.path.join(BASE_DIR, "..", "data", "baza_wiedzy.json"))

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
