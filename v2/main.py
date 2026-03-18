# MAIN v2 - mini-GPT + asystent regulaminowy PWr
# Uruchomienie: python main.py
# Szczegoly i architektura: README.md

import numpy as np
import json
import os
import hashlib
import random
import sqlite3
from datetime import datetime

import torch
torch.backends.cudnn.benchmark = True
torch.backends.cudnn.enabled   = True

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.transformer import MiniGPT, Adam, softmax, URZADZENIE
from shared.tokenizer   import Tokenizer

# ============================================================
# USTAWIENIA
# ============================================================

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
PLIK_DANYCH  = os.path.join(BASE_DIR, "data", "dane.json")
PLIK_CACHE   = os.path.join(BASE_DIR, "data","model_cache.pkl")
PLIK_BAZY    = os.path.join(BASE_DIR, "data", "baza_wiedzy.json")
PLIK_DB      = os.path.join(BASE_DIR, "data", "asystent.db")
WYMIAR       = 128
N_WARSTW     = 4
N_GLOWIC     = 4
DROPOUT      = 0.01
EPOKI        = 5000
LR           = 0.001
MAKS_DLUGOSC = 512    # zwiększony – fragment regulaminu to ~400 znaków
BATCH_SIZE   = 32
PROG_PEWNOSCI = 0.14   # minimalny wynik BM25 żeby użyć kontekstu

# Pobieramy rozszerzenia z centralnego słownika
from core.slowniki import ROZSZERZENIA

# ============================================================
# SQLITE – logi, statystyki, feedback
# ============================================================

def inicjalizuj_db():
    from core.bd import inicjalizuj
    inicjalizuj()


def zapisz_do_db(pytanie, paragraf, podobienstwo):
    from core.bd import zapisz_pytanie
    return zapisz_pytanie(pytanie, paragraf, podobienstwo)


def zapisz_feedback(pytanie_id, ocena):
    from core.bd import zapisz_feedback as bd_zapisz_feedback
    bd_zapisz_feedback(pytanie_id, ocena)


def pokaz_statystyki():
    from core.bd import pobierz_statystyki
    stats = pobierz_statystyki()

    print(f"\n  📊 Statystyki sesji:")
    print(f"     Zadanych pytań:       {stats['pytania']}")
    print(f"     Średnie dopasowanie:  {stats['srednie_podobienstwo']}%")
    if stats.get('top_paragrafy'):
        print(f"     Najczęstsze tematy:")
        for w in stats['top_paragrafy']:
            print(f"       • {w['tytul'][:45]} ({w['n']}×)")
    if stats.get('zle_odpowiedzi'):
        print(f"     Ostatnie złe odpowiedzi (👎):")
        for z in stats['zle_odpowiedzi']:
            print(f"       • '{z['pytanie'][:40]}' → {z['tytul']}")
    print()


# ============================================================
# CACHE – zapis i wczytywanie modelu GPT
# ============================================================

def hash_danych(sciezka):
    """oblicza hash pliku dane.json – wykrywa zmiany danych"""
    with open(sciezka, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def zapisz_cache(model, tokenizer, hash_pliku):
    """zapisuje model PyTorch i tokenizer do pliku cache"""
    dane = {
        "hash":       hash_pliku,
        "tokenizer":  tokenizer,
        "state_dict": model.state_dict(),
        "config": {
            "rozmiar_slownika": tokenizer.rozmiar,
            "wymiar":           model.wymiar,
            "maks_dlugosc":     model.maks_dlugosc,
        }
    }
    torch.save(dane, PLIK_CACHE)
    eksportuj_model(model, tokenizer, hash_pliku)

def wczytaj_cache(model, hash_pliku):
    """
    wczytuje model z cache jeśli dane.json się nie zmieniło.
    zwraca (tokenizer, True) lub (None, False)
    """
    if not os.path.exists(PLIK_CACHE):
        return None, False
    try:
        dane = torch.load(PLIK_CACHE, map_location=URZADZENIE, weights_only=False)
        if dane["hash"] != hash_pliku:
            print("  ⚠️  Dane zmieniły się – trenuję od nowa.\n")
            return None, False
        model.load_state_dict(dane["state_dict"])
        return dane["tokenizer"], True
    except Exception:
        return None, False

def eksportuj_model(model, tokenizer, hash_pliku, sciezka="model_export.pt"):
    """zapisuje skompresowany model do wysyłania na GitHuba"""
    dane = {
        "hash":       hash_pliku,
        "tokenizer":  tokenizer,
        "state_dict": {k: v.half() for k, v in model.state_dict().items()},
        "config": {
            "rozmiar_slownika": tokenizer.rozmiar,
            "wymiar":           model.wymiar,
            "maks_dlugosc":     model.maks_dlugosc,
            "n_warstw":         N_WARSTW,
            "n_glowic":         N_GLOWIC,
            "dropout":          DROPOUT,
        }
    }
    torch.save(dane, sciezka, _use_new_zipfile_serialization=True)
    rozmiar = os.path.getsize(sciezka) / 1024 / 1024
    print(f"  📦 Eksport do '{sciezka}': {rozmiar:.1f} MB (gotowy na GitHub)")

def wczytaj_eksport(model, sciezka="model_export.pt"):
    """wczytuje skompresowany model (np. pobrany z GitHuba)"""
    if not os.path.exists(sciezka):
        return None, False
    try:
        dane  = torch.load(sciezka, map_location=URZADZENIE, weights_only=False)
        state = {k: v.float() for k, v in dane["state_dict"].items()}
        model.load_state_dict(state)
        rozmiar = os.path.getsize(sciezka) / 1024 / 1024
        print(f"  ✅ Wczytano eksport '{sciezka}' ({rozmiar:.1f} MB)")
        return dane["tokenizer"], True
    except Exception:
        return None, False

# ============================================================
# WCZYTAJ DANE
# ============================================================

def wczytaj_dane(sciezka):
    """obsługuje zarówno listę jak i słownik z kluczem 'zdania'"""
    if not os.path.exists(sciezka):
        print(f"❌ Nie znaleziono '{sciezka}'!")
        exit(1)
    with open(sciezka, encoding="utf-8") as f:
        dane = json.load(f)
    if isinstance(dane, list):
        return dane
    return dane.get("zdania", [])

# ============================================================
# TRENING
# ============================================================

def zbuduj_batch(zdania_ids, tokenizer, batch_size, maks_dlugosc):
    probka = random.sample(zdania_ids, min(batch_size, len(zdania_ids)))
    probka = [ids[:maks_dlugosc] for ids in probka if len(ids) >= 2]
    dlugosc = max(len(ids) for ids in probka)

    wejscie_lista, cel_lista = [], []
    for ids in probka:
        w = ids[:-1]
        c = ids[1:].copy()

        # SFT Loss Masking
        idx_token = -1
        for i in range(len(w)):
            tekst_czesciowy = tokenizer.dekoduj(w[:i + 1])
            if tekst_czesciowy.endswith("asystent"):
                idx_token = i
                break

        if idx_token != -1:
            for i in range(idx_token + 1):
                c[i] = -100

        pad_len = dlugosc - 1 - len(w)
        wejscie_lista.append(w + [0] * pad_len)
        cel_lista.append(c + [-100] * pad_len)

    wejscie = torch.tensor(wejscie_lista, dtype=torch.long, device=URZADZENIE)
    cel = torch.tensor(cel_lista, dtype=torch.long, device=URZADZENIE)
    return wejscie, cel

def trenuj(model, optymalizator, zdania_ids, tokenizer):
    kryterium = torch.nn.CrossEntropyLoss(ignore_index=-100)
    n_batchy = max(1, min(20, len(zdania_ids) // BATCH_SIZE))
    calkowita_strata = 0.0

    for _ in range(n_batchy):
        wejscie, cel = zbuduj_batch(zdania_ids, tokenizer, BATCH_SIZE, MAKS_DLUGOSC)
        optymalizator.zeruj_gradienty()
        logits = model.forward(wejscie)
        B, T, V = logits.shape
        strata = kryterium(logits.reshape(B * T, V), cel.reshape(B * T))
        calkowita_strata += strata.item()
        strata.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optymalizator.krok()

    return calkowita_strata / n_batchy

# ============================================================
# WYSZUKIWANIE – rozszerzanie zapytania + BM25 + reranking
# ============================================================

def rozszerz_pytanie(pytanie):
    """
    dodaje słowa kluczowe do pytania na podstawie słownika ROZSZERZENIA.
    np. 'mam poprawkę' → 'mam poprawkę egzamin termin dwukrotnie składanie'
    poprawia trafność BM25 szczególnie dla krótkich i potocznych pytań.
    """
    pytanie_lower = pytanie.lower()
    for fraza, rozszerzenie in ROZSZERZENIA.items():
        if fraza in pytanie_lower:
            return pytanie + " " + rozszerzenie
    # dla bardzo krótkich pytań (1-2 słowa) dodaj wszystkie pasujące synonimy
    if len(pytanie.split()) <= 2:
        try:
            from core.slowniki import SYNONIMY
            slowo = pytanie.strip().lower().rstrip("?!")

            pasujace = list({v for k, v in SYNONIMY.items() if slowo in k})
            if pasujace:
                return pytanie + " " + " ".join(pasujace)
        except ImportError:
            pass
    return pytanie


def szukaj_z_rerankingiem(wyszukiwarka, pytanie, n_wynikow=1):
    """
    Dwuetapowe wyszukiwanie:
    Etap 1 – BM25: szybkie wyszukiwanie po słowach, zwraca top-20
    Etap 2 – reranking przez embeddingi (jeśli embedder.py dostępny)

    Reranking (ponowne rankingowanie) = sprawdzenie top-20 wyników
    dokładniejszą metodą żeby wybrać najlepszy spośród kandydatów.
    """
    pytanie_rozszerzone = rozszerz_pytanie(pytanie)
    wyniki = wyszukiwarka.szukaj(pytanie_rozszerzone, n_wynikow=max(n_wynikow, 20))

    if not wyniki:
        return []

    return wyniki[:n_wynikow]

# ============================================================
# GENEROWANIE ODPOWIEDZI
# ============================================================

def generuj_odpowiedz(pytanie, historia, temperatura, wyszukiwarka, model, tokenizer):
    """
    Pipeline odpowiedzi:
    1. rozszerz pytanie o synonimy/frazy kluczowe
    2. BM25 + opcjonalny reranking -> najlepszy paragraf
    3. odpowiedz formatujemy na podstawie znalezionego fragmentu regulaminu
       (bez generowania tekstu przez mini-GPT)
    """
    from core.formatowanie import formatuj_odpowiedz

    # zachowujemy sygnature funkcji dla zgodnosci z reszta kodu
    _ = (historia, temperatura, model, tokenizer)

    pytanie_clean = pytanie.lower().strip().rstrip("?")

    if wyszukiwarka is None:
        return (
            "Nie mam zaladowanej bazy regulaminu. Uruchom najpierw parser i wyszukiwarke.",
            None,
            0.0,
        )

    wyniki = szukaj_z_rerankingiem(wyszukiwarka, pytanie_clean, n_wynikow=1)
    if not wyniki:
        return (
            "Nie znalazlem odpowiedniego paragrafu. Sprobuj zadac pytanie inaczej.",
            None,
            0.0,
        )

    wynik = wyniki[0]
    paragraf = wynik["tytul"]
    podobienstwo = wynik["podobienstwo"]

    if podobienstwo <= PROG_PEWNOSCI:
        return (
            "Nie jestem pewien odpowiedzi na podstawie regulaminu. "
            "Doprecyzuj pytanie (np. podaj temat: egzamin, urlop, ocena koncowa).",
            None,
            0.0,
        )

    odp = formatuj_odpowiedz(pytanie_clean, wynik)

    if isinstance(odp, dict):
        wstep = odp.get("wstep", "").strip()
        punkty = [p.strip() for p in odp.get("punkty", []) if isinstance(p, str) and p.strip()]
        tekst = (wstep + " " + " ".join(punkty)).strip()
        tekst = " ".join(tekst.split())  # porzadkuje biale znaki

        if not tekst:
            tekst = wynik.get("tresc", "")[:300].strip()

        return tekst, odp.get("tytul", paragraf), odp.get("podobienstwo", podobienstwo)

    tekst = str(odp).strip() if odp is not None else ""
    if not tekst:
        tekst = wynik.get("tresc", "")[:300].strip()

    return tekst, paragraf, podobienstwo



# ============================================================
# GŁÓWNY PROGRAM
# ============================================================

if __name__ == "__main__":

    print("=" * 55)
    print("  MINI-GPT v2 – Asystent Regulaminowy PWr")
    print("=" * 55 + "\n")

    # 0. inicjalizuj bazę SQLite
    inicjalizuj_db()

    # 1. wczytaj dane
    print("📚 Wczytuję dane...")
    zdania        = wczytaj_dane(PLIK_DANYCH)
    aktualny_hash = hash_danych(PLIK_DANYCH)
    print(f"  Załadowano {len(zdania)} zdań.\n")

    # 2. zbuduj model
    print("🧠 Tworzę model...")
    tokenizer_temp = Tokenizer()
    tokenizer_temp.buduj_slownik(zdania)

    model = MiniGPT(
        rozmiar_slownika = tokenizer_temp.rozmiar,
        wymiar           = WYMIAR,
        n_warstw         = N_WARSTW,
        n_glowic         = N_GLOWIC,
        dropout          = DROPOUT,
        maks_dlugosc     = MAKS_DLUGOSC,
    ).to(URZADZENIE)
    print()

    # 3. sprawdź cache → eksport → trenuj
    tokenizer_z_cache, cache_ok = wczytaj_cache(model, aktualny_hash)

    if cache_ok:
        tokenizer = tokenizer_z_cache
        model.ustaw_trening(False)
        print("✅ Wczytano wytrenowany model z cache!")
        print("   (dane.json nie zmieniło się – trening pominięty)\n")

    else:
        tokenizer_export, eksport_ok = wczytaj_eksport(model)
        if eksport_ok:
            tokenizer = tokenizer_export
            model.ustaw_trening(False)
            print("✅ Wczytano model_export.pt – pomijam trening\n")
        else:
            tokenizer     = tokenizer_temp
            zdania_ids    = [tokenizer.koduj(z) for z in zdania]
            optymalizator = Adam(lr=LR, parametry=model.parameters())

            try:
                from tqdm import tqdm
                ma_tqdm = True
            except ImportError:
                ma_tqdm = False
                print("  💡 Zainstaluj tqdm: pip install tqdm\n")

            print(f"⚙️  Trenuję przez {EPOKI} epok...\n")
            model.ustaw_trening(True)

            if ma_tqdm:
                pasek = tqdm(
                    range(1, EPOKI + 1),
                    desc="  Trening",
                    unit="epoka",
                    bar_format="  {l_bar}{bar:40}{r_bar}",
                    dynamic_ncols=True,
                )
                for epoka in pasek:
                    strata = trenuj(model, optymalizator, zdania_ids, tokenizer)
                    pasek.set_postfix(strata=f"{strata:.4f}")
            else:
                for epoka in range(1, EPOKI + 1):
                    strata = trenuj(model, optymalizator, zdania_ids, tokenizer)
                    if epoka % 100 == 0 or epoka == EPOKI:
                        print(f"  Epoka {epoka}/{EPOKI} ({epoka / EPOKI * 100:.0f}%)  strata: {strata:.4f}")

            print(f"\n  ✅ Trening zakończony!")
            model.ustaw_trening(False)
            zapisz_cache(model, tokenizer, aktualny_hash)
            print(f"  💾 Model zapisany do '{PLIK_CACHE}'\n")

    # 4. załaduj wyszukiwarkę (BM25 + opcjonalny reranking)
    print()
    if os.path.exists(PLIK_BAZY):
        from core.wyszukiwarka import Wyszukiwarka
        wyszukiwarka = Wyszukiwarka(PLIK_BAZY)
        # sprawdź czy embedder jest dostępny
        print("  Reranking przez embeddingi: brak")
    else:
        print(f"⚠️  Nie znaleziono '{PLIK_BAZY}' – uruchom najpierw parser.py")
        print("   Model będzie odpowiadał bez kontekstu regulaminu.\n")
        wyszukiwarka = None

    # 5. tryb rozmowy
    print("\n" + "═" * 55)
    print("  💬 ASYSTENT REGULAMINOWY v2")
    print("═" * 55)
    print("  Zadaj pytanie o regulamin studiów PWr.")
    print()
    print("  Komendy: /temp | /szukaj | /feedback | /statystyki")
    print("           /historia | /zapomnij | /info | /pomoc | koniec")
    print("═" * 55 + "\n")

    temperatura   = 0.1
    historia      = []
    ostatnie_pid  = None   # ID ostatniego pytania w SQLite (do feedbacku)

    # ── pętla rozmowy ──────────────────────────────────────────
    while True:
        try:
            wejscie = input("  Ty: ").strip()

            if not wejscie:
                continue

            # ── wyjście ───────────────────────────────────────
            if wejscie.lower() == "koniec":
                print("\n  Do zobaczenia! 👋\n")
                break

            # ── temperatura ───────────────────────────────────
            if wejscie.startswith("/temp"):
                czesci = wejscie.split()
                if len(czesci) == 2:
                    try:
                        temperatura = float(czesci[1])
                        print(f"  ✅ Temperatura: {temperatura}\n")
                    except ValueError:
                        print("  ⚠️  Użycie: /temp 0.1\n")
                continue

            # ── podgląd wyników BM25 bez generowania ──────────
            if wejscie.startswith("/szukaj "):
                zapytanie = wejscie[8:].strip()
                if wyszukiwarka:
                    wyniki = szukaj_z_rerankingiem(wyszukiwarka, zapytanie, n_wynikow=3)
                    print(f"\n  Wyniki dla: '{zapytanie}'")
                    for i, w in enumerate(wyniki, 1):
                        print(f"  [{i}] {w['tytul']} ({int(w['podobienstwo']*100)}%)")
                    print()
                else:
                    print("  ⚠️  Wyszukiwarka niedostępna.\n")
                continue

            # ── feedback dla ostatniej odpowiedzi ──────────────
            # /feedback + lub /feedback -
            if wejscie.startswith("/feedback"):
                czesci = wejscie.split()
                if len(czesci) == 2 and czesci[1] in ("+", "-"):
                    if ostatnie_pid is None:
                        print("  ⚠️  Brak ostatniej odpowiedzi do oceny.\n")
                    else:
                        ocena = 1 if czesci[1] == "+" else -1
                        zapisz_feedback(ostatnie_pid, ocena)
                        print(f"  {'👍 Dziękuję!' if ocena == 1 else '👎 Zapisano, poprawimy.'}\n")
                else:
                    print("  ⚠️  Użycie: /feedback + lub /feedback -\n")
                continue

            # ── statystyki z SQLite ────────────────────────────
            if wejscie == "/statystyki":
                pokaz_statystyki()
                continue

            # ── historia rozmowy ───────────────────────────────
            if wejscie == "/historia":
                if not historia:
                    print("  (brak historii)\n")
                else:
                    print("\n  📜 Historia rozmowy:")
                    for i, (p, o, par) in enumerate(historia, 1):
                        print(f"  {i}. Ty:    {p}")
                        print(f"     Model: {o}")
                        if par:
                            print(f"     Źródło: {par}")
                    print()
                continue

            # ── wyczyść historię ───────────────────────────────
            if wejscie == "/zapomnij":
                historia.clear()
                ostatnie_pid = None
                print("  🗑️  Historia wyczyszczona.\n")
                continue

            # ── info o bazie ───────────────────────────────────
            if wejscie == "/info":
                if wyszukiwarka:
                    print(f"\n  📚 Baza wiedzy:")
                    print(f"     Fragmentów: {len(wyszukiwarka.fragmenty)}")
                    print(f"     Słów w słowniku BM25: {len(wyszukiwarka.idf)}")
                else:
                    print("  ⚠️  Wyszukiwarka niedostępna.")
                print(f"     Plik bazy: {os.path.abspath(PLIK_BAZY)}")
                print(f"     Plik bazy SQLite: {os.path.abspath(PLIK_DB)}\n")
                continue

            # ── pomoc ──────────────────────────────────────────
            if wejscie == "/pomoc":
                print("""
  Komendy:
    /temp 0.1         → temperatura (0.01=deterministyczny, 1.0=losowy)
    /szukaj <pytanie> → pokaż 3 najlepsze paragrafy bez generowania
    /feedback +       → oceń ostatnią odpowiedź jako dobrą  👍
    /feedback -       → oceń ostatnią odpowiedź jako złą    👎
    /statystyki       → pokaż statystyki z bazy SQLite
    /historia         → pokaż historię rozmowy
    /zapomnij         → wyczyść historię
    /info             → informacje o bazie wiedzy
    koniec            → zakończ rozmowę
                """)
                continue

            # ── generuj odpowiedź ──────────────────────────────
            odpowiedz, paragraf, podobienstwo = generuj_odpowiedz(
                wejscie, historia, temperatura,
                wyszukiwarka, model, tokenizer
            )

            print(f"  🤖 Model: {odpowiedz}")
            if paragraf:
                print(f"  📖 Źródło: {paragraf}  ({int(podobienstwo*100)}%)")
            print()
            print("  (oceń odpowiedź: /feedback + lub /feedback -)")
            print()

            # zapisz do SQLite
            ostatnie_pid = zapisz_do_db(wejscie, paragraf, podobienstwo)

            # zapisz do historii w pamięci
            if odpowiedz != "...":
                historia.append((
                    wejscie.lower().strip().rstrip("?"),
                    odpowiedz,
                    paragraf
                ))

        except KeyboardInterrupt:
            print("\n\n  Program zakończony.\n")
            break
