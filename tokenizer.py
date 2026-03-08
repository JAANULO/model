# ============================================================
#  TOKENIZER – zamienia słowa na liczby i z powrotem
#
#  Dlaczego potrzebujemy tokenizera?
#  Sieć neuronowa nie rozumie słów – rozumie LICZBY.
#  Tokenizer to "słownik" między językiem a matematyką.
#
#  Przykład:
#    "warszawa jest stolicą" → [4, 2, 3]
#    [4, 2, 3]               → "warszawa jest stolicą"
# ============================================================

class Tokenizer:
    def __init__(self):
        self.slowo_na_id = {}   # "kot" → 5
        self.id_na_slowo = {}   # 5 → "kot"
        self.rozmiar = 0

        # Specjalne tokeny
        self.PAD = 0   # padding – wypełnienie do równej długości
        self.UNK = 1   # unknown – nieznane słowo

        self.slowo_na_id["<PAD>"] = self.PAD
        self.slowo_na_id["<UNK>"] = self.UNK
        self.id_na_slowo[self.PAD] = "<PAD>"
        self.id_na_slowo[self.UNK] = "<UNK>"
        self.rozmiar = 2

    def buduj_slownik(self, zdania):
        """
        Przechodzi przez wszystkie zdania i buduje słownik.
        Każde nowe słowo dostaje unikalny numer (ID).
        """
        for zdanie in zdania:
            for slowo in zdanie.lower().split():
                if slowo not in self.slowo_na_id:
                    self.slowo_na_id[slowo] = self.rozmiar
                    self.id_na_slowo[self.rozmiar] = slowo
                    self.rozmiar += 1

        print(f"  📖 Słownik: {self.rozmiar} unikalnych tokenów")

    def koduj(self, tekst):
        """
        Zamienia tekst na listę numerów (ID).
        Nieznane słowa → ID 1 (UNK)
        """
        tokeny = tekst.lower().split()
        return [self.slowo_na_id.get(t, self.UNK) for t in tokeny]

    def dekoduj(self, ids):
        """
        Zamienia listę numerów z powrotem na tekst.
        """
        slowa = [self.id_na_slowo.get(i, "<UNK>") for i in ids]
        return " ".join(slowa)