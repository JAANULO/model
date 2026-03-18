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

def pobierz_wspolczynniki_zbiorczo():
    """Pobiera wszystkie oceny jednym zapytaniem, rozwiązując problem N+1"""
    with polacz() as conn:
        wyniki = conn.execute("""
            SELECT p.tytul, SUM(f.ocena) as suma_ocen
            FROM feedback f
            JOIN pytania p ON f.pytanie_id = p.id
            WHERE p.tytul IS NOT NULL
            GROUP BY p.tytul
        """).fetchall()

    slownik = {}
    for w in wyniki:
        suma = w['suma_ocen']
        if suma > 0:
            slownik[w['tytul']] = 1.2
        elif suma < 0:
            slownik[w['tytul']] = 0.8
        else:
            slownik[w['tytul']] = 1.0
    return slownik