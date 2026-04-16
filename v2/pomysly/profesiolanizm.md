# Przewodnik: Jak uprofesjonalnić projekt Flask (Standard Produkcyjny)

Ten dokument zawiera szczegółowe instrukcje, jak przekształcić hobbystyczny projekt w profesjonalną aplikację zgodną ze standardami rynkowymi.

### 📋 Zasady kategoryzacji zadań:
1.  **Kolejność**: Zadania są ułożone od najprostszych do najbardziej złożonych.
2.  **Statusy**:
    - `📅 DO ZROBIENIA` – Zadanie zaplanowane, czeka na rozpoczęcie.
    - `⏳ W TRAKCIE`    – Trwają prace nad implementacją lub dokumentacją techniczną.
    - `✅ ZREALIZOWANE` – Zadanie ukończone
---

## ✅ ZREALIZOWANE: 1. Zarządzanie konfiguracją i bezpieczeństwo (.env)
Nigdy nie przechowuj haseł ani tokenów bezpośrednio w kodzie źródłowym.

### Instrukcja:
1. **Zainstaluj bibliotekę:** `pip install python-dotenv`
2. **Utwórz plik `.env`** w głównym katalogu (uzupełnij swoimi danymi):
   ```env
   ADMIN_TOKEN=twoj-tajny-token-produkcyjny
   FLASK_ENV=development
   DATABASE_URL=data/baza_wiedzy.json
   ```
3. **Zabezpiecz plik:** Dodaj `.env` do pliku `.gitignore`. To kluczowe, aby hasła nie trafiły na GitHuba!
4. **Stwórz wzorzec:** Dodaj plik `.env.example` do repozytorium (z pustymi wartościami), aby inni wiedzieli, jakich kluczy brakuje.
5. **Wczytaj zmienne w `app.py`:**
   ```python
   from dotenv import load_dotenv
   import os
   
   load_dotenv() # Ładuje zmienne z pliku .env
   ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
   ```

---

## ✅ ZREALIZOWANE: 2. Separacja odpowiedzialności (Struktura plików)
Czysty podział na Frontend (wygląd i interakcje) i Backend (logika) ułatwia pracę w zespole i rozwój projektu.

### Rekomendowana struktura:
```text
/projekt
├── static/          # Pliki statyczne (publiczne)
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/       # Szablony HTML
│   ├── index.html
│   └── admin.html
├── core/            # Logika biznesowa (Python)
├── tests/           # Testy automatyczne
├── app.py           # Punkt wejścia aplikacji
└── requirements.txt # Lista zależności
```

### Zmiana w HTML (`templates/index.html`):
Zamiast pisać CSS/JS wewnątrz pliku `.html` w tagach `<style>` i `<script>`, użyj wbudowanego we Flaska mechanizmu `url_for`:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
<script src="{{ url_for('static', filename='js/main.js') }}"></script>
```

---

## ✅ ZREALIZOWANE: 3. Kontrola jakości kodu (Lintery i Formattery)
Zautomatyzuj sprawdzanie błędów, nieużywanych importów i formatowanie kodu zgodnie z PEP 8.

### Instrukcja (Ruff):
1. **Zainstaluj narzędzie:** `pip install ruff`
2. **Dodaj sprawdzanie do GitHub Actions (`.github/workflows/testy.yml`):**
   ```yaml
   - name: Lint with Ruff
     run: |
       pip install ruff
       ruff check .
   ```

---

## 📅 DO ZROBIENIA: 4. Konteneryzacja (Docker)
Docker pozwala na uruchomienie aplikacji w dokładnie takim samym, izolowanym środowisku na każdym komputerze i serwerze, eliminując problem "u mnie działa".

### Przykład pliku `Dockerfile` (umieść w głównym folderze):
```dockerfile
# Używamy lekkiego obrazu z Pythonem 3.13
FROM python:3.13-slim

# Ustawiamy katalog roboczy
WORKDIR /app

# Kopiujemy pliki i instalujemy biblioteki
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy resztę kodu
COPY . .

# Wystawiamy port aplikacji
EXPOSE 5000

# Komenda uruchamiająca serwer
CMD ["python", "app.py"]
```

---

## 📅 DO ZROBIENIA: 5. Dokumentacja (README.md)
Dobre README to klucz do sukcesu projektu na GitHubie – to pierwsza rzecz, którą widzi rekruter lub inny programista.

### Co powinno zawierać profesjonalne README?
- **Opis projektu:** Krótkie podsumowanie, co robi ta aplikacja.
- **Zrzuty ekranu (Screenshots):** Pokaż interfejs graficzny aplikacji.
- **Technologie:** Lista użytych bibliotek i języków (Python, Flask, SQLite).
- **Instrukcja uruchomienia lokalnie:**
  - Jak utworzyć venv.
  - Jak zainstalować zależności (`pip install -r requirements.txt`).
  - Jak uruchomić aplikację.
- **Zmienne środowiskowe:** Opis kluczy potrzebnych do pliku `.env`.


---

## ✅ ZREALIZOWANE: 6. Testy automatyczne (CI/CD)
Upewnij się, że każda modyfikacja wgrywana do repozytorium jest stabilna.

Aby zautomatyzować ten proces, stwórz plik wymuszający analizę po każdym poleceniu PUSH do gałęzi głównej.

**Ścieżka pliku:** `.github/workflows/testy.yml`
```yaml
name: Weryfikacja Jakości PWr
on: [push]

jobs:
  test_and_lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Przygotowanie srodowiska Python 3.13
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"
          
      - name: Instalacja zaleznosci
        run: |
          python -m pip install --upgrade pip
          pip install ruff python-dotenv
          # Instaluje biblioteki zewnetrzne z Flaska jesli istnieja (nie ma uzytych gotowych AI bibliotek)
          if [ -f v2/requirements.txt ]; then pip install -r v2/requirements.txt; fi
          
      - name: Skanowanie Skladniowe (Ruff)
        run: ruff check .
          
      - name: Egzekucja Testow Asystenta
        run: |
          cd v2
          python tests/test.py
