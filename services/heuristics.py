from typing import List, Dict

from .validate import words_per_sentence

MIN_ITEMS = 8
MAX_TEXT_LEN = 1500
DENSITY_THRESHOLD = 0.3  # items per 100 words


def readability(text: str) -> float:
    """Return a crude readability score (0-1)."""
    lengths = words_per_sentence(text)
    if not lengths:
        return 1.0
    avg = sum(lengths) / len(lengths)
    score = min(1.0, 18 / avg)
    return score


def density(text: str, items: List[Dict]) -> float:
    words = len(text.split())
    if words == 0:
        return 0.0
    return len(items) / (words / 100)


def ai_needed(text: str, items: List[Dict]) -> bool:
    if len(text) > MAX_TEXT_LEN:
        return True
    if (
        len(items) >= MIN_ITEMS
        and density(text, items) >= DENSITY_THRESHOLD
        and readability(text) >= 0.65
    ):
        return False
    return True