import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

from .rag import get_context

CACHE_DIR = Path("cache/llm")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = Path("logs/ai.log")
LOG_FILE.touch(exist_ok=True)

class RateLimitError(Exception):
    pass

def _log(entry: str) -> None:
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(entry + "\n")


def _hash_prompt(system: str, user: str) -> str:
    key = (system + user).encode("utf-8")
    return hashlib.sha256(key).hexdigest()


def cached_call(system: str, user: str, call_fn) -> Dict[str, Any]:
    """Call LLM with cache and simple backoff.

    Args:
        system: system prompt
        user: user prompt
        call_fn: function that actually performs the API call
    """
    key = _hash_prompt(system, user)
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        with cache_file.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    delays = [0, 1, 2, 5]
    for delay in delays:
        try:
            resp = call_fn(system, user)
            with cache_file.open("w", encoding="utf-8") as fh:
                json.dump(resp, fh)
            _log(f"cache_miss,{key},saved")
            return resp
        except RateLimitError:
            _log(f"ratelimit,{key},retry,{delay}")
            time.sleep(delay)
    raise RateLimitError("Exceeded retries")


def analyze_text(text: str, reason: str = "") -> List[Dict]:
    """Call an LLM to analyze text and return draft items.

    Falls back to an empty result if the API is unavailable. The call is
    cached and logged with a reason for transparency.
    """

    system = (
        "Tu es un coach de révision expert utilisant des méthodes pédagogiques avancées. "
        "Analyse le contenu avec expertise pédagogique et adapte ta réponse selon le contexte d'apprentissage.\n\n"
        "Principes pédagogiques à respecter:\n"
        "- Scaffolding: construis progressivement les concepts complexes\n"
        "- Active recall: crée des questions qui stimulent la récupération en mémoire\n" 
        "- Spaced repetition: varie la difficulté pour optimiser la rétention\n"
        "- Elaborative processing: aide à créer des liens avec les connaissances existantes\n\n"
        "Retourne uniquement un JSON enrichi avec les listes 'flashcards' et 'exercices', "
        "en incluant des métadonnées pédagogiques comme 'difficulty_level', 'cognitive_load', "
        "'learning_objectives', et 'pedagogical_method'."
    )
    context = "\n\n".join(get_context(text, 5))
    user = text
    if context:
        user += "\n\nContexte:\n" + context
    user += "\nStrict JSON"

    def call_fn(sys: str, usr: str) -> Dict[str, Any]:
        """Perform the actual LLM API call.

        Supports Ollama, OpenAI, and AnythingLLM servers. Provider is chosen via
        environment variables:

        - LLM_PROVIDER=ollama and OLLAMA_HOST (default: http://127.0.0.1:11434)
        - LLM_PROVIDER=anythingllm and ANYTHINGLLM_BASE (url)
        - optional ANYTHINGLLM_TOKEN for auth header
        """
        provider = os.getenv("LLM_PROVIDER", "openai").lower()

        # --- Ollama provider ---
        if provider == "ollama":
            import requests

            host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
            model = os.getenv("OLLAMA_MODEL", "llama3:8b")
            messages = [
                {"role": "system", "content": sys},
                {"role": "user", "content": usr},
            ]
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            try:
                r = requests.post(
                    f"{host.rstrip('/')}/api/chat",
                    json=payload,
                    timeout=int(os.getenv("OLLAMA_TIMEOUT", "60")),
                )
                r.raise_for_status()
                data = r.json()
                content = data.get("message", {}).get("content", "{}")
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # If response is not JSON, return empty structure
                    return {"flashcards": [], "exercices": []}
            except Exception as e:
                _log(f"ollama_error,{str(e)}")
                return {"flashcards": [], "exercices": []}

        # --- AnythingLLM provider ---
        if provider == "anythingllm" or os.getenv("ANYTHINGLLM_BASE"):
            import requests

            base = os.getenv("ANYTHINGLLM_BASE", "http://localhost:3001")
            model = os.getenv("ANYTHINGLLM_MODEL", "gpt-3.5-turbo")
            token = os.getenv("ANYTHINGLLM_TOKEN")
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": sys},
                    {"role": "user", "content": usr},
                ],
                "temperature": 0,
            }
            try:
                r = requests.post(
                    f"{base.rstrip('/')}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=30,
                )
                r.raise_for_status()
                data = r.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                return json.loads(content)
            except Exception:
                return {"flashcards": [], "exercices": []}

        # --- OpenAI provider (default) ---
        try:
            from openai import OpenAI  # type: ignore
            from openai.error import OpenAIError, RateLimitError as _RateLimit
        except Exception:
            # OpenAI package not installed
            return {"flashcards": [], "exercices": []}

        key = os.getenv("OPENAI_API_KEY")
        if not key:
            return {"flashcards": [], "exercices": []}

        client = OpenAI(api_key=key)
        try:
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": sys},
                    {"role": "user", "content": usr},
                ],
                temperature=0,
            )
        except _RateLimit as err:  # surface rate limits to cached_call
            raise RateLimitError(str(err))
        except OpenAIError:
            return {"flashcards": [], "exercices": []}

        try:
            return json.loads(resp.choices[0].message.content)
        except Exception:
            return {"flashcards": [], "exercices": []}

    data = cached_call(system, user, call_fn)
    _log(f"ai_analyze,{reason},{len(text)}")
    items: List[Dict] = []
    for fc in data.get("flashcards", []):
        items.append({"id": f"ai{len(items)}", "kind": "card", "payload": fc})
    for ex in data.get("exercices", []):
        items.append({"id": f"ai{len(items)}", "kind": "exercise", "payload": ex})
    return items
