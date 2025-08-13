import pytest
from services.scheduler import interleave_by_theme


def test_interleave_by_theme_round_robin():
    cards = [
        {"id": 1, "theme": "A"},
        {"id": 2, "theme": "A"},
        {"id": 3, "theme": "B"},
        {"id": 4, "theme": "B"},
        {"id": 5, "theme": "B"},
    ]
    ordered = interleave_by_theme(cards)
    themes = [c["theme"] for c in ordered]
    assert themes == ["A", "B", "A", "B", "B"]
    assert len(ordered) == len(cards)
