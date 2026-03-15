"""
auto_tester.py – automatyczne testowanie + analiza błędów przez Gemini

Gemini generuje pytania → twój model odpowiada → Gemini ocenia
→ Gemini analizuje błędy → sugeruje konkretne poprawki do ROZSZERZENIA_ZAPYTAN

Wymagania:
    pip install google-generativeai python-dotenv

Klucz API Gemini (darmowy): https://aistudio.google.com/app/apikey
Ustaw w pliku .env:  GEMINI_API_KEY=twój_klucz
"""

import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

try:
    from google import genai
except ImportError:
    print("Zainstaluj: pip install google-genai")
    sys.exit(1)

from core.wyszukiwarka import Wyszukiwarka

# ── konfiguracja ──────────────────────────────────────────────
API_KEY = os.getenv("GEMINI_API_KEY", "")
if not API_KEY:
    print("Brak klucza API. Ustaw GEMINI_API_KEY w pliku .env")
    sys.exit(1)

klient = genai.Client(api_key=API_KEY)

LICZBA_PYTAN  = 2
PLIK_WYNIKOW  = "auto_test_wyniki.json"
PLIK_POPRAWEK = "auto_test_poprawki.py"

# ── pomocnicze ────────────────────────────────────────────────

def zapytaj_gemini(prompt: str, proba=3) -> str:
    for i in range(proba):
        try:
            time.sleep(4)
            return klient.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt
            ).text.strip()

        except Exception as e:
            if i < proba - 1:
                print(f"  ⚠ Gemini błąd ({e}), czekam 5s...")
                time.sleep(5)
            else:
                raise


def parsuj_json(tekst: str):
    if "```" in tekst:
        tekst = tekst.split("```")[1]
        if tekst.startswith("json"):
            tekst = tekst[4:]
    return json.loads(tekst.strip())


# ── kroki ─────────────────────────────────────────────────────

def generuj_pytania(baza: list, liczba: int) -> list:
    tytuły = [p['tytul'] for p in baza]
    prompt = f"""Jesteś studentem Politechniki Wrocławskiej.
Wygeneruj {liczba} różnych, realistycznych pytań które student mógłby zadać
o regulamin studiów. Pytania muszą dotyczyć tych paragrafów:
{json.dumps(tytuły, ensure_ascii=False)}

Pisz pytania potocznie i różnorodnie, np:
- "co mi grozi jak obleje egzamin"
- "ile razy moge powtarzac przedmiot"
- "kiedy moge wziac wolne od studiow"

Zwróć TYLKO listę JSON bez żadnego dodatkowego tekstu:
["pytanie 1", "pytanie 2", ...]"""

    tekst = zapytaj_gemini(prompt)
    return parsuj_json(tekst)


def ocen_odpowiedz(pytanie: str, tytul: str, podobienstwo: float) -> dict:
    prompt = f"""Oceń czy paragraf regulaminu pasuje do pytania studenta.

Pytanie: "{pytanie}"
Znaleziony paragraf: "{tytul}"
Podobieństwo BM25: {podobienstwo*100:.0f}%

Zwróć TYLKO JSON:
{{
  "trafny": true,
  "komentarz": "jedno zdanie dlaczego tak lub nie",
  "oczekiwany_paragraf": null
}}"""

    try:
        tekst = zapytaj_gemini(prompt)
        return parsuj_json(tekst)
    except Exception as e:
        return {"trafny": False, "komentarz": f"błąd oceny: {e}", "oczekiwany_paragraf": None}


def analizuj_bledy(bledy: list, baza: list) -> str:
    if not bledy:
        return ""

    kontekst = {}
    for b in bledy:
        oczekiwany = b.get("oczekiwany_paragraf", "")
        if oczekiwany:
            for p in baza:
                if oczekiwany.lower() in p['tytul'].lower():
                    kontekst[p['tytul']] = p['tresc'][:300]
                    break

    prompt = f"""Analizujesz błędy systemu wyszukiwania BM25 dla regulaminu PWr.
System używa słownika rozszerzeń zapytań (ROZSZERZENIA_ZAPYTAN) który mapuje
słowa kluczowe z pytań na unikalne słowa z właściwych paragrafów.

Błędne odpowiedzi:
{json.dumps(bledy, ensure_ascii=False, indent=2)}

Treści oczekiwanych paragrafów:
{json.dumps(kontekst, ensure_ascii=False, indent=2)}

Dla każdego błędu zaproponuj nowy wpis do słownika ROZSZERZENIA_ZAPYTAN.
Wpisy powinny mapować słowa kluczowe z pytania na unikalne słowa z właściwego paragrafu.

Zwróć TYLKO słownik Python (bez żadnego dodatkowego tekstu):
{{
    "słowo_z_pytania": "unikalne słowa z właściwego paragrafu",
}}"""

    try:
        return zapytaj_gemini(prompt)
    except Exception as e:
        return f"# błąd analizy: {e}"


def zapisz_poprawki(poprawki_tekst: str, bledy: list):
    with open(PLIK_POPRAWEK, "w", encoding="utf-8") as f:
        f.write("# ============================================================\n")
        f.write("# SUGEROWANE POPRAWKI do ROZSZERZENIA_ZAPYTAN w wyszukiwarka.py\n")
        f.write("# Wygenerowane automatycznie przez auto_tester.py\n")
        f.write("# Skopiuj potrzebne wpisy do słownika ROZSZERZENIA_ZAPYTAN\n")
        f.write("# ============================================================\n\n")
        f.write("# Błędne pytania:\n")
        for b in bledy:
            f.write(f"#   ✗ '{b['pytanie']}'\n")
            f.write(f"#     → otrzymano:  '{b['otrzymano']}'\n")
            if b.get('oczekiwany_paragraf'):
                f.write(f"#     → oczekiwano: '{b['oczekiwany_paragraf']}'\n")
        f.write("\n# Sugerowane wpisy do ROZSZERZENIA_ZAPYTAN:\n")
        f.write(poprawki_tekst)
        f.write("\n")


# ── główna funkcja ────────────────────────────────────────────

def uruchom():
    print("=" * 55)
    print("  AUTO-TESTER z analizą błędów")
    print("  Gemini + Asystent Regulaminowy PWr")
    print("=" * 55)

    BASE      = os.path.dirname(os.path.abspath(__file__))
    PLIK_BAZY = os.path.join(BASE, "data", "baza_wiedzy.json")

    with open(PLIK_BAZY, encoding="utf-8") as f:
        baza = json.load(f)

    w = Wyszukiwarka(PLIK_BAZY)

    print(f"\n📝 Generuję {LICZBA_PYTAN} pytań przez Gemini...")
    pytania = generuj_pytania(baza, LICZBA_PYTAN)
    print(f"   Wygenerowano {len(pytania)} pytań\n")

    wyniki = []
    bledy  = []
    trafne = 0

    for i, pytanie in enumerate(pytania, 1):
        print(f"[{i}/{len(pytania)}] {pytanie}")

        rezultaty = w.szukaj(pytanie, n_wynikow=1)
        if not rezultaty:
            print("  → BRAK WYNIKÓW\n")
            bledy.append({
                "pytanie": pytanie, "otrzymano": "BRAK",
                "oczekiwany_paragraf": None, "komentarz": "brak wyników"
            })
            continue

        wynik        = rezultaty[0]
        tytul        = wynik["tytul"]
        podobienstwo = wynik["podobienstwo"]
        print(f"  → {tytul} ({podobienstwo*100:.0f}%)")

        ocena = ocen_odpowiedz(pytanie, tytul, podobienstwo)

        if ocena.get("trafny"):
            trafne += 1
            print(f"  ✓ {ocena.get('komentarz', '')}\n")
        else:
            print(f"  ✗ {ocena.get('komentarz', '')}")
            if ocena.get("oczekiwany_paragraf"):
                print(f"    lepszy: {ocena['oczekiwany_paragraf']}\n")
            else:
                print()
            bledy.append({
                "pytanie":             pytanie,
                "otrzymano":           tytul,
                "oczekiwany_paragraf": ocena.get("oczekiwany_paragraf"),
                "komentarz":           ocena.get("komentarz")
            })

        wyniki.append({
            "pytanie": pytanie, "paragraf": tytul,
            "podobienstwo": podobienstwo, "ocena": ocena
        })

    print("=" * 55)
    print(f"  WYNIKI: {trafne}/{len(pytania)} trafnych")
    print(f"  Trafność: {trafne/len(pytania)*100:.0f}%")
    print("=" * 55)

    if bledy:
        print(f"\n🔍 Analizuję {len(bledy)} błędów przez Gemini...")
        poprawki = analizuj_bledy(bledy, baza)
        zapisz_poprawki(poprawki, bledy)
        print(f"💡 Sugerowane poprawki zapisane do: {PLIK_POPRAWEK}")
        print("   Otwórz plik i skopiuj wpisy do ROZSZERZENIA_ZAPYTAN\n")

    with open(PLIK_WYNIKOW, "w", encoding="utf-8") as f:
        json.dump({
            "trafne": trafne, "total": len(pytania),
            "trafnosc_procent": round(trafne/len(pytania)*100, 1),
            "bledy": bledy, "wyniki": wyniki
        }, f, ensure_ascii=False, indent=2)

    print(f"📊 Pełne wyniki zapisane do: {PLIK_WYNIKOW}")


if __name__ == "__main__":
    uruchom()
