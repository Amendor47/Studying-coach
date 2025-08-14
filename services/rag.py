"""Simple retrieval-augmented generation helpers.

Uses FAISS and sentence-transformers when available; otherwise falls back to a naive paragraph splitter so the rest of the pipeline keeps working offline.
"""
from __future__ import annotations

from typing import List

try:  # optional heavy deps
    import faiss  # type: ignore
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover - graceful fallback
    faiss = None  # type: ignore
    SentenceTransformer = None  # type: ignore


class RAGIndex:
    """In-memory semantic index with optional FAISS backend."""

    def __init__(self) -> None:
        # Graceful initialization of SentenceTransformer model
        self.model = None
        if SentenceTransformer:
            try:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:  # Handle network/download errors gracefully
                self.model = None
        
        self.index = (
            faiss.IndexFlatIP(self.model.get_sentence_embedding_dimension())
            if self.model and faiss
            else None
        )
        self.passages: List[str] = []

    def build(self, text: str) -> None:
        """Segment text and build the search index."""
        self.passages = [p.strip() for p in text.splitlines() if p.strip()]
        if self.index and self.model and self.passages:
            try:
                vectors = self.model.encode(self.passages)
                # Reset index to ensure consistency
                self.index.reset()
                self.index.add(vectors)
            except Exception:
                # If encoding fails, clear the index to maintain consistency
                self.index.reset()

    def search(self, query: str, k: int = 5) -> List[str]:
        """Return top-k relevant passages for *query*."""
        if self.index and self.model and self.passages:
            q = self.model.encode([query])
            _, idx = self.index.search(q, min(k, len(self.passages)))
            # Add bounds checking to prevent IndexError
            return [self.passages[i] for i in idx[0] if 0 <= i < len(self.passages)]
        return self.passages[:k]


_default_index = RAGIndex()


def get_context(text: str, k: int = 5) -> List[str]:
    """Convenience wrapper returning contextual passages for *text*."""
    _default_index.build(text)
    return _default_index.search(text, k)
