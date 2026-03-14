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
            for slowo in zdanie.lower():

                if slowo not in self.slowo_na_id:
                    self.slowo_na_id[slowo] = self.rozmiar
                    self.id_na_slowo[self.rozmiar] = slowo
                    self.rozmiar += 1

        print(f"  📖 Słownik: {self.rozmiar} unikalnych tokenów")

    def koduj(self, tekst):
        return [self.slowo_na_id.get(z, self.UNK) for z in tekst.lower()]

    def dekoduj(self, ids):
        znaki = [self.id_na_slowo.get(i, "?") for i in ids]
        return "".join(znaki)