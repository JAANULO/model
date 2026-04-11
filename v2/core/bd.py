"""
db.py – baza SQLite (lokalnie) lub PostgreSQL/Supabase (produkcja).
TRYB wykrywany automatycznie przez zmienną środowiskową DATABASE_URL.
"""
import os
import sqlite3
from contextlib import contextmanager

DATABASE_URL = os.environ.get("DATABASE_URL")
TRYB = "postgres" if DATABASE_URL else "sqlite"


if TRYB == "postgres":
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2.pool import ThreadedConnectionPool

    pg_pool = ThreadedConnectionPool(1, 10, DATABASE_URL)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PLIK_DB = os.path.join(BASE_DIR, "..", "data", "asystent.db")

@contextmanager
def polacz():
    if TRYB == "postgres":
        conn = pg_pool.getconn()
        # dla gładkiego zmapowania RealDictCursor z puli
        conn.cursor_factory = RealDictCursor
        try:
            yield conn
        finally:
            pg_pool.putconn(conn)
    else:
        conn = sqlite3.connect(PLIK_DB)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


def inicjalizuj():
    """Tworzy tabele jeśli nie istnieją."""
    if TRYB == "postgres":
        # tabele już stworzone w Supabase przez SQL Editor
        pass
    else:
        with polacz() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS pytania (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    pytanie     TEXT NOT NULL,
                    tytul       TEXT,
                    podobienstwo REAL,
                    odpowiedz   TEXT,
                    baza        TEXT DEFAULT 'studia',
                    czas        TEXT DEFAULT (datetime('now','localtime'))
                );
                CREATE TABLE IF NOT EXISTS feedback (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    pytanie_id  INTEGER REFERENCES pytania(id),
                    ocena       INTEGER NOT NULL,
                    komentarz   TEXT,
                    czas        TEXT DEFAULT (datetime('now','localtime'))
                );
            """)


def zapisz_pytanie(pytanie, tytul, podobienstwo, baza="studia", odpowiedz=None):
    if TRYB == "postgres":
        with polacz() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO pytania (pytanie, tytul, podobienstwo, baza, odpowiedz) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                    (pytanie, tytul, podobienstwo, baza, odpowiedz)
                )
                conn.commit()
                return cur.fetchone()["id"]
    else:
        with polacz() as conn:
            cur = conn.execute(
                "INSERT INTO pytania (pytanie, tytul, podobienstwo, baza, odpowiedz) VALUES (?,?,?,?,?)",
                (pytanie, tytul, podobienstwo, baza, odpowiedz)
            )
            return cur.lastrowid


def zapisz_feedback(pytanie_id, ocena, komentarz=None):
    if TRYB == "postgres":
        with polacz() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO feedback (pytanie_id, ocena, komentarz) VALUES (%s,%s,%s)",
                    (pytanie_id, ocena, komentarz)
                )
                conn.commit()
    else:
        with polacz() as conn:
            conn.execute(
                "INSERT INTO feedback (pytanie_id, ocena, komentarz) VALUES (?,?,?)",
                (pytanie_id, ocena, komentarz)
            )


def pobierz_wspolczynniki_zbiorczo():
    zapytanie = """
        SELECT p.tytul, SUM(f.ocena) as suma_ocen
        FROM feedback f
        JOIN pytania p ON f.pytanie_id = p.id
        WHERE p.tytul IS NOT NULL
        GROUP BY p.tytul
    """
    if TRYB == "postgres":
        with polacz() as conn:
            with conn.cursor() as cur:
                cur.execute(zapytanie)
                wyniki = cur.fetchall()
    else:
        with polacz() as conn:
            wyniki = conn.execute(zapytanie).fetchall()

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
    """Pobiera zapisane pytanie na podstawie jego ID."""
    if TRYB == "postgres":
        with polacz() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT pytanie, tytul, podobienstwo, odpowiedz FROM pytania WHERE id = %s",
                    (pytanie_id,)
                )
                return cur.fetchone()
    else:
        with polacz() as conn:
            return conn.execute(
                "SELECT pytanie, tytul, podobienstwo, odpowiedz FROM pytania WHERE id = ?",
                (pytanie_id,)
            ).fetchone()


def pobierz_ostatnie_pytania(limit=10):
    """Zwraca ostatnie unikalne pytania do panelu historii."""
    if TRYB == "postgres":
        with polacz() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT pytanie FROM pytania WHERE pytanie IS NOT NULL AND pytanie <> '' ORDER BY id DESC LIMIT %s",
                    (limit * 3,)
                )
                rows = cur.fetchall()
    else:
        with polacz() as conn:
            rows = conn.execute(
                "SELECT pytanie FROM pytania WHERE pytanie IS NOT NULL AND pytanie <> '' ORDER BY id DESC LIMIT ?",
                (limit * 3,)
            ).fetchall()

    unikalne = []
    widziane = set()
    for row in rows:
        p = row["pytanie"]
        if p in widziane:
            continue
        widziane.add(p)
        unikalne.append({"pytanie": p})
        if len(unikalne) >= limit:
            break
    return unikalne


def pobierz_statystyki():
    if TRYB == "postgres":
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
                            FROM feedback f
                                     JOIN pytania p ON f.pytanie_id = p.id
                            WHERE f.ocena = -1
                            ORDER BY f.czas DESC LIMIT 10
                            """)
                zle = cur.fetchall()

                cur.execute("""
                            SELECT TO_CHAR(czas::timestamp, 'YYYY-MM-DD') as dzien, COUNT(*) as liczba
                            FROM pytania
                            GROUP BY dzien
                            ORDER BY dzien LIMIT 30
                            """)
                dzienne = cur.fetchall()

                cur.execute("""
                            SELECT czas, pytanie, odpowiedz, podobienstwo
                            FROM pytania
                            ORDER BY id DESC LIMIT 50
                            """)
                ostatnie = cur.fetchall()
    else:
        with polacz() as conn:
            total = conn.execute("SELECT COUNT(*) FROM pytania").fetchone()[0]
            avg   = conn.execute("SELECT AVG(podobienstwo) FROM pytania").fetchone()[0]
            top   = conn.execute("""
                SELECT tytul, COUNT(*) as n
                FROM pytania WHERE tytul IS NOT NULL
                GROUP BY tytul ORDER BY n DESC LIMIT 5
            """).fetchall()

            zle = conn.execute("""
                               SELECT p.pytanie, p.tytul, p.podobienstwo
                               FROM feedback f
                                        JOIN pytania p ON f.pytanie_id = p.id
                               WHERE f.ocena = -1
                               ORDER BY f.czas DESC LIMIT 10
                                 """).fetchall()

            dzienne = conn.execute("""
                                   SELECT substr(czas, 1, 10) as dzien, COUNT(*) as liczba
                                   FROM pytania
                                   GROUP BY substr(czas, 1, 10)
                                   ORDER BY dzien LIMIT 30
                                   """).fetchall()

            ostatnie = conn.execute("""
                                    SELECT czas, pytanie, odpowiedz, podobienstwo
                                    FROM pytania
                                    ORDER BY id DESC LIMIT 50
                                    """).fetchall()

    return {
        "pytania": total,
        "srednie_podobienstwo": round((avg or 0) * 100, 1),
        "top_paragrafy": [dict(w) for w in top],
        "zle_odpowiedzi": [dict(z) for z in zle],
        "pytania_dzienne": [dict(d) for d in dzienne],
        "ostatnie_pytania": [dict(o) for o in ostatnie],
    }
