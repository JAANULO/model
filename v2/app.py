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
    logger.info("Wyszukiwarka zaladowana")

# ── trasy ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/zapytaj", methods=["POST"])
def zapytaj():
    dane    = request.get_json(force=True)
    pytanie = dane.get("pytanie", "").strip()
    logger.info(f"PYTANIE: {pytanie}")

    if not pytanie:
        logger.warning("Puste pytanie od klienta")
        return jsonify({"blad": "Puste pytanie"}), 400

    if wyszukiwarka is None:
        return jsonify({"blad": "Wyszukiwarka nie załadowana"}), 500

    rozszerzenie = _znajdz_rozszerzenie(pytanie.lower())
    pytanie_do_szukania = (pytanie + " " + rozszerzenie).strip() if rozszerzenie else pytanie

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

    if not wynik or wynik["podobienstwo"] < PROG_PEWNOSCI:
        logger.info(f"BRAK_TRAFIENIA: pytanie='{pytanie}'")
        return jsonify({
            "odpowiedz": "Nie znalazłem informacji na ten temat w regulaminie. Spróbuj zapytać inaczej.",
            "tytul": None,
            "podobienstwo": 0,
            "tytul2": None,
        })

    odp = formatuj_odpowiedz(pytanie, wynik)


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
        })
    # fallback dla błędów (odp to string)
    return jsonify({"odpowiedz": odp, "tytul": None, "podobienstwo": 0})


@app.route("/feedback", methods=["POST"])
def feedback():
    dane = request.get_json(force=True)
    zapisz_feedback(dane["pytanie_id"], dane["ocena"])
    logger.info(f"FEEDBACK: pytanie_id={dane['pytanie_id']}, ocena={dane['ocena']}")
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
