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
import re
import time
from collections import OrderedDict
from datetime import datetime
from core.bd import inicjalizuj, zapisz_pytanie, zapisz_feedback, pobierz_statystyki,pobierz_pytanie

app = Flask(__name__)

def _znajdz_rozszerzenie(pytanie_lower: str) -> str:
    """Zwraca rozszerzenie dla pierwszej pasującej frazy lub pusty string."""
    for fraza, rozszerzenie in ROZSZERZENIA.items():
        if fraza in pytanie_lower:
            return rozszerzenie
    return ""


def _wykryj_numer_paragrafu(pytanie: str) -> str | None:
    """Wykrywa numer paragrafu z zapytania (np. §18, paragraf 18)."""
    pytanie_ascii = pytanie.lower().translate(str.maketrans('ąćęłńóśźż', 'acelnoszzz'[:9]))
    dopasowanie = re.search(r"(?:§\s*|paragraf(?:ie|u|em|owi|ach)?\s+)(\d+)", pytanie_ascii)
    return dopasowanie.group(1) if dopasowanie else None


def _cache_get(pytanie: str):
    wpis = CACHE_ODPOWIEDZI.get(pytanie)
    if not wpis:
        return None
    if time.time() - wpis["ts"] > CACHE_TTL_SECONDS:
        CACHE_ODPOWIEDZI.pop(pytanie, None)
        return None
    return wpis["data"]


def _cache_set(pytanie: str, odpowiedz: dict):
    if pytanie in CACHE_ODPOWIEDZI:
        CACHE_ODPOWIEDZI[pytanie] = {"ts": time.time(), "data": odpowiedz}
        return
    while len(CACHE_ODPOWIEDZI) >= CACHE_MAX_SIZE:
        CACHE_ODPOWIEDZI.popitem(last=False)
    CACHE_ODPOWIEDZI[pytanie] = {"ts": time.time(), "data": odpowiedz}

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DATA_DIR      = os.path.join(BASE_DIR, "data")
PLIK_BAZY     = os.path.join(DATA_DIR, "baza_wiedzy.json")
PLIK_LOG      = os.path.join(BASE_DIR, "logs", "log.txt")
PROG_PEWNOSCI = 0.15

CACHE_TTL_SECONDS = 60 * 60
CACHE_MAX_SIZE = 500
CACHE_ODPOWIEDZI = OrderedDict()

logger = logging.getLogger("asystent")
logger.setLevel(logging.INFO)
logger.propagate = False  # nie przepuszczaj do root loggera
logging.getLogger("werkzeug").setLevel(logging.WARNING)

# ── ładowanie wyszukiwarki raz przy starcie ───────────────────────────────────
wyszukiwarka = None
indeks_zdan  = None

def zaladuj_wyszukiwarke():
    global wyszukiwarka
    if not os.path.isdir(DATA_DIR):
        raise FileNotFoundError(f"Brak katalogu '{DATA_DIR}'.")

    os.makedirs(os.path.dirname(PLIK_LOG), exist_ok=True)

    if not logger.handlers:
        fh = logging.FileHandler(PLIK_LOG, encoding="utf-8")
        fh.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(fh)

    wyszukiwarka = Wyszukiwarka(DATA_DIR)
    global indeks_zdan
    from core.indeks_zdan import IndeksZdan
    indeks_zdan = IndeksZdan(DATA_DIR)
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

    cache_dozwolony = kontekst_tytul is None
    if cache_dozwolony:
        cached = _cache_get(pytanie)
        if cached is not None:
            return jsonify(cached)

    numer_paragrafu = _wykryj_numer_paragrafu(pytanie)
    if numer_paragrafu:
        wynik_bezposredni = wyszukiwarka.pobierz_paragraf_po_numerze(numer_paragrafu)
        if wynik_bezposredni:
            odp = formatuj_odpowiedz(pytanie, wynik_bezposredni)
            tekst_odpowiedzi = odp["wstep"] if isinstance(odp, dict) else odp

            inicjalizuj()
            pid = zapisz_pytanie(
                pytanie,
                wynik_bezposredni["tytul"],
                wynik_bezposredni["podobienstwo"],
                odpowiedz=tekst_odpowiedzi,
            )

            logger.info(
                f"DIRECT_PARAGRAF: pid={pid}, paragraf={numer_paragrafu}, tytul='{wynik_bezposredni['tytul']}'"
            )

            if isinstance(odp, dict):
                payload = {
                    "wstep":         odp["wstep"],
                    "punkty":        odp["punkty"],
                    "tytul":         odp["tytul"],
                    "zacheta":       odp["zacheta"],
                    "podobienstwo":  odp["podobienstwo"],
                    "pelna_tresc":   odp["pelna_tresc"],
                    "tytul2":        None,
                    "podobienstwo2": None,
                    "pytanie_id": pid,
                    "kontekst_tytul": odp["tytul"],
                    "zrodlo": wynik_bezposredni.get("zrodlo"),
                }
                if cache_dozwolony:
                    _cache_set(pytanie, payload)
                return jsonify(payload)

            payload = {
                "odpowiedz": odp,
                "tytul": wynik_bezposredni["tytul"],
                "podobienstwo": 1.0,
                "pytanie_id": pid,
                "zrodlo": wynik_bezposredni.get("zrodlo"),
            }
            if cache_dozwolony:
                _cache_set(pytanie, payload)
            return jsonify(payload)

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
        pod = wynik["podobienstwo"] if wynik else 0.0

        top3 = wyszukiwarka.szukaj(pytanie_do_szukania, n_wynikow=3)
        propozycje = [w["tytul"] for w in top3 if w["podobienstwo"] > 0.05]
        tekst = "Nie znalazłem dokładnej odpowiedzi w regulaminie."
        if propozycje:
            tekst += f" Może chodzi o: {', '.join(propozycje[:2])}?"

        inicjalizuj()
        pid = zapisz_pytanie(pytanie, None, pod, odpowiedz=tekst)

        logger.info(f"BRAK_TRAFIENIA: pytanie='{pytanie}', najlepsze={pod:.3f}, pid={pid}")
        payload = {
            "odpowiedz": tekst,
            "tytul": None,
            "podobienstwo": pod,
            "tytul2": None,
            "pytanie_id": pid,
            "zrodlo": None,
        }
        if cache_dozwolony:
            _cache_set(pytanie, payload)
        return jsonify(payload)

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

    tekst_odpowiedzi = odp["wstep"] if isinstance(odp, dict) else odp

    inicjalizuj()
    pid = zapisz_pytanie(pytanie, wynik["tytul"], wynik["podobienstwo"], odpowiedz=tekst_odpowiedzi)

    logger.info(
        f"ODPOWIEDZ: pid={pid}, tytul='{wynik['tytul']}', podobienstwo={wynik['podobienstwo']:.4f}"
    )

    if isinstance(odp, dict):
        payload = {
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
            "zrodlo": wynik.get("zrodlo"),
            "zrodlo2": wynik2.get("zrodlo") if wynik2 else None,
        }
        if cache_dozwolony:
            _cache_set(pytanie, payload)
        return jsonify(payload)
    # fallback dla błędów (odp to string)
    payload = {"odpowiedz": odp, "tytul": None, "podobienstwo": 0, "pytanie_id": pid, "zrodlo": None}
    if cache_dozwolony:
        _cache_set(pytanie, payload)
    return jsonify(payload)


@app.route("/feedback", methods=["POST"])
def feedback():
    dane = request.get_json(force=True)
    pid = dane["pytanie_id"]
    ocena = dane["ocena"]
    zapisz_feedback(pid, ocena)
    logger.info(f"FEEDBACK: pytanie_id={pid}, ocena={ocena}")

    # Dodatkowy log do pliku dla negatywnych ocen z niską pewnością
    # Dodatkowy log do pliku dla negatywnych ocen z niską pewnością
    if ocena == -1:
        rekord = pobierz_pytanie(pid)
        if rekord and rekord["podobienstwo"] is not None and rekord["podobienstwo"] < 0.2:
            log_dir = os.path.join(BASE_DIR, "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "do_poprawy.txt")

            with open(log_path, "a", encoding="utf-8") as f:
                czas = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(
                    f"[{czas}] Pytanie: '{rekord['pytanie']}' | Odpowiedź: '{rekord['odpowiedz'] or ''}' | Podobieństwo: {rekord['podobienstwo']:.3f} | Tytuł: {rekord['tytul']}\n")

    return jsonify({"ok": True})


ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev-token-zmien-mnie")


@app.route("/historia", methods=["GET"])
def historia():
    try:
        import sqlite3
        import glob

        # Wyszukaj wszystkie bazy i wybierz tę, która faktycznie ma tabelę pytań
        db_files = glob.glob(os.path.join(BASE_DIR, "*.db")) + glob.glob(os.path.join(BASE_DIR, "data", "*.db"))
        if not db_files:
            return jsonify({"error": "Nie znaleziono pliku bazy .db"}), 404

        db_path = None
        table_name = None

        for candidate in db_files:
            test_conn = sqlite3.connect(candidate)
            test_conn.row_factory = sqlite3.Row
            test_cur = test_conn.cursor()
            test_cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND (name='pytania' OR name='historia')"
            )
            row = test_cur.fetchone()
            test_conn.close()

            if row:
                db_path = candidate
                table_name = row["name"]
                break

        if not db_path or not table_name:
            return jsonify({"error": "Nie znaleziono tabeli 'pytania' ani 'historia' w żadnej bazie .db"}), 404

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()


        # Pobierz 10 ostatnich niepustych i unikalnych pytań
        cur.execute(
            f"SELECT DISTINCT pytanie FROM {table_name} WHERE pytanie IS NOT NULL AND pytanie != '' ORDER BY id DESC LIMIT 10")
        wyniki = [dict(row) for row in cur.fetchall()]
        conn.close()
        return jsonify(wyniki)
    except Exception as e:
        logger.error(f"Błąd pobierania historii: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/admin")
def admin():
    token = request.args.get("token", "")
    if token != ADMIN_TOKEN:
        return "Brak dostępu! Podaj prawidłowy token w adresie, np: /admin?token=dev-token-zmien-mnie", 403
    return render_template("admin.html", stats=pobierz_statystyki())


# ── start ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Ładowanie bazy wiedzy...")
    zaladuj_wyszukiwarke()
    print("Serwer startuje → http://localhost:5000\n")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, use_reloader=False, host="0.0.0.0", port=port)
