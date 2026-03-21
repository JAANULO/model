> 🇬🇧 [English](#-pwr-regulatory-assistant) &nbsp;|&nbsp; 🇵🇱 [Polski](#-asystent-regulaminowy-pwr)

---

# 🇬🇧 PWr Regulatory Assistant

> An information retrieval system for the study regulations of Wrocław University of Science and Technology (PWr).  
> Unlike classic LLMs that hallucinate — **this system always cites the exact source paragraph**.

An academic project built entirely from scratch — no NLP libraries (no sklearn, no Hugging Face, no external APIs).

---

## How It Works

```
user question: "how many times can I take an exam?"
         ↓
  tokenization + normalization
  (stemming, typo correction, diacritic removal)
         ↓
  BM25 — each word of the query compared against every paragraph
  (Best Match 25 — improves TF-IDF with document length normalization)
         ↓
  cosine similarity → paragraph ranking
         ↓
  answer + source: "§ 18. Exams"
```

All algorithms implemented **from scratch in pure Python**.

---

## Project Versions

### Version 1.0 – Generative Mini-GPT

A custom GPT architecture implementation written from scratch in PyTorch.  
The model learns to generate text based on a training sentence corpus.

**Features:**
- Transformer architecture with Multi-Head Attention mechanism
- Character-level tokenizer (43-token vocabulary)
- Batch training on GPU (CUDA)
- Model saving and loading with cache
- Compressed model export to GitHub (Git LFS)
- Conversation mode with memory of last 3 exchanges

**Model parameters:**

| Parameter | Value |
|---|---|
| Embedding dimension | 256 |
| Transformer layers | 6 |
| Multi-Head Attention heads | 8 |
| Total parameters | ~831,000 |
| Final loss (cross-entropy) | 0.084 |
| Training time (RTX 3060 Ti) | ~12 min |

---

### Version 2.0 – Regulatory Assistant

An extension of v1 with an information retrieval system for the PWr study regulations.  
Instead of generating answers from memory (risking hallucinations), the system first retrieves the correct regulation paragraph and then formulates a response.

**Features:**
- PDF parser (`pdfplumber`) for multiple files from `v2/data/` → separate JSON per document
- **BM25** algorithm from scratch (replaces TF-IDF — better accuracy for varying paragraph lengths)
- Cosine similarity for result ranking
- Levenshtein distance for typo correction (from scratch)
- Dictionary of ~180 Polish synonyms and word forms
- BM25 vector cache (`.pkl` file) — instant startup
- In-memory answer cache in API (`/zapytaj`) — TTL 1h, max 500 entries
- Direct paragraph retrieval by number (`§18`, `paragraph 18`) without BM25 recomputation
- **Sentence-level index** — instead of returning whole paragraphs, finds the exact sentence with the answer
- **Intent classifier** — detects question type (NUMBER / DATE / YES-NO / CONSEQUENCE / PROCEDURE) and returns a direct short answer, e.g. "You can take the exam **2 times**."
- **Number and date extraction via regex** — returns concrete values instead of regulation text
- **Conversation context memory** — follow-up questions like "and what if I fail?" refer to the previous paragraph
- Web interface (Flask + HTML/CSS/JS) with mobile support, light/dark mode toggle, sidebar with last 10 queries, and PDF export of chat
- CLI interface with conversation history
- **SQLite database** for statistics and feedback (`v2/data/asystent.db`)
- Text logs to `v2/logs/log.txt` (GUI + CLI runtime events)
- Feedback buttons 👍/👎 in GUI — saved to database; low-confidence negative feedback is appended to `v2/logs/do_poprawy.txt`
- Automated tests (`tests/test.py`) — regression set of 77 questions, **77/77 accuracy**
- `/historia` endpoint — last 10 questions from SQLite
- `/admin` dashboard (Chart.js) secured by `ADMIN_TOKEN`
---

## Test Results

| Metric | Value |
|---|---|
| Test set size | 77 questions |
| Accuracy (correct paragraph) | **77/77 (100%)** |
| Response time | < 50 ms |
| Knowledge base size | 40 paragraphs |
| Sentence index size | 465 sentences |
| BM25 vocabulary | ~2166 unique words |
| Synonym dictionary entries | ~180 |
| Query expansion entries | ~80 |

---

## Project Architecture

```
Mini-GPT/
├── shared/                     ← shared modules (v1 & v2)
│   ├── transformer.py          # GPT architecture (from scratch)
│   └── tokenizer.py            # character tokenizer
│
├── v1/                         ← generative version
│   ├── main.py                 # training + conversation mode
│   └── dane.json               # training data
│
└── v2/                         ← regulatory assistant
├── main.py                 # entry point: training + CLI loop
├── app.py                  # Flask server (GUI)
├── parser.py               # PDFs in data/ → JSON knowledge files
├── asystent.py             # standalone CLI interface
├── requirements.txt        # Python dependencies
│
├── core/                   ← search & formatting logic
│   ├── wyszukiwarka.py     # BM25 + Levenshtein + cosine
│   ├── formatowanie.py     # response formatting
│   └── bd.py               # SQLite: stats, feedback
│
├── data/
│   ├── *.pdf               # source documents
│   ├── *.json              # parsed knowledge files (one per document)
│   └── *_cache.pkl         # BM25 / sentence index caches
│
├── tests/
│   └── test.py             # automated tests (regression set, 50+ questions)
│
└── templates/
    ├── index.html          # web interface
    └── admin.html          # stats dashboard (Chart.js)
```

---

## Installation & Usage

### Requirements

- Python 3.10+
- NVIDIA GPU with CUDA support (optional — also runs on CPU)

### Install dependencies

```bash
# PyTorch with CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# other libraries
pip install numpy tqdm pdfplumber flask
```

---

### Version 1.0 — Mini-GPT

```bash
cd v1
python main.py
```

The program automatically trains the model and starts conversation mode.  
On subsequent runs it loads the model from cache (training is skipped).

---

### Version 2.0 — Regulatory Assistant

**Step 1 — generate the knowledge base** (once, or when PDFs in `v2/data/` change):

```bash
cd v2
python parser.py
```

**Step 2 — launch the GUI:**

```bash
python app.py
# → open http://localhost:5000
```

**Step 3 — run the tests:**

```bash
python tests/test.py
```

**Alternatively — CLI interface:**

```bash
python asystent.py
```

**Optional debug helper (PDF parser check):**

```bash
python tests/debug_parser.py
```

### Troubleshooting (v2)

- `FileNotFoundError` for missing knowledge files
  - Run `python parser.py` in `v2` to parse PDFs from `v2/data/` into JSON files.
- Red underline on `from core...` in IDE
  - In JetBrains: mark `v2` as **Sources Root** and use the same interpreter as runtime.
- Relative import error (`attempted relative import with no known parent package`)
  - Do not run package modules by file path; use project entry points (`python app.py`, `python asystent.py`, `python tests/test.py`).
- Missing logs in root `logs/`
  - Runtime logs are stored in `v2/logs/log.txt` (not in repository root).

---

### CLI Commands

| Command | Description |
|---|---|
| `/szukaj <question>` | show top 3 paragraphs with similarity scores |
| `/historia` | show conversation history |
| `/zapomnij` | clear conversation history |
| `/info` | knowledge base info (paragraph count, vocabulary size) |
| `/pomoc` | list all commands |
| `koniec` | exit the program |

---

## Technologies Used

| Technology | Purpose |
|---|---|
| **Python 3.13** | entire backend |
| **PyTorch** | Transformer architecture, GPU training |
| **NumPy** | matrix operations |
| **pdfplumber** | PDF regulation parsing |
| **Flask** | HTTP server for GUI |
| **SQLite** | statistics and feedback storage |
| **tqdm** | training progress bar |
| **Git LFS** | model file storage on GitHub |

**Algorithms implemented from scratch** (no external NLP libraries):
- **BM25** (Best Match 25 — improved TF-IDF used by Elasticsearch)
- Cosine similarity
- Levenshtein distance (typo correction)
- GPT / Transformer architecture
- Character-level tokenizer

---

## Hardware

| Component | Specification |
|---|---|
| CPU | Intel Core i7-11700F |
| GPU | NVIDIA RTX 3060 Ti 8 GB |
| RAM | 32 GB |
| OS | Windows 10 |

---



# 🇵🇱 Asystent Regulaminowy PWr

> System wyszukiwania informacji z regulaminu studiów Politechniki Wrocławskiej.  
> Zamiast halucynować jak klasyczne LLM — **zawsze podaje źródłowy paragraf regulaminu**.

Projekt akademicki zbudowany od zera — bez gotowych bibliotek NLP (bez sklearn, bez Hugging Face, bez zewnętrznych API).

---

## Jak to działa

```
pytanie użytkownika: "ile razy można podejść do egzaminu?"
         ↓
  tokenizacja + normalizacja
  (usuwanie odmiany, literówek, polskich znaków)
         ↓
  BM25 — każde słowo pytania porównywane z każdym paragrafem
  (Best Match 25 — ulepsza TF-IDF o normalizację długości dokumentu)
         ↓
  podobieństwo cosinusowe → ranking paragrafów
         ↓
  odpowiedź + źródło: "§ 18. Egzaminy"
```

Wszystkie algorytmy napisane **od zera w czystym Pythonie**.

---


## Wersje projektu

### Wersja 1.0 – Mini-GPT generatywny

Własna implementacja modelu GPT napisana od zera bez gotowych frameworków NLP.  
Model uczy się generować tekst na podstawie zbioru zdań treningowych.

**Co zawiera:**
- Architektura Transformer z mechanizmem Multi-Head Attention
- Znakowy tokenizer (słownik 43 tokenów)
- Trening batchowy na GPU (CUDA)
- Zapis i wczytywanie modelu z cache
- Eksport skompresowanego modelu na GitHub (Git LFS)
- Tryb rozmowy z pamięcią ostatnich 3 wymian

**Parametry modelu:**

| Parametr | Wartość |
|---|---|
| Wymiar embeddingu | 256 |
| Liczba warstw Transformera | 6 |
| Głowice Multi-Head Attention | 8 |
| Parametry łącznie | ~831 000 |
| Strata końcowa (cross-entropy) | 0.084 |
| Czas treningu (RTX 3060 Ti) | ~12 min |

---

### Wersja 2.0 – Asystent Regulaminowy PWr

Rozbudowa v1 o system wyszukiwania informacji z regulaminu studiów Politechniki Wrocławskiej.  
Zamiast halucynować, model najpierw wyszukuje właściwy paragraf, a potem generuje odpowiedź.

**Co zawiera:**
- Parser PDF (`pdfplumber`) dla wielu plików z `v2/data/` → osobne JSON dla dokumentów
- Algorytm **BM25** napisany od zera (zastąpił TF-IDF — lepsza trafność dla różnej długości paragrafów)
- Podobieństwo cosinusowe do rankingu wyników
- Korekcja literówek algorytmem Levenshteina (napisanym od zera)
- Słownik ~180 synonimów i odmian dla języka polskiego
- Cache wektorów BM25 (plik `.pkl`) — natychmiastowy start
- Cache odpowiedzi w API (`/zapytaj`) — TTL 1h, max 500 wpisów
- Bezpośrednie trafienie paragrafu po numerze (`§18`, `paragraf 18`) bez liczenia BM25
- **Indeks na poziomie zdań** — zamiast zwracać cały paragraf, system znajduje konkretne zdanie z odpowiedzią
- **Klasyfikator intencji** — wykrywa typ pytania (LICZBA / TERMIN / TAK-NIE / SKUTEK / PROCEDURA) i zwraca krótką bezpośrednią odpowiedź, np. „Możesz podejść do egzaminu **2 razy**."
- **Ekstrakcja liczb i terminów przez regex** — konkretne wartości zamiast tekstu regulaminu
- **Pamięć kontekstu rozmowy** — pytania następcze typu „a co jak nie zdam?" odnoszą się do poprzedniego paragrafu
- Interfejs webowy (Flask + HTML/CSS/JS) z obsługą mobile, przełącznikiem jasny/ciemny, panelem historii i eksportem rozmowy do PDF
- Interfejs CLI z historią rozmowy
- **Baza SQLite** dla statystyk i feedbacku (`v2/data/asystent.db`)
- Logi tekstowe do `v2/logs/log.txt` (zdarzenia uruchomieniowe GUI/CLI)
- Przyciski feedbacku 👍/👎 w GUI — zapisywane do bazy; słabe odpowiedzi trafiają do `v2/logs/do_poprawy.txt`
- Testy automatyczne (`tests/test.py`) — zestaw regresyjny 77 pytań, **trafność 77/77**
- Endpoint `/historia` — ostatnie 10 pytań z SQLite
- Dashboard `/admin` (Chart.js) zabezpieczony tokenem `ADMIN_TOKEN`

## Architektura projektu

```
Mini-GPT/
├── shared/                     ← wspólne moduły (v1 i v2)
│   ├── transformer.py          # architektura GPT (od zera)
│   └── tokenizer.py            # tokenizer znakowy
│
├── v1/                         ← wersja generatywna
│   ├── main.py                 # trening + tryb rozmowy
│   └── dane.json               # dane treningowe
│
└── v2/                         ← asystent regulaminowy
    ├── main.py                 # punkt wejścia: trening + pętla CLI
    ├── app.py                  # serwer Flask (GUI)
    ├── parser.py               # PDF-y z data/ → pliki JSON wiedzy
    ├── asystent.py             # samodzielny interfejs CLI
    ├── requirements.txt        # zależności Pythona
    │
    ├── core/                   ← logika wyszukiwania i formatowania
    │   ├── wyszukiwarka.py     # BM25 + Levenshtein + cosinus
    │   ├── formatowanie.py     # formatowanie odpowiedzi
    │   └── bd.py               # SQLite: statystyki, feedback
    │
    ├── data/
    │   ├── *.pdf               # dokumenty źródłowe
    │   ├── *.json              # baza wiedzy per dokument
    │   └── *_cache.pkl         # cache indeksów BM25 i zdań
    │
    ├── tests/
    │   └── test.py             # testy automatyczne (zestaw regresyjny, 50+ pytań)
    │
    └── templates/
        ├── index.html          # interfejs webowy
        └── admin.html          # dashboard statystyk
```
---

## Wyniki testów

| Metryka | Wartość |
|---|---|
| Rozmiar zestawu testowego | 77 pytań |
| Trafność (właściwy paragraf) | **77/77 (100%)** |
| Czas odpowiedzi | < 50 ms |
| Rozmiar bazy | 40 paragrafów |
| Rozmiar indeksu zdań | 465 zdań |
| Słownik BM25 | ~2166 unikalnych słów |
| Synonimów w słowniku | ~180 wpisów |
| Wpisów rozszerzenia zapytań | ~80 |

---

##  Instalacja i uruchomienie

### Wymagania

- Python 3.10+
- NVIDIA GPU z obsługą CUDA (opcjonalnie – działa też na CPU)

### Instalacja zależności

```bash
# PyTorch z obsługą CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# pozostałe biblioteki
pip install numpy tqdm pdfplumber flask
```

---

### Wersja 1.0


```bash
cd v1
python main.py
```

Program automatycznie wytrenuje model i uruchomi tryb rozmowy.  
Przy kolejnych uruchomieniach wczytuje model z cache (trening pomijany).

---

### Wersja 2.0 — Asystent Regulaminowy

**Krok 1 — wygeneruj bazę wiedzy** (tylko raz, lub gdy zmienią się PDF-y w `v2/data/`):

```bash
cd v2
python parser.py
```

**Krok 2 — uruchom GUI:**

```bash
python app.py
# → otwórz http://localhost:5000
```

**Krok 3 — uruchom testy:**

```bash
python tests/test.py
```

**Alternatywnie — interfejs CLI:**

```bash
python asystent.py
```

**Opcjonalnie — szybki debug parsera PDF:**

```bash
python tests/debug_parser.py
```

### Rozwiązywanie problemów (v2)

- `FileNotFoundError` dla plików wiedzy
  - Uruchom `python parser.py` w katalogu `v2`, aby sparsować PDF-y z `v2/data/` do JSON.
- Czerwone podkreślenie `from core...` w IDE
  - W JetBrains oznacz `v2` jako **Sources Root** i użyj tego samego interpretera co przy uruchomieniu.
- Błąd importu względnego (`attempted relative import with no known parent package`)
  - Nie uruchamiaj modułów pakietu po ścieżce pliku; używaj punktów wejścia projektu (`python app.py`, `python asystent.py`, `python tests/test.py`).
- Brak logów w `logs/` w katalogu głównym repo
  - Logi runtime zapisują się do `v2/logs/log.txt`.

---

### Komendy CLI

| Komenda | Opis |
|---|---|
| `/szukaj <pytanie>` | pokaż 3 najlepsze paragrafy z wynikami |
| `/historia` | pokaż historię rozmowy |
| `/zapomnij` | wyczyść historię |
| `/info` | informacje o bazie (liczba paragrafów, słów) |
| `/pomoc` | lista komend |
| `koniec` | zakończ program |

---

##  Użyte Technologie

| Technologia | Zastosowanie |
|---|---|
| **Python 3.13** | cały backend |
| **PyTorch** | architektura Transformer, trening GPU |
| **NumPy** | operacje na macierzach |
| **pdfplumber** | parsowanie regulaminu PDF |
| **Flask** | serwer HTTP dla GUI |
| **SQLite** | statystyki i feedback |
| **tqdm** | pasek postępu treningu |
| **Git LFS** | przechowywanie plików modelu na GitHub |

**Algorytmy zaimplementowane od zera** (bez zewnętrznych bibliotek NLP):
- BM25 (Best Match 25 — ulepszony TF-IDF, używany przez Elasticsearch)
- Podobieństwo cosinusowe
- Odległość Levenshteina (korekcja literówek)
- Architektura GPT / Transformer
- Tokenizer znakowy

---

##  Sprzęt testowy

| Komponent | Specyfikacja |
|---|---|
| CPU | Intel Core i7-11700F |
| GPU | NVIDIA RTX 3060 Ti 8 GB |
| RAM | 32 GB |
| System | Windows 10 |
