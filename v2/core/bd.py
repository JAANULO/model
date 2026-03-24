"""
db.py – baza SQLite dla logów, statystyk i feedbacku.
Zastępuje log.txt. Wbudowana biblioteka sqlite3 – zero instalacji.
"""
import os
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")
TRYB = "postgres" if DATABASE_URL else "sqlite"

if TRYB == "postgres":
    import psycopg2
    from psycopg2.extras import RealDictCursor
else:
    import sqlite3
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PLIK_DB = os.path.join(BASE_DIR, "..", "data", "asystent.db")

def polacz():
    if TRYB == "postgres":
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        conn = sqlite3.connect(PLIK_DB)
        conn.row_factory = sqlite3.Row
        return conn


def inicjalizuj():
    """Tworzy tabele i brakujące kolumny wymagane przez aplikację."""
    with polacz() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pytania (
                    id SERIAL PRIMARY KEY,
                    pytanie TEXT,
                    tytul TEXT,
                    podobienstwo REAL,
                    odpowiedz TEXT,
                    baza TEXT DEFAULT 'studia',
                    czas TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    pytanie_id INTEGER REFERENCES pytania(id) ON DELETE CASCADE,
                    ocena INTEGER NOT NULL,
                    komentarz TEXT,
                    czas TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("ALTER TABLE pytania ADD COLUMN IF NOT EXISTS odpowiedz TEXT")
            cur.execute("ALTER TABLE pytania ADD COLUMN IF NOT EXISTS baza TEXT DEFAULT 'studia'")
            conn.commit()


def zapisz_pytanie(pytanie, tytul, podobienstwo, baza="studia", odpowiedz=None):
    with polacz() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO pytania (pytanie, tytul, podobienstwo, baza, odpowiedz) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                (pytanie, tytul, podobienstwo, baza, odpowiedz)
            )
            conn.commit()
            return cur.fetchone()["id"]


def zapisz_feedback(pytanie_id, ocena, komentarz=None):
    with polacz() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO feedback (pytanie_id, ocena, komentarz) VALUES (%s,%s,%s)",
                (pytanie_id, ocena, komentarz)
            )
            conn.commit()

def pobierz_wspolczynniki_zbiorczo():
    with polacz() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.tytul, SUM(f.ocena) as suma_ocen
                FROM feedback f
                JOIN pytania p ON f.pytanie_id = p.id
                WHERE p.tytul IS NOT NULL
                GROUP BY p.tytul
            """)
            wyniki = cur.fetchall()

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

def pobierz_pytanie(pytanie_id):
    """Pobiera zapisane pytanie na podstawie jego ID"""
    with polacz() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pytanie, tytul, podobienstwo, odpowiedz FROM pytania WHERE id = %s",
                (pytanie_id,)
            )
            return cur.fetchone()


def pobierz_ostatnie_pytania(limit=10):
    """Zwraca ostatnie unikalne pytania (od najnowszych) do panelu historii."""
    with polacz() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT pytanie
                FROM pytania
                WHERE pytanie IS NOT NULL AND pytanie <> ''
                ORDER BY id DESC
                LIMIT %s
                """,
                (max(int(limit) * 3, int(limit)),)
            )
            rows = cur.fetchall()

    unikalne = []
    widziane = set()
    for row in rows:
        p = row["pytanie"]
        if p in widziane:
            continue
        widziane.add(p)
        unikalne.append({"pytanie": p})
        if len(unikalne) >= int(limit):
            break
    return unikalne

def pobierz_statystyki():
    with polacz() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as total FROM pytania")
            total = cur.fetchone()["total"]

            cur.execute("SELECT AVG(podobienstwo) as avg FROM pytania")
            avg = cur.fetchone()["avg"]

            cur.execute("""
                SELECT tytul, COUNT(*) as n
                FROM pytania WHERE tytul IS NOT NULL
                GROUP BY tytul ORDER BY n DESC LIMIT 5
            """)
            top = cur.fetchall()

            cur.execute("""
                SELECT p.pytanie, p.tytul, p.podobienstwo
                FROM feedback f JOIN pytania p ON f.pytanie_id = p.id
                WHERE f.ocena = -1
                ORDER BY f.czas DESC LIMIT 10
            """)
            zle = cur.fetchall()

    return {
        "pytania":              total,
        "srednie_podobienstwo": round((avg or 0) * 100, 1),
        "top_paragrafy":        [dict(w) for w in top],
        "zle_odpowiedzi":       [dict(z) for z in zle]
    }