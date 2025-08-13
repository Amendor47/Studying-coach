"""Simple retrieval-augmented generation helpers.

Uses FAISS and sentence-transformers when available; otherwise falls back to a naive paragraph splitter so the rest of the pipeline keeps working offline.
"""
from __future__ import annotations

import os
import warnings
from typing import List

try:  # optional heavy deps
    import faiss  # type: ignore
    from sentence_transformers import SentenceTransformer  # type: ignore
    
    # Suppress unnecessary warnings about local model files
    warnings.filterwarnings('ignore', category=UserWarning, module='sentence_transformers')
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'  # Avoid warnings about tokenizer parallelism
    
except Exception:  # pragma: no cover - graceful fallback
    faiss = None  # type: ignore
    SentenceTransformer = None  # type: ignore

# Global model instance to avoid reloading
_global_model = None
_model_load_attempted = False


def _get_shared_model():
    """Get shared sentence transformer model, loading only once."""
    global _global_model, _model_load_attempted
    
    if _model_load_attempted:
        return _global_model
    
    _model_load_attempted = True
    
    if not SentenceTransformer:
        return None
        
    try:
        # Try to load model locally first
        _global_model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
    except Exception:
        try:
            # If local loading fails and we have internet, try downloading
            _global_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            # If all else fails, continue without model
            _global_model = None
    
    return _global_model


class RAGIndex:
    """In-memory semantic index with optional FAISS backend."""

    def __init__(self) -> None:
        self.model = _get_shared_model()
        self.index = None
        self.passages: List[str] = []
        
        # Initialize FAISS index if model is available
        if self.model and faiss:
            try:
                self.index = faiss.IndexFlatIP(self.model.get_sentence_embedding_dimension())
            except Exception:
                self.index = None

    def build(self, text: str) -> None:
        """Segment text and build the search index."""
        self.passages = [p.strip() for p in text.splitlines() if p.strip()]
        if self.index and self.model and self.passages:
            vectors = self.model.encode(self.passages)
            self.index.add(vectors)

    def search(self, query: str, k: int = 5) -> List[str]:
        """Return top-k relevant passages for *query*."""
        if self.index and self.model and self.passages:
            q = self.model.encode([query])
            _, idx = self.index.search(q, min(k, len(self.passages)))
            return [self.passages[i] for i in idx[0]]
        return self.passages[:k]


_default_index = RAGIndex()


def get_context(text: str, k: int = 5) -> List[str]:
    """Convenience wrapper returning contextual passages for *text*."""
    _default_index.build(text)
    return _default_index.search(text, k)
