import re
import unicodedata
from typing import List

MAX_WORDS = 1500
OVERLAP_RATIO = 0.3

def normalize_text(text: str) -> str:
    """Normalize Unicode and collapse whitespace."""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def chunk_text(text: str, max_words: int = MAX_WORDS, overlap: float = OVERLAP_RATIO) -> List[str]:
    """Split text into overlapping word chunks.

    Args:
        text: The raw text to segment.
        max_words: Maximum number of words per chunk.
        overlap: Fraction of overlap between consecutive chunks.
    """
    words = normalize_text(text).split()
    if not words:
        return []

    step = int(max_words * (1 - overlap)) or 1
    chunks = []
    for start in range(0, len(words), step):
        end = start + max_words
        chunk_words = words[start:end]
        if not chunk_words:
            continue
        chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
    return chunks