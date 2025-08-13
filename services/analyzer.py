"""Offline text analysis utilities.

The goal of the offline analyzer is to extract meaningful concepts from a raw
course text without relying on an external AI service. It identifies headings to
infer thèmes and simple "terme – définition" pairs to build draft cards and exercises.
The heuristics are lightweight but provide a solid baseline when network access
or an API key is unavailable.
"""

from __future__ import annotations

import random
import re
from collections import Counter
from typing import Dict, List, Tuple

from .validate import MAX_VERSO_CHARS, validate_items

# very small stopword list for keyword extraction
STOPWORDS = {
    "les",
    "des",
    "une",
    "dans",
    "est",
    "pour",
    "avec",
    "sur",
    "par",
    "que",
    "qui",
    "plus",
    "moins",
}


def _sections(text: str) -> List[Tuple[str, str]]:
    """Split the raw text into (theme, paragraph) tuples."""

    theme = "Général"
    buff: List[str] = []
    sections: List[Tuple[str, str]] = []
    for line in text.splitlines():
        m = re.match(r"^(?:#+|\d+\.)\s*(.+)$", line.strip())
        if m:
            if buff:
                sections.append((theme, "\n".join(buff).strip()))
                buff = []
            theme = m.group(1).strip()
        else:
            buff.append(line)
    if buff:
        sections.append((theme, "\n".join(buff).strip()))
    # further split into paragraphs
    final: List[Tuple[str, str]] = []
    for th, blk in sections:
        for para in re.split(r"\n\s*\n", blk):
            p = para.strip()
            if p:
                final.append((th, p))
    return final


def _keywords(text: str, top: int = 3) -> List[str]:
    words = [w.lower() for w in re.findall(r"\b\w{4,}\b", text)]
    words = [w for w in words if w not in STOPWORDS]
    if not words:
        return []
    freq = Counter(words)
    return [w for w, _ in freq.most_common(top)]


def _extract_pairs(text: str) -> List[Tuple[str, str, str]]:
    """Return list of (theme, term, definition) triples."""

    pairs: List[Tuple[str, str, str]] = []
    for theme, para in _sections(text):
        lines = [l.strip() for l in para.splitlines() if l.strip()]
        for line in lines:
            m = re.match(r"(.+?)[\s]*[:\-][\s]*(.+)", line)
            if not m:
                m = re.match(r"(.+?)\s+est\s+(.+)", line, re.IGNORECASE)
            if m:
                term, definition = m.groups()
                pairs.append((theme, term.strip(), definition.strip()))
    return pairs


def _build_drafts(pairs: List[Tuple[str, str, str]]) -> List[Dict]:
    """Create card and exercise drafts from extracted pairs."""

    drafts: List[Dict] = []
    definitions = [p[2] for p in pairs]
    for idx, (theme, term, definition) in enumerate(pairs):
        # QA card
        drafts.append(
            {
                "id": f"c{idx}",
                "kind": "card",
                "payload": {
                    "type": "QA",
                    "front": term[:200],
                    "back": definition[:MAX_VERSO_CHARS],
                    "theme": theme,
                    "keywords": _keywords(definition),
                },
            }
        )

        # QCM exercise
        distractors = [d for d in definitions if d != definition]
        random.shuffle(distractors)
        distractors = distractors[:3]
        filler_idx = 0
        while len(distractors) < 3:
            filler = f"option{filler_idx}"
            filler_idx += 1
            if filler not in distractors:
                distractors.append(filler)
        options = distractors + [definition]
        random.shuffle(options)
        drafts.append(
            {
                "id": f"e{idx}",
                "kind": "exercise",
                "payload": {
                    "type": "QCM",
                    "q": f"Quelle est la définition de {term} ?",
                    "options": options,
                    "answer": definition,
                    "theme": theme,
                },
            }
        )

        # Vrai/Faux card
        drafts.append(
            {
                "id": f"v{idx}",
                "kind": "card",
                "payload": {
                    "type": "VF",
                    "front": f"{term} correspond à {definition[:100]}",
                    "answer": "Vrai",
                    "theme": theme,
                },
            }
        )

        # Cloze card
        first_word = definition.split()[0] if definition.split() else definition
        drafts.append(
            {
                "id": f"cl{idx}",
                "kind": "card",
                "payload": {
                    "type": "CLOZE",
                    "front": f"{term} est ____",
                    "answer": first_word.lower(),
                    "theme": theme,
                },
            }
        )

    return drafts


def analyze_offline(text: str) -> List[Dict]:
    """Analyze text and return validated draft items."""
    pairs = _extract_pairs(text)
    drafts = _build_drafts(pairs)
    return validate_items(drafts)
