# ============================================================
#  TRANSFORMER – mini-GPT w PyTorch z obsługą CUDA
# ============================================================

import torch
import torch.nn as nn
import numpy as np

URZADZENIE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def softmax(x, os=-1):
    """Zostawiamy dla kompatybilności z main.py"""
    x = x - np.max(x, axis=os, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=os, keepdims=True)


class MiniGPT(nn.Module):
    """
    Mini-GPT w PyTorch z Multi-Head Attention, Dropout, LayerNorm.
    PyTorch sam oblicza gradienty – nie piszemy backward() ręcznie!
    """

    def __init__(self, rozmiar_slownika, wymiar=128, n_warstw=4,
                 n_glowic=4, dropout=0.1, maks_dlugosc=64):
        super().__init__()

        self.wymiar       = wymiar
        self.maks_dlugosc = maks_dlugosc

        # Embedding słów i pozycji
        self.embedding     = nn.Embedding(rozmiar_slownika, wymiar)
        self.pos_embedding = nn.Embedding(maks_dlugosc, wymiar)
        self.dropout_wej   = nn.Dropout(dropout)

        # Bloki Transformera (Multi-Head Attention + FF + LN)
        warstwa = nn.TransformerEncoderLayer(
            d_model        = wymiar,
            nhead          = n_glowic,
            dim_feedforward= wymiar * 4,
            dropout        = dropout,
            activation     = "relu",
            batch_first    = True,
            norm_first     = True,
        )
        self.transformer = nn.TransformerEncoder(
            warstwa,
            num_layers          = n_warstw,
            enable_nested_tensor= False,   # ← usuwa ostrzeżenie
        )

        # Warstwa wyjściowa
        self.glowa        = nn.Linear(wymiar, rozmiar_slownika, bias=False)
        self.glowa.weight = self.embedding.weight  # weight tying

        # Inicjalizacja
        nn.init.normal_(self.embedding.weight,     std=0.02)
        nn.init.normal_(self.pos_embedding.weight, std=0.02)

        total = sum(p.numel() for p in self.parameters())
        print(f"  🔢 Parametry modelu: {total:,}")
        print(f"  💻 Urządzenie: {URZADZENIE}")

    def _maska(self, T):
        return torch.triu(torch.ones(T, T, device=URZADZENIE), diagonal=1).bool()

    def forward(self, ids):
        if isinstance(ids, (list, np.ndarray)):
            ids = torch.tensor(ids, dtype=torch.long, device=URZADZENIE)
        else:
            ids = ids.to(URZADZENIE)

        T   = ids.shape[0]
        poz = torch.arange(T, device=URZADZENIE)

        x = self.embedding(ids) + self.pos_embedding(poz)
        x = self.dropout_wej(x)
        x = x.unsqueeze(0)
        x = self.transformer(x, mask=self._maska(T), is_causal=True)
        x = x.squeeze(0)
        return self.glowa(x)

    def ustaw_trening(self, trening=True):
        self.train() if trening else self.eval()


class Adam:
    """Wrapper na PyTorch AdamW"""
    def __init__(self, lr=0.003, parametry=None):
        self._opt = torch.optim.AdamW(parametry, lr=lr, weight_decay=0.01)

    def krok(self, _=None):
        self._opt.step()

    def zeruj_gradienty(self):
        self._opt.zero_grad()