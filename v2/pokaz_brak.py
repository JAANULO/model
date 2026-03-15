import json, os

with open('data/baza_wiedzy.json', encoding='utf-8') as f:
    baza = json.load(f)

szukaj = ['§ 21', '§ 19', '§ 33', '§ 11']

for p in baza:
    for s in szukaj:
        if p['tytul'].startswith(s):
            print(f"\n{'='*60}")
            print(f"TYTUŁ: {p['tytul']}")
            print(p['tresc'][:500])
