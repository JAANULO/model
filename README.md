#  Mini-GPT – Transformer od zera

Hobbystyczny projekt budowania modelu językowego od podstaw w Pythonie z PyTorch.  
Projekt składa się z dwóch wersji – generatywnej (v1) i wyszukiwawczej z asystentem regulaminowym (v2).

---

##  Opis projektu

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
| Wymiar | 256 |
| Liczba warstw | 6 |
| Głowice Attention | 8 |
| Parametry łącznie | ~831 000 |
| Strata po treningu | 0.084 |
| Czas treningu (RTX 3060 Ti) | ~12 min |

---

### Wersja 2.0 – Asystent Regulaminowy PWr

Rozbudowa v1 o system wyszukiwania informacji z regulaminu studiów Politechniki Wrocławskiej.  
Zamiast halucynować, model najpierw wyszukuje właściwy paragraf, a potem generuje odpowiedź.

**Architektura:**
```
pytanie użytkownika
        ↓
wyszukiwarka TF-IDF (napisana od zera)
znajduje właściwy paragraf regulaminu
        ↓
mini-GPT dostaje pytanie + fragment regulaminu
i generuje ludzką odpowiedź
        ↓
"możesz podejść do egzaminu dwa razy"
📖 Źródło: § 18. Egzaminy
```

**Co zawiera:**
- Parser PDF regulaminu (pdfplumber) – dzieli dokument na 40 paragrafów
- Algorytm TF-IDF napisany od zera (bez sklearn)
- Podobieństwo cosinusowe do rankingu wyników
- Mini-GPT trenowany na parach pytanie–kontekst–odpowiedź
- Wyświetlanie źródłowego paragrafu przy każdej odpowiedzi

---

##  Instalacja i uruchomienie

### Wymagania

- Python 3.10+
- NVIDIA GPU z obsługą CUDA (opcjonalnie – działa też na CPU)

### Instalacja bibliotek

```bash
# PyTorch z obsługą CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# pozostałe biblioteki
pip install numpy tqdm pdfplumber
```

---

### Wersja 1.0

```
v1/
    main.py
    transformer.py
    tokenizer.py
    dane.json
```

**Uruchomienie:**
```bash
cd v1
python main.py
```

Program automatycznie wytrenuje model i uruchomi tryb rozmowy.  
Przy kolejnych uruchomieniach wczytuje model z cache (trening pomijany).

---

### Wersja 2.0

```
v2/
    main.py
    transformer.py
    tokenizer.py
    wyszukiwarka.py
    parser.py
    dane.json
    regulamin.pdf      ← regulamin studiów PWr
```

**Pierwsze uruchomienie – generuj bazę wiedzy:**
```bash
cd v2
python parser.py
```
Tworzy plik `baza_wiedzy.json` z paragrafami regulaminu.  
Wystarczy uruchomić raz (lub gdy zmieni się PDF).

**Uruchomienie asystenta:**
```bash
python main.py
```

---

### Komendy w trybie rozmowy

| Komenda | Opis |
|---|---|
| `/temp 0.1` | zmień temperaturę (0.01 = deterministyczny, 1.0 = losowy) |
| `/historia` | pokaż historię rozmowy |
| `/zapomnij` | wyczyść pamięć modelu |
| `/pomoc` | lista komend |
| `koniec` | zakończ program |

---

##  Technologie

- **Python 3.13**
- **PyTorch** – architektura Transformer, trening GPU
- **NumPy** – operacje na wektorach
- **pdfplumber** – parsowanie PDF
- **tqdm** – pasek postępu treningu
- **Git LFS** – przechowywanie plików modelu na GitHub

---

##  Sprzęt testowy

- CPU: Intel Core i7-11700F
- GPU: NVIDIA RTX 3060 Ti 8GB
- RAM: 32GB
- System: Windows 10
