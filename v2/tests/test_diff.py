"""
test_diff.py – narzędzie do analizy regresji
Pozwala zapisać baseline testów i porównać go z nową wersją algorytmu.
Użycie:
  python test_diff.py --save     (zapisuje obecne wyniki)
  python test_diff.py --compare  (pokazuje zmiany względem zapisu)
"""
import argparse
import json
import os
import sys

# Ustawienie PYTHONPATH dla folderu v2
skrypt_dir = os.path.dirname(os.path.abspath(__file__))
v2_dir = os.path.dirname(skrypt_dir)
if v2_dir not in sys.path:
    sys.path.insert(0, v2_dir)

try:
    from core.wyszukiwarka import Wyszukiwarka
    from tests.test import TESTY
except ImportError:
    from .test import TESTY

BASELINE_FILE = os.path.join(os.path.dirname(__file__), "baseline.json")

def ran_tests(w):
    """Uruchamia testy i zbiera wyniki w formacie słownika"""
    results = {}
    for pytanie, oczekiwany in TESTY:
        wyniki = w.szukaj(pytanie, n_wynikow=1)
        tytul = wyniki[0]["tytul"] if wyniki else "BRAK"
        results[pytanie] = {
            "oczekiwany": oczekiwany,
            "otrzymany": tytul,
            "sukces": (oczekiwany.lower() in tytul.lower()) if wyniki else False
        }
    return results

def main():
    parser = argparse.ArgumentParser(description="Narzędzie do analizy regresji")
    parser.add_argument("--save", action="store_true", help="Zapisz aktualne wyniki jako baseline")
    parser.add_argument("--compare", action="store_true", help="Porownaj aktualne wyniki z baseline")
    args = parser.parse_args()

    # Ustawienie ścieżek bezwzględnych
    SKRYPT_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(SKRYPT_DIR)
    PLIK_BAZY = os.path.join(BASE_DIR, "data", "baza_wiedzy.json")

    if not os.path.exists(PLIK_BAZY):
        print(f"Blad: Nie znaleziono pliku bazy w {PLIK_BAZY}")
        return

    w = Wyszukiwarka(PLIK_BAZY)

    if args.save:
        print("Uruchamiam testy i zapisuję baseline...")
        res = ran_tests(w)
        with open(BASELINE_FILE, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=4, ensure_ascii=False)
        print(f"Sukces! Zapisano baseline do {BASELINE_FILE}")

    elif args.compare:
        if not os.path.exists(BASELINE_FILE):
            print("Blad: Brak pliku baseline.json. Uruchom najpierw z opcją --save.")
            return

        print("Porównuję obecne wyniki z baseline...")
        with open(BASELINE_FILE, "r", encoding="utf-8") as f:
            baseline = json.load(f)

        current = ran_tests(w)
        diffs = []

        for q, old in baseline.items():
            new = current.get(q)
            if not new: continue
            
            if old["sukces"] != new["sukces"]:
                diffs.append((q, old["sukces"], new["sukces"]))

        if not diffs:
            print("\nStan identyczny! Brak regresji i popraw w skutecznosci.")
        else:
            print(f"\nZnaleziono {len(diffs)} zmian w skutecznosci:")
            for q, old_s, new_s in diffs:
                if new_s:
                    print(f"  ✅ POPRAWA:   '{q}'")
                else:
                    print(f"  ❌ REGRESJA:  '{q}'")
            
            # Podsumowanie liczbowe
            poprawy = len([d for d in diffs if d[2]])
            regresje = len(diffs) - poprawy
            print(f"\nPodsumowanie zmiany: +{poprawy} / -{regresje}")
    else:
        parser.print_help()

if __name__ == "__main__":
    # Obsługa UTF-8 na Windows
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    main()
