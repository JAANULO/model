"""
db.py – baza SQLite dla logów, statystyk i feedbacku.
Zastępuje log.txt. Wbudowana biblioteka sqlite3 – zero instalacji.
"""
#import sqlite3
import os
import psycopg2
from psycopg2.extras import RealDictCursor
#from datetime import datetime

#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#PLIK_DB = os.path.join(BASE_DIR, "..", "data","asystent.db")

DATABASE_URL = os.environ.get("DATABASE_URL")

def polacz():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


def inicjalizuj():
    """tworzy tabele jeśli nie istnieją - tabele już są w Supabase, funkcja zostawiona dla kompatybilności"""
    pass

# Inicjalizacja bazy natychmiast przy załadowaniu modułu (przed jakimkolwiek zapytaniem)
inicjalizuj()

def zapisz_pytanie(pytanie, tytul, podobienstwo, baza="studia"):
    with polacz() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO pytania (pytanie, tytul, podobienstwo, baza) VALUES (%s,%s,%s,%s) RETURNING id",
                (pytanie, tytul, podobienstwo, baza)
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
                "SELECT pytanie, tytul, podobienstwo FROM pytania WHERE id = %s",
                (pytanie_id,)
            )
            return cur.fetchone()

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