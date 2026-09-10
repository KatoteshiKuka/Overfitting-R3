"""Calcolo e verifica del codice fiscale italiano.

Implementa l'algoritmo vero, non un generatore di sedici caratteri a caso: i profili
sintetici devono essere formalmente validi, altrimenti qualunque validatore incontrato
poi (form, import, controlli lato ospedale) li rifiuterebbe e la demo cadrebbe lì.

`checksum` è scritto in modo indipendente da `encode`, così il test che verifica il
carattere di controllo non finisce per ricontrollare la stessa riga di codice.
"""

from __future__ import annotations

import unicodedata
from datetime import date

VOWELS = "AEIOU"

# Lettera del mese, secondo la tabella ufficiale.
MONTH_LETTERS = "ABCDEHLMPRST"

# Valori dei caratteri in posizione dispari (1ª, 3ª, ...), contando da 1.
ODD_VALUES: dict[str, int] = {
    "0": 1, "1": 0, "2": 5, "3": 7, "4": 9, "5": 13, "6": 15, "7": 17, "8": 19, "9": 21,
    "A": 1, "B": 0, "C": 5, "D": 7, "E": 9, "F": 13, "G": 15, "H": 17, "I": 19, "J": 21,
    "K": 2, "L": 4, "M": 18, "N": 20, "O": 11, "P": 3, "Q": 6, "R": 8, "S": 12, "T": 14,
    "U": 16, "V": 10, "W": 22, "X": 25, "Y": 24, "Z": 23,
}  # fmt: skip

# In posizione pari il valore è la posizione nell'alfabeto (o la cifra stessa).
EVEN_VALUES: dict[str, int] = {str(d): d for d in range(10)} | {
    chr(ord("A") + i): i for i in range(26)
}

CHECK_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def normalize(value: str) -> str:
    """Toglie accenti e caratteri non alfabetici: `D'Amico` → `DAMICO`."""
    decomposed = unicodedata.normalize("NFKD", value)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return "".join(c for c in stripped.upper() if c.isalpha())


def surname_code(surname: str) -> str:
    letters = normalize(surname)
    consonants = [c for c in letters if c not in VOWELS]
    vowels = [c for c in letters if c in VOWELS]
    code = "".join(consonants + vowels)[:3]
    return code.ljust(3, "X")


def name_code(name: str) -> str:
    """Con quattro o più consonanti si prendono la prima, la terza e la quarta."""
    letters = normalize(name)
    consonants = [c for c in letters if c not in VOWELS]
    vowels = [c for c in letters if c in VOWELS]
    if len(consonants) >= 4:
        chosen = [consonants[0], consonants[2], consonants[3]]
    else:
        chosen = consonants + vowels
    return "".join(chosen)[:3].ljust(3, "X")


def birth_code(birth: date, gender: str) -> str:
    """Anno, mese, giorno. Alle donne si sommano 40 al giorno."""
    day = birth.day + (40 if gender.upper() == "F" else 0)
    return f"{birth.year % 100:02d}{MONTH_LETTERS[birth.month - 1]}{day:02d}"


def checksum(partial: str) -> str:
    """Carattere di controllo dai primi quindici caratteri.

    Scritto a partire dalla definizione (posizioni dispari e pari contate da 1) e non
    riusando `encode`, così i test lo verificano davvero in modo indipendente.
    """
    if len(partial) != 15:
        raise ValueError("Il carattere di controllo si calcola su 15 caratteri.")

    total = 0
    for index, char in enumerate(partial.upper(), start=1):
        table = ODD_VALUES if index % 2 == 1 else EVEN_VALUES
        if char not in table:
            raise ValueError(f"Carattere non ammesso nel codice fiscale: {char!r}")
        total += table[char]
    return CHECK_LETTERS[total % 26]


def encode(
    surname: str, name: str, birth: date, gender: str, birthplace_code: str
) -> str:
    """Codice fiscale completo. `birthplace_code` è il codice catastale del comune."""
    place = birthplace_code.upper()
    if len(place) != 4 or not place[0].isalpha() or not place[1:].isdigit():
        raise ValueError(f"Codice catastale non valido: {birthplace_code!r}")

    partial = f"{surname_code(surname)}{name_code(name)}{birth_code(birth, gender)}{place}"
    return f"{partial}{checksum(partial)}"


def is_valid(code: str) -> bool:
    """Verifica formale: lunghezza, alfabeto e carattere di controllo."""
    value = (code or "").strip().upper()
    if len(value) != 16 or not value.isalnum():
        return False
    try:
        return checksum(value[:15]) == value[15]
    except ValueError:
        return False
