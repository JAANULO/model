# debug.py
import inspect
import re
import os
import sys

from core.indeks_zdan import IndeksZdan
from core.intencje import (
    _usun_ogonki,
    wyciagnij_liczbe,
    wyciagnij_termin,
    wykryj_intencje,
)
from core.wyszukiwarka import Wyszukiwarka


idx = IndeksZdan('data/baza_wiedzy.json')
w = Wyszukiwarka('data/baza_wiedzy.json')

pytania = [
    'ile dni miedzy terminami egzaminu',
    'ile razy mozna powtarzac przedmiot',
    'kiedy mozna wziac urlop dziekanski',
]

for pyt in pytania:
    print(f'\n--- {pyt} ---')
    for z in idx.szukaj(pyt, n_wynikow=5):
        liczba = wyciagnij_liczbe(z['zdanie'])
        termin = wyciagnij_termin(z['zdanie'])
        print(f"  {z['podobienstwo']:.3f} | L:{liczba} T:{termin} | {z['zdanie'][:100]}")

print('--- ile dni ---')
for z in idx.szukaj('ile dni miedzy terminami egzaminu', n_wynikow=5):
    print(f"  {z['podobienstwo']:.3f} | L:{wyciagnij_liczbe(z['zdanie'])} | {z['zdanie'][:100]}")

print('\n--- powtarzac ---')
for z in idx.szukaj('ile razy mozna powtarzac przedmiot', n_wynikow=3):
    print(f"  {z['podobienstwo']:.3f} | L:{wyciagnij_liczbe(z['zdanie'])} | {z['zdanie'][:100]}")

print('\n--- szukam pieciodniowym ---')
for z in idx.zdania:
    if 'pięciodniowym' in z['tekst'] or 'pieciodniowym' in z['tekst']:
        print(z['tekst'][:120])

print('\n--- pelne zdanie z pieciodniowym ---')
for z in idx.zdania:
    if 'pięciodniowym' in z['tekst'] or 'pieciodniowym' in z['tekst']:
        print(repr(z['tekst']))

print('\n--- ile dni - tylko §18 ---')
for z in idx.zdania:
    if '§ 18' in z['tytul'] and ('odstep' in z['tekst'].lower() or 'odstęp' in z['tekst'].lower()):
        print(repr(z['tekst'][:150]))

print('\n--- ile dni top10 ---')
for z in idx.szukaj('ile dni miedzy terminami egzaminu', n_wynikow=10):
    print(f"  {z['podobienstwo']:.3f} | {z['tytul'][:20]} | {z['zdanie'][:80]}")

wyniki = w.szukaj('ile dni miedzy terminami egzaminu', n_wynikow=1)
print('BM25 tytul:', wyniki[0]['tytul'])

print("f")

pytanie = 'ile dni miedzy terminami egzaminu'
intencja = wykryj_intencje(pytanie)
print('intencja:', intencja)

wyniki_bm25 = w.szukaj(pytanie, n_wynikow=1)
tytul_bm25 = wyniki_bm25[0]['tytul']

zdania_wyniki = idx.szukaj(pytanie, n_wynikow=10)
for zw in zdania_wyniki:
    pasuje_tytul = zw['tytul'] == tytul_bm25
    pasuje_prog = zw['podobienstwo'] >= 0.1
    ma_odstep = any(s in zw['zdanie'].lower() for s in ["odstęp", "odstep", "pięciodniowym", "pieciodniowym"])
    print(f"  tytul_ok:{pasuje_tytul} prog_ok:{pasuje_prog} odstep:{ma_odstep} | {zw['zdanie'][:80]}")

print("f")

zdanie = 'Dopuszcza się drugą oraz trzecią realizację przedmiotu na zasadach ogólnych, określonych w niniejszym Regulaminie. W przypadku niezaliczenia przedmiotu, student realizuje po raz drugi lub trzeci wszystkie zajęcia'

print('oryginalne:', zdanie[:80])
print('bez ogonkow:', _usun_ogonki(zdanie.lower())[:80])
print('wyciagnij_liczbe:', wyciagnij_liczbe(zdanie))

tekst_czysty = re.sub(r'\bust\.?\s*\d+', '', zdanie)
tekst_czysty = re.sub(r'\bpkt\.?\s*\d+', '', tekst_czysty)
tekst_czysty = re.sub(r'\bart\.?\s*\d+', '', tekst_czysty)
tekst_czysty = re.sub(r'§\s*\d+', '', tekst_czysty)
tekst_czysty = re.sub(r'\b(czwartego|czwarty|czwartej|czterech)\s+tygodni\w*', '', tekst_czysty)
tekst_czysty = re.sub(r'\b(pierwszego|drugiego|trzeciego|czwartego|piątego|szóstego)\s+dnia\b', '', tekst_czysty)
tekst_czysty = re.sub(r'\b(pierwszego|drugiego|trzeciego|czwartego|piątego)\s+tygodnia\b', '', tekst_czysty)

print('po czyszczeniu:', tekst_czysty[:120])
print('szukam cyfry:', re.search(r'\b([1-9]\d?)\b', tekst_czysty))

tekst_lower = _usun_ogonki(tekst_czysty.lower())
print('szukam slownie:', any(s in tekst_lower for s in ['druga oraz trzecia', 'drugą oraz trzecią']))

print("f")
print(wykryj_intencje('ile razy mozna powtarzac przedmiot'))
print(wykryj_intencje('ile razy można powtarzać przedmiot'))

print("f")
print(inspect.getsource(wyciagnij_liczbe))

print("f")
pytanie = 'a co jak nie zdam'
pyt_ascii = pytanie.lower().translate(str.maketrans('ąćęłńóśźż', 'acelnoszzz'[:9]))
print('ascii:', pyt_ascii)

SYGNALY_KONTEKSTU = [
    "a co jak", "a jesli", "a jezeli", "co jak", "co jesli",
    "a co jesli", "i co wtedy", "co wtedy", "a wtedy",
    "a jak nie", "jak nie zdam", "jak obleje", "co jak nie",
    "a czy moge", "czy wtedy", "co z tym", "i co z",
]
for s in SYGNALY_KONTEKSTU:
    if s in pyt_ascii:
        print(f'TRAFIENIE: "{s}"')

print("f")
wyniki = w.szukaj('ile razy mozna podejsc do egzaminu a co jak nie zdam', n_wynikow=3)
for wyn in wyniki:
    print(round(wyn['podobienstwo'], 3), '|', wyn['tytul'])