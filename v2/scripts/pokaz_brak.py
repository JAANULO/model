import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLIK_BAZY = os.path.join(BASE_DIR, "data", "baza_wiedzy.json")

with open(PLIK_BAZY, encoding='utf-8') as f:
    baza = json.load(f)

szukaj = ['§ 21', '§ 19', '§ 33', '§ 11']

for p in baza:
    for s in szukaj:
        if p['tytul'].startswith(s):
            print(f"\n{'='*60}")
            print(f"TYTUŁ: {p['tytul']}")
            print(p['tresc'][:500])
