
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

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
        "Tu es un coach de révision FR. Retourne uniquement un JSON avec les"
        " listes 'flashcards' et 'exercices'."
    )
    user = text + "\nStrict JSON"

    def call_fn(sys: str, usr: str) -> Dict[str, Any]:
        try:
            from openai import OpenAI  # type: ignore
        except Exception:
            return {"flashcards": [], "exercices": []}

        key = os.getenv("OPENAI_API_KEY")
        if not key:
            return {"flashcards": [], "exercices": []}
        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": sys}, {"role": "user", "content": usr}],
            temperature=0,
        )
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
