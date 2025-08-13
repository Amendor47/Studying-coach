from datetime import date, timedelta
from collections import defaultdict
from typing import Dict, List

REVIEW_OFFSETS = (0, 2, 5)


def group_by_theme_level(drafts: List[Dict]) -> Dict[str, Dict[str, List[Dict]]]:
    """Group drafts by theme and difficulty level."""
    grouped: Dict[str, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))
    for d in drafts:
        payload = d.get("payload", {})
        theme = payload.get("theme", "Général")
        level = str(payload.get("level", "1"))
        grouped[theme][level].append(d)
    return grouped


def generate_plan(drafts: List[Dict], start: date | None = None, cycle_days: int = 7) -> List[Dict]:
    """Create a simple spaced-repetition study plan.

    Each draft is scheduled on a study day and reviewed later using
    REVIEW_OFFSETS. Returns a list of entries sorted by date with fields
    {id, date, theme, level, review?}.
    """
    if start is None:
        start = date.today()
    schedule: List[Dict] = []
    grouped = group_by_theme_level(drafts)
    idx = 0
    for theme in grouped:
        for level in sorted(grouped[theme], key=lambda x: int(x)):
            for d in grouped[theme][level]:
                base_day = start + timedelta(days=idx % cycle_days)
                for off in REVIEW_OFFSETS:
                    entry = {
                        "id": d.get("id"),
                        "date": (base_day + timedelta(days=off)).isoformat(),
                        "theme": theme,
                        "level": level,
                        "review": off != 0,
                    }
                    schedule.append(entry)
                idx += 1
    schedule.sort(key=lambda e: e["date"])
    return schedule
