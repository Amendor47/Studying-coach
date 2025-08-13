"""Simple health monitoring utilities.

These helpers provide lightweight checks to ensure external services such as
local LLM backends or internet connectivity remain available. They can be
scheduled periodically by a cron job or background thread to log potential
outages that could degrade the user experience.
"""
from __future__ import annotations

import logging
from typing import Dict

import requests


def check_llm(base_url: str = "http://127.0.0.1:5000/api/health/llm", timeout: int = 5) -> bool:
    """Return True if the LLM health endpoint responds.

    Any exception is caught and logged at WARNING level so the caller can decide
    how to react (retry, fallback to offline mode, etc.).
    """
    try:
        r = requests.get(base_url, timeout=timeout)
        r.raise_for_status()
        data: Dict = r.json()
        logging.info("LLM health: %s", data)
        return bool(data.get("ok"))
    except Exception as exc:  # pragma: no cover - network failures are logged
        logging.warning("LLM health check failed: %s", exc)
        return False


def check_web(query: str = "ping", timeout: int = 5) -> bool:
    """Perform a tiny DuckDuckGo request to ensure the network is up.

    The function returns True on success and False otherwise. It never raises to
    avoid crashing the caller when offline.
    """
    try:
        r = requests.get("https://duckduckgo.com/html/", params={"q": query}, timeout=timeout)
        return r.status_code == 200
    except Exception as exc:  # pragma: no cover
        logging.warning("web connectivity check failed: %s", exc)
        return False
