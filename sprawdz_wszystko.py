import glob
import subprocess
import sys
from html.parser import HTMLParser

# 1. Kolorowanie konsoli dla czytelności z ręki
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_krok(nazwa):
    print(f"\n{YELLOW}>> ROZPOCZYNANIE: {nazwa}{RESET}")

def print_sukces(nazwa):
    print(f"{GREEN}[OK] {nazwa} działa perfekcyjnie.{RESET}")

def print_porazka(nazwa, blady_log=""):
    print(f"{RED}[BŁĄD] {nazwa} nie zaliczony!{RESET}")
    if blady_log:
        print(blady_log)

# Specjalny parser do kontroli frontendu "w locie" bez zewnętrznych maszyn.
class FrontendTester(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stos_tagow = []
        self.bledy = []

    def handle_starttag(self, tag, attrs):
        if tag not in ["br", "hr", "img", "input", "meta", "link"]:
            self.stos_tagow.append(tag)

    def handle_endtag(self, tag):
        if tag not in ["br", "hr", "img", "input", "meta", "link"]:
            if not self.stos_tagow:
                self.bledy.append(f"Znaleziono zamknięcie tagu </{tag}> ale wcześniej nie został on otwarty!")
            elif self.stos_tagow[-1] == tag:
                self.stos_tagow.pop()
            else:
                self.bledy.append(f"Oczekiwano zamknięcia </{self.stos_tagow[-1]}>, ale napotkano </{tag}>. Złamana gałąź DOM w locie!")


def sprawdz_front_end():
    print_krok("Kontrola Front-Endu (HTML)")
    pliki_html = glob.glob('v2/templates/**/*.html', recursive=True)
    wszystko_ok = True

    for plik in pliki_html:
        with open(plik, 'r', encoding='utf-8') as f:
            kod_strony = f.read()

        tester = FrontendTester()
        
        try:
            tester.feed(kod_strony)
            if tester.bledy:
                wszystko_ok = False
                print(f" {RED}- {plik}:{RESET}")
                for b in tester.bledy:
                    print(f"    - {b}")
        except Exception as e:
            wszystko_ok = False
            print(f" {RED}- {plik}: BŁĄD WEWNĘTRZNY SKŁADNI: {e}{RESET}")

    if wszystko_ok:
        print_sukces("Logika wcięcia HTML")
    return wszystko_ok


def upewnij_sie_o_linter() -> bool:
    """Instaluje Flake8 z powłoki lokalnej jeśli jest wymagany w repozytorium"""
    try:
        import flake8  # noqa: F401
        return True
    except ImportError:
        print(f" {YELLOW}(Trwa wstrzykiwanie wbudowanego testera Flake8...){RESET}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "flake8", "-q"])
            return True
        except Exception as e:
            print_porazka("Brak mechanizmu testującego, nie udało się zainstalować Flake8", str(e))
            return False

def sprawdz_backend():
    print_krok("Kontrola Logiki Algorytmów i Środowiska (Python)")
    
    if not upewnij_sie_o_linter():
        return False

    komenda = [sys.executable, "-m", "flake8", ".", "--exclude", "venv,.git,__pycache__,v1/", "--select=E9,F63,F7,F82"]
    wynik = subprocess.run(komenda, capture_output=True, text=True)

    if wynik.returncode == 0:
        print_sukces("Syntaktyka i kod plików backendowych .py")
        return True
    else:
        # Próba sformatowania obfitych logów na ludzkie odniesienia
        bledy = wynik.stdout.split('\n')
        print_porazka(f"W plikach Pythona odnalazłem usterki (Ostrzeżenia kompilacji: {len(bledy)-1}):")
        
        max_wys = 15
        for licznik, zgloszenie in enumerate(bledy):
            if not zgloszenie.strip(): continue
            if licznik < max_wys:
                print(f"   - {zgloszenie}")
        
        if len(bledy) > max_wys:
            print(f"   ... i {len(bledy) - max_wys} kolejnych usterek.")
        
        return False

def symulacja_kompilacji():
    print_krok("Integracja Importowa Aplikacji Serwerowej")
    """Próbuje wylistować brakujące pakiety potrzebne silnikom by powiadomić na czas."""
    komenda = [sys.executable, "-c", "import sys; sys.path.insert(0, './v2'); import app"]
    wynik = subprocess.run(komenda, capture_output=True, text=True)
    if wynik.returncode == 0:
         print_sukces("Główny Serwer wczytuje się z plików stabilnie (Dry run).")
         return True
    else:
         print_porazka("Aplikacja zgłasza krytyczny błąd ładowania serwera. Załamała się podczas próby symulacji!", wynik.stderr)
         return False

def testuj_wszystko():
    # Flaga sukcesu
    sukces = True
    
    print("\n" + "="*50)
    print("   [GLOBALNY SKANER BŁĘDÓW - ASYSTENT PWR]")
    print("     Odpalamy filtry bezpieczeństwa całego obszaru...")
    print("="*50)
    
    # KROK 1: Frontend
    if not sprawdz_front_end():
        sukces = False

    # KROK 2: Test statyczny backendu (linter po calym pliku)
    if not sprawdz_backend():
        sukces = False
        
    # KROK 3: Dry-run symulacja 
    if not symulacja_kompilacji():
        sukces = False

    print("\n" + "="*50)
    if sukces:
         print(f"{GREEN}[X] TWOJA ARCHITEKTURA ZDAŁA EGZAMIN. GOTOWY DO PUSZCZANIA DO GITA (COMMIT){RESET}")
         sys.exit(0)
    else:
         print(f"{RED}[!] PRODUKCJA ZABLOKOWANA. W PLIKACH WYKRYTO USTERKI, NALEŻY JE NAPRAWIĆ!{RESET}")
         sys.exit(1)

if __name__ == "__main__":
    testuj_wszystko()
