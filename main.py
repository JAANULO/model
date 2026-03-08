# ============================================================
#  MAIN – trening i rozmowa z mini-GPT
#
#  Uruchom: python main.py
#  Wymagania: pip install numpy
#
#  Pliki:
#    main.py         ← ten plik
#    transformer.py  ← architektura modelu
#    tokenizer.py    ← słownik tokenów
#    dane.json       ← zdania treningowe
# ============================================================

import numpy as np
import json
import os
import hashlib

from tokenizer    import Tokenizer
from transformer  import MiniGPT, Adam, softmax

# ============================================================
# USTAWIENIA
# ============================================================

PLIK_DANYCH   = "dane.json"
PLIK_CACHE    = "model_cache.pkl"  # tu zapisujemy wytrenowany model
WYMIAR        = 128      # większy wymiar = więcej pojemności
N_WARSTW      = 4        # więcej warstw = głębszy model
N_GLOWIC      = 4        # głowice Multi-Head Attention
DROPOUT       = 0.1      # 10% dropout przeciw przeuczeniu
EPOKI         = 3000     # więcej epok = lepsze zapamiętanie
LR            = 0.003    # learning rate
MAKS_DLUGOSC  = 64       # dłuższy kontekst
BATCH_SIZE    = 32       # ← NOWE

# ============================================================
# CACHE – zapis i wczytywanie modelu
# ============================================================

def hash_danych(sciezka):
    """Oblicza hash pliku dane.json – wykrywa zmiany danych."""
    with open(sciezka, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def zapisz_cache(model, tokenizer, hash_pliku):
    """
    Zapisuje model PyTorch i tokenizer.
    Używamy torch.save – to właściwy sposób zapisu modeli PyTorch.
    """
    import torch
    dane = {
        "hash":        hash_pliku,
        "tokenizer":   tokenizer,
        "state_dict":  model.state_dict(),   # wszystkie wagi modelu
        "config": {                           # architektura modelu
            "rozmiar_slownika": tokenizer.rozmiar,
            "wymiar":           model.wymiar,
            "maks_dlugosc":     model.maks_dlugosc,
        }
    }
    torch.save(dane, PLIK_CACHE)

def wczytaj_cache(model, hash_pliku):
    """
    Wczytuje model z cache jeśli dane.json się nie zmieniło.
    Zwraca (tokenizer, True) lub (None, False).
    """
    import torch
    from transformer import URZADZENIE

    if not os.path.exists(PLIK_CACHE):
        return None, False

    try:
        dane = torch.load(PLIK_CACHE, map_location=URZADZENIE,weights_only=False)
        model.load_state_dict(dane["state_dict"])  # ← przywraca wagi
    except Exception:
        return None, False

    if dane["hash"] != hash_pliku:
        print("  ⚠️  Dane zmieniły się – trenuję od nowa.\n")
        return None, False

    # Wczytaj wagi do modelu
    model.load_state_dict(dane["state_dict"])

    return dane["tokenizer"], True

# ============================================================
# KROK 1: WCZYTAJ DANE
# ============================================================

def wczytaj_dane(sciezka):
    if not os.path.exists(sciezka):
        print(f"❌ Nie znaleziono '{sciezka}'!")
        exit(1)
    with open(sciezka, encoding="utf-8") as f:
        dane = json.load(f)
    return dane.get("zdania", [])

# ============================================================
# KROK 2: FUNKCJA STRATY
# ============================================================

def cross_entropy_loss(logits, cel_ids):
    """Zostawiamy dla kompatybilności – używana tylko w starej wersji"""
    import numpy as np
    from transformer import softmax
    T     = len(cel_ids)
    probs = softmax(logits)
    probs = np.clip(probs, 1e-9, 1.0)
    strata = -np.log(probs[np.arange(T), cel_ids]).mean()
    grad   = probs.copy()
    grad[np.arange(T), cel_ids] -= 1
    grad  /= T
    return strata, grad

# ============================================================
# KROK 3: TRENING (PyTorch)
# ============================================================

def trenuj(model, optymalizator, zdania_ids):
    """
    Trening z batch processing – wysyłamy wiele zdań naraz na GPU.

    Kroki:
      1. Posortuj zdania po długości (zmniejsza ilość paddingu)
      2. Podziel na batche po BATCH_SIZE zdań
      3. Wyrównaj zdania w batchu paddingiem do tej samej długości
      4. Wyślij cały batch na GPU jednocześnie
      5. Oblicz stratę ignorując tokeny PAD
    """
    import torch
    import random
    from transformer import URZADZENIE

    kryterium = torch.nn.CrossEntropyLoss(ignore_index=0)  # 0 = PAD, ignoruj go

    # Filtruj za krótkie zdania
    zdania = [ids for ids in zdania_ids if len(ids) >= 2]

    # Losowa kolejność każdą epokę – model nie zapamiętuje kolejności
    random.shuffle(zdania)

    calkowita_strata = 0.0
    n_batchy = 0

    # Podziel na batche
    for i in range(0, len(zdania), BATCH_SIZE):
        batch = zdania[i : i + BATCH_SIZE]

        # Znajdź najdłuższe zdanie w batchu
        maks_len = max(len(ids) for ids in batch)

        # Wyrównaj wszystkie zdania paddingiem (0 = PAD)
        wejscia = []
        cele    = []
        for ids in batch:
            brakuje = maks_len - len(ids)
            # wejście: wszystko oprócz ostatniego tokenu
            w = ids[:-1] + [0] * (brakuje + 1)
            # cel: wszystko oprócz pierwszego tokenu
            c = ids[1:]  + [0] * (brakuje + 1)
            wejscia.append(w[:maks_len])
            cele.append(c[:maks_len])

        # Zamień na tensory i wyślij na GPU
        # kształt: (BATCH_SIZE, długość_sekwencji)
        W = torch.tensor(wejscia, dtype=torch.long, device=URZADZENIE)
        C = torch.tensor(cele,    dtype=torch.long, device=URZADZENIE)

        optymalizator.zeruj_gradienty()

        # Forward pass dla całego batcha naraz
        # Przetwarzamy każde zdanie w batchu przez model
        logits_batch = []
        for j in range(W.shape[0]):
            logits = model.forward(W[j])        # (T, V)
            logits_batch.append(logits)

        # Złącz wyniki: (BATCH_SIZE * T, V)
        logits_all = torch.cat(logits_batch, dim=0)
        cele_all   = C.reshape(-1)               # (BATCH_SIZE * T,)

        # Strata – PAD tokeny są automatycznie ignorowane
        strata = kryterium(logits_all, cele_all)
        calkowita_strata += strata.item()
        n_batchy += 1

        # Backward + gradient clipping + krok optymalizatora
        strata.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optymalizator.krok()

    return calkowita_strata / max(n_batchy, 1)

# ============================================================
# KROK 4: GENEROWANIE TEKSTU
# ============================================================

def generuj(model, tokenizer, slowo_start, max_slow=10, temperatura=1.0):
    """
    Generuje tekst token po tokenie (autoregresywnie).
    torch.no_grad() wyłącza liczenie gradientów – szybsze generowanie.
    """
    import torch
    from transformer import URZADZENIE

    ids = tokenizer.koduj(slowo_start)
    if not ids or ids[0] == tokenizer.UNK:
        return f"[Nie znam słowa '{slowo_start}']"

    with torch.no_grad():
        for _ in range(max_slow):
            wejscie = ids[-MAKS_DLUGOSC:]
            logits  = model.forward(wejscie)

            # Pobierz logity ostatniego tokenu jako numpy
            ostatnie = logits[-1].cpu().numpy()
            ostatnie = ostatnie / max(temperatura, 0.01)
            probs    = softmax(ostatnie)
            nastepny = int(np.argmax(probs) if temperatura < 0.05
                          else np.random.choice(len(probs), p=probs))
            ids.append(nastepny)
            if nastepny == tokenizer.PAD:
                break

    return tokenizer.dekoduj(ids)

# ============================================================
# GŁÓWNY PROGRAM
# ============================================================

if __name__ == "__main__":

    print("=" * 55)
    print("  MINI-GPT – Transformer od zera!")
    print("=" * 55 + "\n")

    # 1. Dane + hash
    print("📚 Wczytuję dane...")
    zdania = wczytaj_dane(PLIK_DANYCH)
    aktualny_hash = hash_danych(PLIK_DANYCH)
    print(f"  Załadowano {len(zdania)} zdań.\n")

    # 2. Model (zawsze tworzymy strukturę)
    print("🧠 Tworzę model...")

    # Najpierw budujemy tokenizer żeby znać rozmiar słownika
    tokenizer_temp = Tokenizer()
    tokenizer_temp.buduj_slownik(zdania)

    from transformer import URZADZENIE
    model = MiniGPT(
        rozmiar_slownika = tokenizer_temp.rozmiar,
        wymiar           = WYMIAR,
        n_warstw         = N_WARSTW,
        n_glowic         = N_GLOWIC,
        dropout          = DROPOUT,
        maks_dlugosc     = MAKS_DLUGOSC,
    ).to(URZADZENIE)   # ← przenosi wszystkie wagi modelu na GPU
    print()

    # 3. Sprawdź cache
    tokenizer_z_cache, cache_ok = wczytaj_cache(model, aktualny_hash)

    if cache_ok:
        # ── Cache aktualny – pomijamy trening ──────────────────
        tokenizer = tokenizer_z_cache
        model.ustaw_trening(False)  # wyłącz Dropout
        print("✅ Wczytano wytrenowany model z cache!")
        print("   (dane.json nie zmieniło się – trening pominięty)\n")

    else:
        # ── Brak cache lub dane zmienione – trenujemy ──────────
        tokenizer  = tokenizer_temp
        zdania_ids = [tokenizer.koduj(z) for z in zdania]
        optymalizator = Adam(lr=LR, parametry=model.parameters())

        try:
            from tqdm import tqdm
            ma_tqdm = True
        except ImportError:
            ma_tqdm = False
            print("  💡 Wskazówka: zainstaluj tqdm dla ładniejszego paska:")
            print("     pip install tqdm\n")

        print(f"⚙️  Trenuję przez {EPOKI} epok...\n")

        model.ustaw_trening(True)   # włącz Dropout podczas treningu
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
            # Fallback – wypisuje co 100 epok bez animacji
            for epoka in range(1, EPOKI + 1):
                strata = trenuj(model, optymalizator, zdania_ids)
                if epoka % 100 == 0 or epoka == EPOKI:
                    proc = epoka / EPOKI * 100
                    print(f"  Epoka {epoka}/{EPOKI} ({proc:.0f}%)  strata: {strata:.4f}")

        print(f"\n  ✅ Trening zakończony!")
        model.ustaw_trening(False)  # wyłącz Dropout przy generowaniu

        # Zapisz model do cache
        zapisz_cache(model, tokenizer, aktualny_hash)
        print(f"  💾 Model zapisany do '{PLIK_CACHE}'\n")

    # 4. Test
    print("🧪 Test generowania:")
    for slowo in ["warszawa", "polska", "kot", "wisła"]:
        wynik = generuj(model, tokenizer, slowo, temperatura=0.5)
        print(f"  '{slowo}' → {wynik}")

    # 6. Tryb rozmowy z pamięcią
    print("\n" + "═" * 55)
    print("  💬 TRYB ROZMOWY – model pamięta kontekst!")
    print("═" * 55)
    print("  Przykłady pytań:")
    print("    co to jest kot")
    print("    gdzie jest warszawa")
    print("    kim jesteś")
    print()
    print("  Komendy: /temp 0.1 | /historia | /zapomnij | /pomoc | koniec")
    print("═" * 55 + "\n")

    temperatura   = 0.1   # niska = pewne odpowiedzi
    OKNO_PAMIECI  = 3     # ile ostatnich wymian model pamięta

    # Historia rozmowy – lista par (pytanie, odpowiedź)
    historia = []

    id_koniec = tokenizer.slowo_na_id.get("koniec", -1)

    def buduj_kontekst(historia, nowe_pytanie):
        """
        Buduje wejście dla modelu z historią rozmowy.

        Przykład z historią 2 wymian:
          użytkownik masz kota asystent tak mam kota
          użytkownik ile kotów asystent [tu model generuje]

        Im więcej historii → model lepiej rozumie kontekst.
        Ale za dużo → przekracza MAKS_DLUGOSC, więc bierzemy
        tylko ostatnie OKNO_PAMIECI wymian.
        """
        czesci = []

        # Dodaj ostatnie N wymian jako kontekst
        for (stare_pyt, stara_odp) in historia[-OKNO_PAMIECI:]:
            czesci.append(f"użytkownik {stare_pyt} asystent {stara_odp}")

        # Dodaj nowe pytanie
        czesci.append(f"użytkownik {nowe_pytanie} asystent")

        return " ".join(czesci)

    # Mapa polskich znaków – naprawia literówki bez ogonków
    BEZ_OGONKOW = {
        "a": "ą", "c": "ć", "e": "ę", "l": "ł", "n": "ń",
        "o": "ó", "s": "ś", "z": "ź", "x": "ż",
    }

    def napraw_ogonki(slowo):
        """
        Próbuje dopasować słowo bez ogonków do słownika modelu.
        Przykład: "jestes" → "jesteś", "czesc" → "cześć"
        """
        if tokenizer.koduj(slowo)[0] != tokenizer.UNK:
            return slowo  # słowo znane – nie zmieniaj

        # Spróbuj podmienić ostatnią literę na wersję z ogonkiem
        for i, litera in enumerate(slowo):
            if litera in BEZ_OGONKOW:
                kandydat = slowo[:i] + BEZ_OGONKOW[litera] + slowo[i+1:]
                if tokenizer.koduj(kandydat)[0] != tokenizer.UNK:
                    return kandydat
        return slowo  # nie znaleziono – zwróć oryginał


    def generuj_odpowiedz(pytanie, historia, temperatura):
        import torch
        from transformer import URZADZENIE

        pytanie = pytanie.lower().strip().rstrip("?")
        pytanie = " ".join(napraw_ogonki(s) for s in pytanie.split())

        # Napraw ogonki w każdym słowie
        pytanie = " ".join(napraw_ogonki(s) for s in pytanie.split())

        if len(pytanie.split()) == 1:
            if tokenizer.koduj(pytanie)[0] == tokenizer.UNK:
                return f"Nie znam słowa '{pytanie}'. Dodaj je do dane.json!"
            pytanie = f"co to jest {pytanie}"

        stop_slowa = {"co","to","jest","gdzie","jaka","czym","kim",
                      "jak","się","masz","czy","ile","kto","kiedy"}
        nieznane = [s for s in pytanie.split()
                    if s not in stop_slowa
                    and tokenizer.koduj(s)[0] == tokenizer.UNK]
        if nieznane:
            return f"Nie znam słów: {', '.join(nieznane)}. Dodaj je do dane.json!"

        kontekst = buduj_kontekst(historia, pytanie)
        ids      = tokenizer.koduj(kontekst)

        ostatnie_n = []  # do wykrywania zapętlenia

        with torch.no_grad():
            ostatnie_n = []
            for _ in range(15):
                logits   = model.forward(ids[-MAKS_DLUGOSC:])
                ostatnie = logits[-1].cpu().numpy() / max(temperatura, 0.01)
                probs    = softmax(ostatnie)
                nastepny = int(np.argmax(probs) if temperatura < 0.05
                               else np.random.choice(len(probs), p=probs))

                if nastepny == id_koniec or nastepny == tokenizer.PAD:
                    break

                    # Wykryj zapętlenie – jeśli ten sam token 3 razy z rzędu → stop
                ostatnie_n.append(nastepny)
                if len(ostatnie_n) >= 4 and len(set(ostatnie_n[-4:])) <= 2:
                    break

                ostatnie_n.append(nastepny)
                if len(ostatnie_n) >= 4 and len(set(ostatnie_n[-4:])) <= 2:
                    break
                ids.append(nastepny)

        wszystkie = tokenizer.dekoduj(ids).split()
        if "asystent" in wszystkie:
            idx       = len(wszystkie) - 1 - wszystkie[::-1].index("asystent")
            odpowiedz = " ".join(wszystkie[idx + 1:])
        else:
            odpowiedz = " ".join(wszystkie)

        odpowiedz = odpowiedz.replace("koniec", "").replace("użytkownik", "").strip()
        return odpowiedz if odpowiedz else "..."

    while True:
        try:
            wejscie = input("  Ty: ").strip()

            if not wejscie:
                continue

            # ── komendy ───────────────────────────────────────

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

  Jak działa pamięć:
    Model pamięta ostatnie 3 wymiany.
    Użyj /zapomnij żeby zacząć nowy temat.
                """)
                continue

            # ── generuj odpowiedź ──────────────────────────────

            odpowiedz = generuj_odpowiedz(wejscie, historia, temperatura)
            print(f"  🤖 Model: {odpowiedz}\n")

            # Zapisz do historii (tylko jeśli odpowiedź sensowna)
            if odpowiedz != "...":
                pytanie_clean = wejscie.lower().strip().rstrip("?")
                if len(pytanie_clean.split()) == 1:
                    pytanie_clean = f"co to jest {pytanie_clean}"
                historia.append((pytanie_clean, odpowiedz))

        except KeyboardInterrupt:
            print("\n\n  Program zakończony.\n")
            break