"""
app.py – serwer Flask dla asystenta regulaminowego PWr
Uruchomienie: python app.py
Adres:        http://localhost:5000
"""

from flask import Flask, request, jsonify, render_template
from core.wyszukiwarka import Wyszukiwarka
from core.formatowanie import formatuj_odpowiedz
from core.slowniki import ROZSZERZENIA, SYNONIMY
import logging
import os
from core.bd import inicjalizuj, zapisz_pytanie, zapisz_feedback, pobierz_statystyki

app = Flask(__name__)

def _znajdz_rozszerzenie(pytanie_lower: str) -> str:
    """Zwraca rozszerzenie dla pierwszej pasującej frazy lub pusty string."""
    for fraza, rozszerzenie in ROZSZERZENIA.items():
        if fraza in pytanie_lower:
            return rozszerzenie
    return ""

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PLIK_BAZY     = os.path.join(BASE_DIR, "data", "baza_wiedzy.json")
PLIK_LOG      = os.path.join(BASE_DIR, "logs", "log.txt")
PROG_PEWNOSCI = 0.15

logger = logging.getLogger("asystent")
logger.setLevel(logging.INFO)
logger.propagate = False  # nie przepuszczaj do root loggera
logging.getLogger("werkzeug").setLevel(logging.WARNING)

# ── ładowanie wyszukiwarki raz przy starcie ───────────────────────────────────
wyszukiwarka = None
indeks_zdan  = None

def zaladuj_wyszukiwarke():
    global wyszukiwarka
    if not os.path.exists(PLIK_BAZY):
        raise FileNotFoundError(f"Brak pliku '{PLIK_BAZY}'. Uruchom najpierw: python parser.py")

    os.makedirs(os.path.dirname(PLIK_LOG), exist_ok=True)

    if not logger.handlers:
        fh = logging.FileHandler(PLIK_LOG, encoding="utf-8")
        fh.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(fh)

    wyszukiwarka = Wyszukiwarka(PLIK_BAZY)
    global indeks_zdan
    from core.indeks_zdan import IndeksZdan
    indeks_zdan = IndeksZdan(PLIK_BAZY)
    logger.info("Wyszukiwarka zaladowana")

# ── trasy ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/zapytaj", methods=["POST"])
def zapytaj():
    dane = request.get_json(force=True)
    pytanie = dane.get("pytanie", "").strip()
    kontekst_tytul = dane.get("kontekst_tytul", None)  # poprzedni paragraf
    kontekst_pytanie = dane.get("kontekst_pytanie", None)  # poprzednie pytanie
    #print(f"DEBUG kontekst: tytul={kontekst_tytul}, pytanie={kontekst_pytanie}")
    logger.info(f"PYTANIE: {pytanie} | kontekst: {kontekst_tytul}")

    if not pytanie:
        logger.warning("Puste pytanie od klienta")
        return jsonify({"blad": "Puste pytanie"}), 400

    if wyszukiwarka is None:
        return jsonify({"blad": "Wyszukiwarka nie załadowana"}), 500

    rozszerzenie = _znajdz_rozszerzenie(pytanie.lower())
    pytanie_do_szukania = (pytanie + " " + rozszerzenie).strip() if rozszerzenie else pytanie

    # wykryj pytania kontekstowe – krótkie pytania nawiązujące do poprzedniego
    SYGNALY_KONTEKSTU = [
        "a co jak", "a jesli", "a jezeli", "co jak", "co jesli",
        "a co jesli", "i co wtedy", "co wtedy", "a wtedy",
        "a jak nie", "jak nie zdam", "jak obleje", "co jak nie",
        "a czy moge", "czy wtedy", "co z tym", "i co z",
    ]
    pyt_ascii = pytanie.lower().translate(str.maketrans('ąćęłńóśźż', 'acelnoszzz'[:9]))
    jest_kontekstowe = (
            kontekst_tytul is not None and
            len(pytanie.split()) <= 7 and
            any(s in pyt_ascii for s in SYGNALY_KONTEKSTU)
    )
    print(
        f"DEBUG jest_kontekstowe={jest_kontekstowe}, tytul={kontekst_tytul}, len={len(pytanie.split())}, ascii={pyt_ascii}")

    # dla pytań kontekstowych – dodaj poprzedni paragraf do zapytania
    if jest_kontekstowe and kontekst_pytanie:
        pytanie_do_szukania = kontekst_pytanie + " " + pytanie
        logger.info(f"KONTEKST: rozszerzam pytanie o '{kontekst_pytanie}'")
        #print(f"DEBUG pytanie_do_szukania: {pytanie_do_szukania}")

    # rozszerzenie krótkich pytań
    if len(pytanie.split()) <= 2:
        slowo_bazowe = pytanie.strip().lower().rstrip("?!")
        pasujace = [v for k, v in SYNONIMY.items() if slowo_bazowe in k]
        if pasujace:
            pytanie_do_szukania = pytanie + " " + " ".join(set(pasujace))

    wyniki = wyszukiwarka.szukaj(pytanie_do_szukania, n_wynikow=2)
    wynik  = wyniki[0] if wyniki else None

    # drugi paragraf przy bliskim podobieństwie lub długim pytaniu
    wynik2 = None
    if len(wyniki) == 2:
        roznica = wyniki[0]["podobienstwo"] - wyniki[1]["podobienstwo"]
        # drugi paragraf tylko gdy: blisko pierwszego ORAZ długie pytanie (więcej kontekstu)
        if roznica < 0.03 and len(pytanie.split()) >= 6:
            wynik2 = wyniki[1]

    prog = 0.10 if jest_kontekstowe else PROG_PEWNOSCI
    #print(f"DEBUG prog={prog}, podobienstwo={wynik['podobienstwo'] if wynik else None}")
    if not wynik or wynik["podobienstwo"] < prog:

        logger.info(f"BRAK_TRAFIENIA: pytanie='{pytanie}', najlepsze={wynik['podobienstwo'] if wynik else 0:.3f}")
        top3 = wyszukiwarka.szukaj(pytanie_do_szukania, n_wynikow=3)
        propozycje = [w["tytul"] for w in top3 if w["podobienstwo"] > 0.05]
        tekst = "Nie znalazłem dokładnej odpowiedzi w regulaminie."
        if propozycje:
            tekst += f" Może chodzi o: {', '.join(propozycje[:2])}?"
        return jsonify({
            "odpowiedz": tekst,
            "tytul": None,
            "podobienstwo": 0,
            "tytul2": None,
        })

    from core.intencje import wykryj_intencje, generuj_skrot, wyciagnij_liczbe, wyciagnij_termin

    intencja = wykryj_intencje(pytanie)
    zdania_wyniki = indeks_zdan.szukaj(pytanie, n_wynikow=5) if indeks_zdan else []

    # klasyfikator intencji – musi być PRZED pętlą
    intencja = wykryj_intencje(pytanie)

    najlepsze_zdanie = None
    for zw in zdania_wyniki:
        if zw['tytul'] != wynik['tytul'] or zw['podobienstwo'] < 0.1:
            continue
        if intencja == "LICZBA":
            # dla "ile dni" szukaj zdania z "odstep" zamiast liczby
            p_lower = pytanie.lower()

            if "ile dni" in p_lower or "miedzy terminami" in p_lower:

                if any(s in zw['zdanie'].lower() for s in ["odstęp", "odstep", "pięciodniowym", "pieciodniowym"]):
                    najlepsze_zdanie = zw['zdanie']
                    break

            else:
                l = wyciagnij_liczbe(zw['zdanie'])
                print(f"DEBUG zdanie: {zw['zdanie'][:80]} → L:{l}")
                if l:
                    najlepsze_zdanie = zw['zdanie']
                    break

        elif intencja == "TERMIN":

            if wyciagnij_termin(zw['zdanie']):
                najlepsze_zdanie = zw['zdanie']
                break
            # fallback dla "ile dni" – szukaj zdania z odstępem
            p_lower = pytanie.lower()
            if any(s in p_lower for s in ["ile dni", "miedzy terminami"]):
                if any(s in zw['zdanie'].lower() for s in ["odstęp", "odstep", "pięciodniowym", "pieciodniowym"]):
                    najlepsze_zdanie = zw['zdanie']
                    break
        else:
            najlepsze_zdanie = zw['zdanie']
            break

    skrot = None

    if najlepsze_zdanie:
        skrot = generuj_skrot(intencja, pytanie, najlepsze_zdanie)

    # dla SKUTEK i TAK_NIE jedno zdanie wystarczy
    if intencja in ("SKUTEK", "TAK_NIE") and najlepsze_zdanie:
        odp = formatuj_odpowiedz(pytanie, wynik, najlepsze_zdanie=najlepsze_zdanie, skrot=skrot, tylko_jedno=True)
    else:
        odp = formatuj_odpowiedz(pytanie, wynik, najlepsze_zdanie=najlepsze_zdanie, skrot=skrot)


    inicjalizuj()
    pid = zapisz_pytanie(pytanie, wynik["tytul"], wynik["podobienstwo"])

    logger.info(
        f"ODPOWIEDZ: pid={pid}, tytul='{wynik['tytul']}', podobienstwo={wynik['podobienstwo']:.4f}"
    )

    if isinstance(odp, dict):
        return jsonify({
            "wstep":         odp["wstep"],
            "punkty":        odp["punkty"],
            "tytul":         odp["tytul"],
            "zacheta":       odp["zacheta"],
            "podobienstwo":  odp["podobienstwo"],
            "pelna_tresc":   odp["pelna_tresc"],
            "tytul2":        wynik2["tytul"] if wynik2 else None,
            "podobienstwo2": wynik2["podobienstwo"] if wynik2 else None,
            "pytanie_id": pid,
            "kontekst_tytul": odp["tytul"],  # przekaż do frontendu
        })
    # fallback dla błędów (odp to string)
    return jsonify({"odpowiedz": odp, "tytul": None, "podobienstwo": 0})


@app.route("/feedback", methods=["POST"])
def feedback():
    dane = request.get_json(force=True)
    zapisz_feedback(dane["pytanie_id"], dane["ocena"])
    logger.info(f"FEEDBACK: pytanie_id={dane['pytanie_id']}, ocena={dane['ocena']}")
    #print(f"DEBUG kontekst: tytul={kontekst_tytul}, pytanie={kontekst_pytanie}")
    return jsonify({"ok": True})


ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev-token-zmien-mnie")

@app.route("/statystyki")
def statystyki():
    token = request.args.get("token", "")
    if token != ADMIN_TOKEN:
        return jsonify({"blad": "Brak dostępu"}), 403
    return jsonify(pobierz_statystyki())


# ── start ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Ładowanie bazy wiedzy...")
    zaladuj_wyszukiwarke()
    print("Serwer startuje → http://localhost:5000\n")
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5000)
