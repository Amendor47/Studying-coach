"""Scheduling utilities for spaced repetition."""

from datetime import date, timedelta
from typing import Any, Dict, List

from .store import load_db, save_db

# Effective-factor bounds for SM-2
EF_MIN = 1.3
EF_MAX = 2.8


def interleave_by_theme(cards: List[Dict]) -> List[Dict]:
    """Round-robin shuffle of cards grouped by theme.

    This prevents long runs of cards from the same theme and implements a
    simple form of interleaving recommended in the spec. The function expects
    each card to expose a ``theme`` field; cards missing one are grouped under
    ``"General"``.
    """

    buckets: Dict[str, List[Dict]] = {}
    for card in cards:
        theme = card.get("theme", "General")
        buckets.setdefault(theme, []).append(card)

    ordered: List[Dict] = []
    # iterate in round-robin fashion until all buckets are exhausted
    while any(buckets.values()):
        for theme in list(buckets.keys()):
            if buckets[theme]:
                ordered.append(buckets[theme].pop(0))
    return ordered


def due_cards(db: Dict[str, Any] | None = None) -> List[Dict]:
    """Return due cards interleaved by theme."""
    if db is None:
        db = load_db()
    today = date.today().isoformat()
    cards = [c for c in db.get("cards", []) if c.get("srs", {}).get("due", today) <= today]
    return interleave_by_theme(cards)


def update_srs(card: Dict, quality: int) -> None:
    """Update a card's SM-2 scheduling fields based on review quality (0-5)."""
    srs = card.setdefault("srs", {"EF": 2.5, "interval": 1, "reps": 0, "due": date.today().isoformat()})
    ef = srs.get("EF", 2.5)
    reps = srs.get("reps", 0)
    if quality < 3:
        reps = 0
        interval = 1
    else:
        reps += 1
        if reps == 1:
            interval = 1
        elif reps == 2:
            interval = 6
        else:
            interval = round(srs.get("interval", 1) * ef)
        ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        ef = max(EF_MIN, min(EF_MAX, ef))
    srs.update({"EF": ef, "interval": interval, "reps": reps, "due": (date.today() + timedelta(days=interval)).isoformat()})


def build_exercises_from_cards(cards: List[Dict]) -> List[Dict]:
    """Create simple recall exercises from cards."""
    exercises: List[Dict] = []
    for c in cards:
        exercises.append({"type": "RC", "q": c.get("front"), "answer": c.get("back")})
    return exercises


def save_progress(db: Dict[str, Any]) -> None:
    """Persist database after scheduling updates."""
    save_db(db)
