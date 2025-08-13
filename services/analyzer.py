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


def _extract_pairs(sections: List[Tuple[str, str]]) -> List[Tuple[str, str, str]]:
    """Return list of (theme, term, definition) triples from parsed sections.

    The heuristic scans full paragraphs instead of isolated lines and relies on a
    small dictionary of link words (``est``, ``signifie``, etc.). It skips pairs
    where either side is too short, which previously produced nonsensical
    flashcards.
    """

    pairs: List[Tuple[str, str, str]] = []
    connectors = [":", "-", " est ", " signifie ", " correspond à "]
    for theme, para in sections:
        for sent in re.split(r"(?<=[.!?])\s+", para):
            for conn in connectors:
                if conn in sent:
                    term, definition = sent.split(conn, 1)
                    term = term.strip()
                    definition = definition.strip()
                    if len(term.split()) < 7 and len(definition.split()) >= 3:
                        pairs.append((theme, term, definition))
                    break
    return pairs


def _build_courses(sections: List[Tuple[str, str]]) -> List[Dict]:
    """Create course items summarising each theme."""
    grouped: Dict[str, List[str]] = {}
    for theme, para in sections:
        grouped.setdefault(theme, []).append(para)

    courses: List[Dict] = []
    for idx, (theme, paras) in enumerate(grouped.items()):
        text = " ".join(paras)
        sentences = [s.strip() for s in re.split(r"[.!?]", text) if s.strip()]
        summary = " ".join(sentences[:2])[:MAX_VERSO_CHARS]
        bullets = sentences[:4]
        courses.append(
            {
                "id": f"course{idx}",
                "kind": "course",
                "payload": {
                    "title": theme,
                    "summary": summary,
                    "bullets": bullets,
                    "keywords": _keywords(text, top=5),
                    "theme": theme,
                },
            }
        )
    return courses


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

        # QCM exercise (only if we have enough unique distractors)
        distractors = [d for d in definitions if d != definition]
        distractors = list(dict.fromkeys(distractors))
        random.shuffle(distractors)
        if len(distractors) >= 3:
            options = distractors[:3] + [definition]
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


def _summarize_para(p: str, max_len: int = 240) -> str:
    """Return a tiny summary made of 2-3 short sentences."""
    sents = re.split(r"(?<=[.!?])\s+", p.strip())
    out: List[str] = []
    words = 0
    for s in sents:
        if not s:
            continue
        out.append(s.strip())
        words += len(s.split())
        if words >= 45 or len(out) >= 3:
            break
    text = " ".join(out).strip()
    return text[:max_len]


def analyze_offline(text: str) -> List[Dict]:
    """Analyze text and return validated draft items."""
    sections = _sections(text)
    pairs = _extract_pairs(sections)
    drafts = _build_drafts(pairs)

    # generate 'course' fiches for each section
    for theme, para in sections:
        kws = _keywords(para, top=5)
        outline: List[str] = []
        for line in para.splitlines():
            line = line.strip(" -•\t")
            if len(line.split()) >= 3 and any(ch.isalpha() for ch in line):
                outline.append(line)
            if len(outline) >= 5:
                break
        summary = _summarize_para(para)
        payload = {
            "type": "COURSE",
            "title": theme,
            "summary": summary,
            "bullets": outline[:5],
            "keywords": kws,
            "theme": theme,
            "level": 1,
        }
        drafts.append({"id": f"co{len(drafts)}", "kind": "course", "payload": payload})

    return drafts
