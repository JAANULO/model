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
  TF-IDF — each word of the query compared against every paragraph
  (Term Frequency × Inverse Document Frequency)
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
- PDF regulation parser (`pdfplumber`) — splits the document into 40 paragraphs
- TF-IDF algorithm from scratch (no sklearn)
- Cosine similarity for result ranking
- Levenshtein distance for typo correction (from scratch)
- Dictionary of ~180 Polish synonyms and word forms
- TF-IDF vector cache (`.pkl` file) — instant startup
- Web interface (Flask + HTML/CSS/JS)
- CLI interface with conversation history and logging
- Automated tests (`test.py`) — 20 test questions
- `/statistics` endpoint — query count, average similarity, top paragraphs

---

## Test Results

| Metric | Value |
|---|---|
| Test set | 20 questions |
| Accuracy (correct paragraph) | run `python test.py` |
| Response time | < 50 ms |
| Knowledge base size | 40 paragraphs |
| TF-IDF vocabulary | ~400 unique words |
| Synonym dictionary entries | ~180 |

---

## Project Architecture

```
Mini-GPT/
├── v1/                         ← generative version
│   ├── main.py                 # training + conversation mode
│   ├── transformer.py          # GPT architecture (from scratch)
│   ├── tokenizer.py            # character tokenizer
│   └── dane.json               # training data
│
└── v2/                         ← regulatory assistant
    ├── parser.py               # PDF → baza_wiedzy.json
    ├── wyszukiwarka.py         # TF-IDF + Levenshtein + cosine
    ├── formatowanie.py         # response formatting
    ├── asystent.py             # CLI interface
    ├── app.py                  # Flask server (GUI)
    ├── test.py                 # automated tests
    ├── baza_wiedzy.json        # 40 regulation paragraphs
    ├── baza_wiedzy_cache.pkl   # vector cache (auto-generated)
    ├── log.txt                 # session logs (auto-generated)
    ├── regulamin.pdf           # PWr study regulations PDF
    └── templates/
        └── index.html          # web interface
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

**Step 1 — generate the knowledge base** (once, or when the PDF changes):

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
python test.py
```

**Alternatively — CLI interface:**

```bash
python asystent.py
```

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
| **tqdm** | training progress bar |
| **Git LFS** | model file storage on GitHub |

**Algorithms implemented from scratch** (no external NLP libraries):
- TF-IDF (Term Frequency — Inverse Document Frequency)
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
  TF-IDF — każde słowo pytania porównywane z każdym paragrafem
  (Term Frequency × Inverse Document Frequency)
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
- Parser PDF regulaminu (`pdfplumber`) — dzieli dokument na 40 paragrafów
- Algorytm TF-IDF napisany od zera (bez sklearn)
- Podobieństwo cosinusowe do rankingu wyników
- Korekcja literówek algorytmem Levenshteina (napisanym od zera)
- Słownik ~180 synonimów i odmian dla języka polskiego
- Cache wektorów TF-IDF (plik `.pkl`) — natychmiastowy start
- Interfejs webowy (Flask + HTML/CSS/JS)
- Interfejs CLI z historią rozmowy i logowaniem
- Testy automatyczne (`test.py`) — 20 pytań testowych
- Endpoint `/statystyki` — liczba pytań, średnie dopasowanie, top paragrafy


## Architektura projektu

```
Mini-GPT/
├── v1/                         ← wersja generatywna
│   ├── main.py                 # trening + tryb rozmowy
│   ├── transformer.py          # architektura GPT (od zera)
│   ├── tokenizer.py            # tokenizer znakowy
│   └── dane.json               # dane treningowe
│
└── v2/                         ← asystent regulaminowy
    ├── parser.py               # PDF → baza_wiedzy.json
    ├── wyszukiwarka.py         # TF-IDF + Levenshtein + cosinus
    ├── formatowanie.py         # formatowanie odpowiedzi
    ├── asystent.py             # interfejs CLI
    ├── app.py                  # serwer Flask (GUI)
    ├── test.py                 # testy automatyczne
    ├── baza_wiedzy.json        # 40 paragrafów regulaminu
    ├── baza_wiedzy_cache.pkl   # cache wektorów (auto-generowany)
    ├── log.txt                 # logi sesji (auto-generowany)
    ├── regulamin.pdf           # regulamin studiów PWr
    └── templates/
        └── index.html          # interfejs webowy
```
---

## Wyniki testów

| Metryka | Wartość |
|---|---|
| Zestaw testowy | 20 pytań |
| Trafność (właściwy paragraf) | uruchom `python test.py` |
| Czas odpowiedzi | < 50 ms |
| Rozmiar bazy | 40 paragrafów |
| Słownik TF-IDF | ~400 unikalnych słów |
| Synonimów w słowniku | ~180 wpisów |

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
pip install numpy tqdm pdfplumber
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

**Krok 1 — wygeneruj bazę wiedzy** (tylko raz, lub gdy zmieni się PDF):

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
python test.py
```

**Alternatywnie — interfejs CLI:**

```bash
python asystent.py
```

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
| **tqdm** | pasek postępu treningu |
| **Git LFS** | przechowywanie plików modelu na GitHub |

**Algorytmy zaimplementowane od zera** (bez zewnętrznych bibliotek NLP):
- TF-IDF (Term Frequency — Inverse Document Frequency)
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
