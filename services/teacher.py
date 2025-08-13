from __future__ import annotations
from pathlib import Path
from typing import Optional

try:
    from gpt4all import GPT4All  # optional local LLM
except Exception:  # pragma: no cover - missing optional dep
    GPT4All = None  # type: ignore

MODEL_DIR = Path("models")
DEFAULT_MODEL = "gpt4all-falcon-q4_0.gguf"

class LocalTeacher:
    """Simple wrapper around a local GPT4All model.

    The model is optional; if the binary or dependency is missing, the
    chat method returns a friendly message instead of failing.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.model: Optional[GPT4All] = None
        if GPT4All is None:
            return
        path = MODEL_DIR / model_name
        if path.exists():
            try:
                self.model = GPT4All(path.as_posix())
            except Exception:
                self.model = None

    def chat(self, prompt: str) -> str:
        if not self.model:
            return "Modèle local indisponible."
        with self.model.chat_session():
            try:
                return self.model.generate(prompt, max_tokens=256).strip()
            except Exception:
                return "Erreur dans le modèle local." 
