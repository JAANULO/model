# 🧠 Architektura i Matematyka Projektu

Dokument ten opisuje, jak system działa "pod maską". Przedstawia algorytmy i wzory matematyczne użyte w projekcie, które zostały zaimplementowane od zera, bez użycia gotowych bibliotek z gotowymi modelami (takich jak `scikit-learn` czy `transformers`).

Projekt dzieli się na dwa główne filary: **System Wyszukiwania (RAG)** oraz **Model Generatywny (Mini-GPT)**.

---

## 1. System Wyszukiwania (Asystent Regulaminowy v2)

Celem systemu jest znalezienie jednego, najbardziej trafnego paragrafu regulaminu na podstawie pytania użytkownika. 

### A. Korekta literówek – Odległość Levenshteina
Używamy algorytmu programowania dynamicznego do obliczenia minimalnej liczby operacji (wstawienie, usunięcie, zamiana) potrzebnych do przekształcenia jednego słowa w drugie. W kodzie dopuszczamy maksymalnie **1 błąd edycyjny**.

### B. Wektoryzacja tekstu – Algorytm BM25
W przeciwieństwie do klasycznego TF-IDF, zaimplementowano **BM25 (Best Match 25)**. Radzi on sobie ze zjawiskiem "przesycenia" słowami oraz z różną długością paragrafów.

**1. IDF (Odwrotna Częstotliwość Dokumentowa) w wersji Robertsona:**
W kodzie użyto wygładzonej wersji logarytmu, aby uniknąć wartości ujemnych dla bardzo popularnych słów:

$$
\text{IDF}(q_i) = \ln\left(\frac{N - df(q_i) + 0.5}{df(q_i) + 0.5} + 1\right)
$$

Gdzie:
*   $N$: Całkowita liczba dokumentów (paragrafów).
*   $df(q_i)$: Liczba dokumentów zawierających słowo $q_i$.

**2. Główny wzór BM25:**

$$
\text{BM25}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{\text{TF}(q_i, D) \cdot (k_1 + 1)}{\text{TF}(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}
$$

Gdzie:
*   $\text{TF}(q_i, D)$: Częstotliwość słowa w danym paragrafie znormalizowana przez jego długość.
*   $|D|$: Długość obecnego paragrafu (liczba słów).
*   $\text{avgdl}$: Średnia długość paragrafu w całej bazie.
*   $k_1 = 1.5$: Współczynnik nasycenia.
*   $b = 0.75$: Normalizacja długości (karanie długich tekstów).

### C. Ranking wyników – Podobieństwo Cosinusowe
Zamiast liczyć euklidesową odległość punktów, liczymy **kąt pomiędzy wektorami** (Podobieństwo Cosinusowe). System skupia się na proporcji użytych słów, ignorując bezwzględną wielkość wektora.

$$
\text{Cosinus}(\theta) = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \times \|\mathbf{B}\|} = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \sqrt{\sum_{i=1}^{n} B_i^2}}
$$

*   Wynik bliski **1.0** = wektory wskazują ten sam kierunek (idealne dopasowanie). Próg odcięcia w aplikacji to **0.05**.

---

## 2. Model Generatywny (Mini-GPT v1)

Mini-GPT to głęboka sieć neuronowa zbudowana w oparciu o architekturę Transformera, uczona przewidywania następnego tokenu (znaku) na podstawie historii.

### A. Mechanizm Samouwagi (Multi-Head Attention)
Pozwala sieci ocenić, które znaki w zdaniu są najważniejsze dla zrozumienia obecnego kontekstu.

$$
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
$$

*   **$Q$ (Query), $K$ (Key), $V$ (Value)**: Macierze zapytań, kluczy i wartości.
*   **$\sqrt{d_k}$**: Czynnik skalujący. Zapobiega eksplozji gradientów (zbyt dużym liczbom psującym sieć).
*   **Maska Causalna**: Górny trójkąt macierzy $QK^T$ jest zerowany (wartość $-\infty$), co uniemożliwia modelowi "patrzenie w przyszłość" podczas treningu.

### B. Normalizacja i Aktywacja (LayerNorm & GELU)
Wewnątrz bloków Transformera użyto najnowocześniejszych technik stabilizujących sieć:

**1. Layer Normalization (Normalizacja Warstwy):**
Wyrównuje rozkład aktywacji wewnątrz sieci:

$$
y = \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}} \cdot \gamma + \beta
$$

**2. GELU (Gaussian Error Linear Unit):**
Zamiast prostej aktywacji ReLU (odcinającej wartości ujemne), użyto nieliniowej funkcji GELU (stosowanej m.in. w modelach BERT i GPT-3):

$$
\text{GELU}(x) = x \cdot \Phi(x)
$$
*(gdzie $\Phi(x)$ to dystrybuanta standardowego rozkładu normalnego).*

### C. Funkcja Straty (Cross-Entropy Loss)
Model trenowany jest z wykorzystaniem funkcji straty krzyżowej entropii (Cross-Entropy Loss). Karze ona model tym mocniej, im bardziej był "pewny" błędnej odpowiedzi.

$$
\mathcal{L} = -\sum_{i} y_i \log(\hat{y}_i)
$$

Gdzie $y_i$ to wektor oczekiwany (Prawda), a $\hat{y}_i$ to prawdopodobieństwo wygenerowane przez model.

### D. Generowanie tekstu (Softmax i Temperatura)
Ostatnia warstwa sieci (w której zastosowano *Weight Tying* w celu redukcji parametrów) zwraca surowe liczby (Logits). Przekształcamy je na ostateczne prawdopodobieństwa używając funkcji Softmax z parametrem Temperatury ($T$).

$$
P(x_i) = \frac{e^{x_i / T}}{\sum_{j} e^{x_j / T}}
$$

*   **$T < 1.0$ (np. 0.1)**: Model staje się sztywny i deterministyczny. Zastosowano to w kodzie produkcyjnym dla najwyższej dokładności przy cytowaniu prawa.
*   **$T = 1.0$**: Naturalne prawdopodobieństwa modelu.