"""
db.py – baza SQLite dla logów, statystyk i feedbacku.
Zastępuje log.txt. Wbudowana biblioteka sqlite3 – zero instalacji.
"""
import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLIK_DB = os.path.join(BASE_DIR, "..", "asystent.db")


def polacz():
    conn = sqlite3.connect(PLIK_DB)
    conn.row_factory = sqlite3.Row   # wyniki jako słowniki
    return conn


def inicjalizuj():
    """tworzy tabele jeśli nie istnieją"""
    with polacz() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS pytania (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                pytanie     TEXT NOT NULL,
                tytul       TEXT,
                podobienstwo REAL,
                baza        TEXT DEFAULT 'studia',
                czas        TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                pytanie_id  INTEGER REFERENCES pytania(id),
                ocena       INTEGER NOT NULL,   -- 1 = dobre, -1 = złe
                komentarz   TEXT,
                czas        TEXT DEFAULT (datetime('now','localtime'))
            );
        """)


def zapisz_pytanie(pytanie, tytul, podobienstwo, baza="studia"):
    with polacz() as conn:
        cur = conn.execute(
            "INSERT INTO pytania (pytanie, tytul, podobienstwo, baza) VALUES (?,?,?,?)",
            (pytanie, tytul, podobienstwo, baza)
        )
        return cur.lastrowid   # zwraca ID do feedbacku


def zapisz_feedback(pytanie_id, ocena, komentarz=None):
    with polacz() as conn:
        conn.execute(
            "INSERT INTO feedback (pytanie_id, ocena, komentarz) VALUES (?,?,?)",
            (pytanie_id, ocena, komentarz)
        )

    def pobierz_wspolczynnik_feedbacku(tytul):
        """Oblicza mnożnik dla paragrafu na podstawie łapek w górę/dół (RLHF)"""
        with polacz() as conn:
            wynik = conn.execute("""
                                 SELECT SUM(f.ocena)
                                 FROM feedback f
                                          JOIN pytania p ON f.pytanie_id = p.id
                                 WHERE p.tytul = ?
                                 """, (tytul,)).fetchone()[0]

        if wynik is None or wynik == 0:
            return 1.0  # Waga neutralna
        elif wynik > 0:
            return 1.2  # 20% bonusu za przewagę pozytywnych ocen
        else:
            return 0.8  # 20% kary za przewagę negatywnych ocen

def pobierz_statystyki():
    with polacz() as conn:
        total = conn.execute("SELECT COUNT(*) FROM pytania").fetchone()[0]
        avg   = conn.execute("SELECT AVG(podobienstwo) FROM pytania").fetchone()[0]
        top   = conn.execute("""
            SELECT tytul, COUNT(*) as n
            FROM pytania WHERE tytul IS NOT NULL
            GROUP BY tytul ORDER BY n DESC LIMIT 5
        """).fetchall()
        zle   = conn.execute("""
            SELECT p.pytanie, p.tytul, p.podobienstwo
            FROM feedback f JOIN pytania p ON f.pytanie_id = p.id
            WHERE f.ocena = -1
            ORDER BY f.czas DESC LIMIT 10
        """).fetchall()
    return {
        "pytania":             total,
        "srednie_podobienstwo": round((avg or 0) * 100, 1),
        "top_paragrafy":       [{"tytul": r["tytul"], "liczba": r["n"]} for r in top],
        "zle_odpowiedzi":      [dict(r) for r in zle],
    }