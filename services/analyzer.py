"""Simple text analyzer and item normalizer."""

from typing import Dict, List

try:  # pragma: no cover - import guard
    import spacy  # type: ignore
    try:
        nlp = spacy.load("fr_core_news_sm")  # modèle français
    except Exception:  # pragma: no cover - fallback if model missing
        nlp = spacy.blank("fr")
except Exception:  # pragma: no cover - spacy not installed
    spacy = None
    nlp = None


def advanced_analyze(text: str) -> Dict[str, List[Dict]]:
    if nlp is None:
        return {}
    doc = nlp(text)
    themes: Dict[str, List[Dict]] = {}
    for sent in doc.sents:
        # Détecter concept clé, définition, exemple, relation
        keywords = [token.text for token in sent if token.is_alpha and not token.is_stop]
        theme = "Général"
        if keywords:
            theme = keywords[0]  # exemple simple, à raffiner
        if theme not in themes:
            themes[theme] = []
        themes[theme].append(
            {
                "front": sent.text[:200],
                "back": sent.text,
                "type": "QA",
            }
        )
    return themes


def _dedupe(seq: List[str]) -> List[str]:
    """Remove duplicates while preserving order."""
    return list(dict.fromkeys(seq))


def finalize_qcm_item(item: Dict) -> Dict:
    """Ensure QCM items have unique distractors or fall back to simpler types."""
    ans = item.get("answer") or item.get("reponse")
    distractors = _dedupe(item.get("distractors", []))
    distractors = [d for d in distractors if d != ans]
    if len(distractors) >= 3:
        item["options"] = distractors[:3] + [ans]
        item.pop("distractors", None)
        return item

    front = item.get("front", "")
    back = item.get("back", "")
    if ans and ans in front:
        return {
            "front": front.replace(ans, "____"),
            "back": back,
            "answer": ans,
            "type": "CLOZE",
        }

    return {
        "front": front,
        "back": back,
        "answer": "Vrai",
        "options": ["Vrai", "Faux"],
        "type": "VF",
    }


def finalize_items(items: List[Dict]) -> List[Dict]:
    """Normalize a list of items, fixing QCM distractors."""
    normalized: List[Dict] = []
    for it in items:
        if it.get("type") == "QCM":
            normalized.append(finalize_qcm_item(it))
        else:
            normalized.append(it)
    return normalized

