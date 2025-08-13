"""Utility helpers for generating embeddings locally."""
from __future__ import annotations

from typing import List

try:  # optional dependency
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore


_MODEL = None


def _load_model(name: str):
    global _MODEL
    if _MODEL is None and SentenceTransformer:
        _MODEL = SentenceTransformer(name)
    return _MODEL


def local_embed(texts: List[str], settings=None) -> List[List[float]]:
    """Return embeddings using sentence-transformers if available."""
    model_name = "all-MiniLM-L6-v2"
    if settings and settings.embedding_model:
        model_name = settings.embedding_model
    model = _load_model(model_name)
    if model:
        vecs = model.encode(texts)
        return [v.tolist() for v in vecs]
    # fallback: zero vectors
    return [[0.0] * 3 for _ in texts]
