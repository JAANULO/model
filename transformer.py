# ============================================================
#  TRANSFORMER – mini-GPT w PyTorch
#  Prosta architektura GPT bez TransformerEncoder
# ============================================================

import torch
import torch.nn as nn
import numpy as np

URZADZENIE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def softmax(x, os=-1):
    x = x - np.max(x, axis=os, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=os, keepdims=True)


# ────────────────────────────────────────────────────────────
# Jeden blok Transformera
# ────────────────────────────────────────────────────────────

class GPTBlok(nn.Module):
    def __init__(self, wymiar, n_glowic, dropout):
        super().__init__()
        self.ln1  = nn.LayerNorm(wymiar)
        self.ln2  = nn.LayerNorm(wymiar)
        self.attn = nn.MultiheadAttention(
            embed_dim   = wymiar,
            num_heads   = n_glowic,
            dropout     = dropout,
            batch_first = True,
        )
        self.ff = nn.Sequential(
            nn.Linear(wymiar, wymiar * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(wymiar * 4, wymiar),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        T = x.shape[1]
        # Maska causalna
        maska = torch.triu(
            torch.ones(T, T, device=x.device), diagonal=1
        ).bool()

        # Self-Attention z residual
        x2 = self.ln1(x)
        x2, _ = self.attn(x2, x2, x2, attn_mask=maska, is_causal=True)
        x = x + x2

        # Feed-Forward z residual
        x = x + self.ff(self.ln2(x))
        return x


# ────────────────────────────────────────────────────────────
# Główny model
# ────────────────────────────────────────────────────────────

class MiniGPT(nn.Module):
    def __init__(self, rozmiar_slownika, wymiar=128, n_warstw=4,
                 n_glowic=4, dropout=0.1, maks_dlugosc=256):
        super().__init__()
        self.wymiar       = wymiar
        self.maks_dlugosc = maks_dlugosc

        self.tok_emb = nn.Embedding(rozmiar_slownika, wymiar)
        self.pos_emb = nn.Embedding(maks_dlugosc, wymiar)
        self.drop    = nn.Dropout(dropout)
        self.bloki   = nn.Sequential(
            *[GPTBlok(wymiar, n_glowic, dropout) for _ in range(n_warstw)]
        )
        self.ln_f    = nn.LayerNorm(wymiar)
        self.glowa   = nn.Linear(wymiar, rozmiar_slownika, bias=False)

        # Inicjalizacja wag
        self.apply(self._init_wagi)

        self.glowa.weight = self.tok_emb.weight  # weight tying

        total = sum(p.numel() for p in self.parameters())
        print(f"  🔢 Parametry modelu: {total:,}")
        print(f"  💻 Urządzenie: {URZADZENIE}")

    def _init_wagi(self, modul):
        if isinstance(modul, nn.Linear):
            nn.init.normal_(modul.weight, mean=0.0, std=0.02)
            if modul.bias is not None:
                nn.init.zeros_(modul.bias)
        elif isinstance(modul, nn.Embedding):
            nn.init.normal_(modul.weight, mean=0.0, std=0.02)

    def forward(self, ids):
        if isinstance(ids, (list, np.ndarray)):
            ids = torch.tensor(ids, dtype=torch.long, device=URZADZENIE)
        else:
            ids = ids.to(URZADZENIE)

        tryb_batch = ids.dim() == 2

        if tryb_batch:
            B, T = ids.shape
            T = min(T, self.maks_dlugosc)
            ids = ids[:, :T]
        else:
            T = min(ids.shape[0], self.maks_dlugosc)
            ids = ids[:T]
            ids = ids.unsqueeze(0)

        poz = torch.arange(T, device=URZADZENIE)
        x = self.drop(self.tok_emb(ids) + self.pos_emb(poz))
        x = self.bloki(x)
        x = self.ln_f(x)
        logits = self.glowa(x)

        if not tryb_batch:
            logits = logits.squeeze(0)

        return logits

    def ustaw_trening(self, trening=True):
        self.train() if trening else self.eval()


class Adam:
    def __init__(self, lr=0.001, parametry=None):
        self._opt = torch.optim.AdamW(
            parametry, lr=lr, weight_decay=0.01,
            betas=(0.9, 0.95)
        )

    def krok(self, _=None):
        self._opt.step()

    def zeruj_gradienty(self):
        self._opt.zero_grad(set_to_none=True)