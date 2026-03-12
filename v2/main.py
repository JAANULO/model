# ============================================================
#  MAIN v2 – mini-GPT + asystent regulaminowy PWr
#
#  Uruchom: python main.py
#  Wymagania: pip install numpy pdfplumber tqdm
#
#  Pliki:
#    main.py          ← ten plik
#    transformer.py   ← architektura modelu
#    tokenizer.py     ← słownik tokenów
#    dane.json        ← zdania treningowe (dane_v2.json)
#    wyszukiwarka.py  ← TF-IDF do znajdowania paragrafu
#    baza_wiedzy.json ← przetworzone paragrafy regulaminu
# ============================================================

import numpy as np
import json
import os
import hashlib
import random

import torch
torch.backends.cudnn.benchmark = True
torch.backends.cudnn.enabled   = True

from transformer import MiniGPT, Adam, softmax, URZADZENIE
from tokenizer   import Tokenizer

# ============================================================
# USTAWIENIA
# ============================================================

PLIK_DANYCH  = "dane.json"
PLIK_CACHE   = "model_cache.pkl"
PLIK_BAZY    = "baza_wiedzy.json"
WYMIAR       = 256
N_WARSTW     = 6
N_GLOWIC     = 8
DROPOUT      = 0.05
EPOKI        = 5000
LR           = 0.001
MAKS_DLUGOSC = 512    # zwiększony – fragment regulaminu to ~400 znaków
BATCH_SIZE   = 32

# ============================================================
# CACHE – zapis i wczytywanie modelu
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

def zbuduj_batch(zdania_ids, batch_size, maks_dlugosc):
    probka  = random.sample(zdania_ids, min(batch_size, len(zdania_ids)))
    probka  = [ids[:maks_dlugosc] for ids in probka if len(ids) >= 2]
    dlugosc = max(len(ids) for ids in probka)

    wejscie_lista, cel_lista = [], []
    for ids in probka:
        w       = ids[:-1]
        c       = ids[1:]
        pad_len = dlugosc - 1 - len(w)
        wejscie_lista.append(w + [0] * pad_len)
        cel_lista.append(c    + [0] * pad_len)

    wejscie = torch.tensor(wejscie_lista, dtype=torch.long, device=URZADZENIE)
    cel     = torch.tensor(cel_lista,     dtype=torch.long, device=URZADZENIE)
    return wejscie, cel

def trenuj(model, optymalizator, zdania_ids):
    kryterium        = torch.nn.CrossEntropyLoss(ignore_index=0)
    n_batchy         = max(1, min(20, len(zdania_ids) // BATCH_SIZE))
    calkowita_strata = 0.0

    for _ in range(n_batchy):
        wejscie, cel = zbuduj_batch(zdania_ids, BATCH_SIZE, MAKS_DLUGOSC)
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
# GŁÓWNY PROGRAM
# ============================================================

if __name__ == "__main__":

    print("=" * 55)
    print("  MINI-GPT v2 – Asystent Regulaminowy PWr")
    print("=" * 55 + "\n")

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
                    strata = trenuj(model, optymalizator, zdania_ids)
                    pasek.set_postfix(strata=f"{strata:.4f}")
            else:
                for epoka in range(1, EPOKI + 1):
                    strata = trenuj(model, optymalizator, zdania_ids)
                    if epoka % 100 == 0 or epoka == EPOKI:
                        print(f"  Epoka {epoka}/{EPOKI} ({epoka/EPOKI*100:.0f}%)  strata: {strata:.4f}")

            print(f"\n  ✅ Trening zakończony!")
            model.ustaw_trening(False)
            zapisz_cache(model, tokenizer, aktualny_hash)
            print(f"  💾 Model zapisany do '{PLIK_CACHE}'\n")

    # 4. załaduj wyszukiwarkę regulaminu
    print()
    if os.path.exists(PLIK_BAZY):
        from wyszukiwarka import Wyszukiwarka
        wyszukiwarka = Wyszukiwarka(PLIK_BAZY)
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
    print("  Komendy: /temp 0.1 | /historia | /zapomnij | /pomoc | koniec")
    print("═" * 55 + "\n")

    temperatura  = 0.1
    OKNO_PAMIECI = 3
    historia     = []

    def generuj_odpowiedz(pytanie, historia, temperatura):
        """
        v2: wyszukiwarka TF-IDF znajduje paragraf → mini-GPT generuje odpowiedź
        format wejścia: użytkownik [pytanie] kontekst [fragment] asystent
        """
        pytanie_clean = pytanie.lower().strip().rstrip("?")

        # znajdź pasujący fragment regulaminu
        if wyszukiwarka is not None:
            wyniki = wyszukiwarka.szukaj(pytanie_clean, n_wynikow=1)
        else:
            wyniki = []

        if wyniki and wyniki[0]['podobienstwo'] > 0.05:
            fragment = wyniki[0]['tresc'][:300]   # max 300 znaków
            paragraf = wyniki[0]['tytul']
            kontekst = f"użytkownik {pytanie_clean} kontekst {fragment} asystent"
        else:
            paragraf = None
            kontekst = f"użytkownik {pytanie_clean} asystent"

        ids = tokenizer.koduj(kontekst)

        with torch.no_grad():
            for _ in range(200):
                logits   = model.forward(ids[-MAKS_DLUGOSC:])
                ostatnie = logits[-1].cpu().numpy() / max(temperatura, 0.01)
                probs    = softmax(ostatnie)
                nastepny = int(np.argmax(probs) if temperatura < 0.05
                               else np.random.choice(len(probs), p=probs))
                ids.append(nastepny)
                if "koniec" in tokenizer.dekoduj(ids)[-10:]:
                    break

        tekst = tokenizer.dekoduj(ids)

        # wyciągnij odpowiedź po ostatnim "asystent"
        if "asystent" in tekst:
            idx       = tekst.rfind("asystent") + len("asystent")
            odpowiedz = tekst[idx:]
        else:
            odpowiedz = tekst

        for stop in ["koniec", "użytkownik"]:
            if stop in odpowiedz:
                odpowiedz = odpowiedz[:odpowiedz.index(stop)]

        odpowiedz = odpowiedz.strip()
        return (odpowiedz if odpowiedz else "..."), paragraf

    # ── pętla rozmowy ──────────────────────────────────────────
    while True:
        try:
            wejscie = input("  Ty: ").strip()

            if not wejscie:
                continue

            if wejscie.lower() == "koniec":
                print("\n  Do zobaczenia! 👋\n")
                break

            if wejscie.startswith("/temp"):
                czesci = wejscie.split()
                if len(czesci) == 2:
                    try:
                        temperatura = float(czesci[1])
                        print(f"  ✅ Temperatura: {temperatura}\n")
                    except ValueError:
                        print("  ⚠️  Użycie: /temp 0.1\n")
                continue

            if wejscie == "/historia":
                if not historia:
                    print("  (brak historii)\n")
                else:
                    print("\n  📜 Historia rozmowy:")
                    for i, (p, o) in enumerate(historia, 1):
                        print(f"  {i}. Ty:    {p}")
                        print(f"     Model: {o}")
                    print()
                continue

            if wejscie == "/zapomnij":
                historia.clear()
                print("  🗑️  Historia wyczyszczona.\n")
                continue

            if wejscie == "/pomoc":
                print("""
  Komendy:
    /temp 0.1    → temperatura (0.01=zawsze to samo, 1.0=losowy)
    /historia    → pokaż historię rozmowy
    /zapomnij    → wyczyść pamięć modelu
    koniec       → zakończ rozmowę
                """)
                continue

            # generuj odpowiedź
            odpowiedz, paragraf = generuj_odpowiedz(wejscie, historia, temperatura)
            print(f"  🤖 Model: {odpowiedz}")
            if paragraf:
                print(f"  📖 Źródło: {paragraf}")
            print()

            # zapisz do historii
            if odpowiedz != "...":
                historia.append((wejscie.lower().strip().rstrip("?"), odpowiedz))

        except KeyboardInterrupt:
            print("\n\n  Program zakończony.\n")
            break
