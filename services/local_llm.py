"""Minimal local LLM wrapper using llama-cpp.

Allows the coach to run completely offline by loading a GGUF model
specified via the LOCAL_LLM_MODEL environment variable. If the optional
``llama_cpp`` dependency or the model file is unavailable, calls fall
back to empty results so the rest of the pipeline can continue.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Dict, Optional

try:  # optional heavy dependency
    from llama_cpp import Llama  # type: ignore
except Exception:  # pragma: no cover - graceful fallback
    Llama = None  # type: ignore


@lru_cache(maxsize=1)
def _load_model() -> Optional[Llama]:
    path = os.getenv("LOCAL_LLM_MODEL")
    if not path or not Llama:
        return None
    try:
        return Llama(model_path=path, n_ctx=2048)
    except Exception:  # pragma: no cover - failure to load model
        return None


def complete(system: str, user: str) -> Dict[str, dict]:
    """Return JSON dict from a locally hosted model."""

    llm = _load_model()
    if not llm:
        return {"flashcards": [], "exercices": []}
    prompt = f"<s>[INST]<<SYS>>{system}<</SYS>>{user}[/INST]"
    try:
        out = llm(prompt, max_tokens=512, temperature=0)
        txt = out["choices"][0]["text"]
        return json.loads(txt.strip())
    except Exception:  # pragma: no cover - model may return bad JSON
        return {"flashcards": [], "exercices": []}
