import hashlib
import re
import unicodedata
from typing import Dict, List

# Constants for limits
MAX_RECTO_CHARS = 200
MAX_VERSO_CHARS = 420
MAX_SENTENCE_WORDS = 18

class ValidationError(Exception):
    """Raised when an item fails validation."""


def words_per_sentence(text: str) -> List[int]:
    sentences = re.split(r"[.!?]+", text)
    return [len(s.split()) for s in sentences if s.strip()]


def ok_recto(text: str) -> bool:
    return (
        isinstance(text, str)
        and len(text) <= MAX_RECTO_CHARS
        and all(w <= MAX_SENTENCE_WORDS for w in words_per_sentence(text))
    )


def is_valid_qcm(item: Dict) -> bool:
    opts = item.get("options", [])
    ans = item.get("answer") or item.get("reponse")
    return (
        isinstance(opts, list)
        and len(opts) == 4
        and len(set(opts)) == 4
        and ans in opts
        and opts.count(ans) == 1
    )


def normalize_answer(text: str) -> str:
    """Lowercase and strip accents for comparison."""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.lower().strip()


def normalize_key(front: str, back: str) -> str:
    base = f"{front}|{back}".lower().strip()
    return hashlib.sha256(base.encode()).hexdigest()


seen_hashes = set()


def validate_card(card: Dict) -> None:
    ctype = card.get("type", "QA").upper()
    front = card.get("front") or card.get("recto")
    back = card.get("back") or card.get("verso")
    if not ok_recto(front):
        raise ValidationError("recto invalide")

    if ctype == "QA":
        if not isinstance(back, str) or len(back) > MAX_VERSO_CHARS:
            raise ValidationError("verso invalide")
        key_back = back
    elif ctype == "QCM":
        if not is_valid_qcm(card):
            raise ValidationError("QCM invalide")
        key_back = card.get("answer") or card.get("reponse")
    elif ctype == "VF":
        ans = (card.get("answer") or card.get("reponse"))
        if ans not in {"Vrai", "Faux"}:
            raise ValidationError("reponse VF invalide")
        key_back = ans
    elif ctype == "CLOZE":
        ans = normalize_answer(card.get("answer") or card.get("reponse"))
        if front.count("____") != 1 or not ans:
            raise ValidationError("cloze invalide")
        key_back = ans
    elif ctype == "RC":
        ans = card.get("answer") or card.get("reponse")
        if not isinstance(ans, str):
            raise ValidationError("reponse courte invalide")
        key_back = ans
    else:
        raise ValidationError("type de carte inconnu")

    h = normalize_key(front, key_back)
    if h in seen_hashes:
        raise ValidationError("duplicate card")
    seen_hashes.add(h)


def validate_exercise(ex: Dict) -> None:
    qtype = (ex.get("type") or "").lower()
    qtext = ex.get("q") or ex.get("question")
    if not isinstance(qtext, str):
        raise ValidationError("exercise question must be string")

    if qtype == "qcm":
        if not is_valid_qcm(ex):
            raise ValidationError("invalid QCM")
        key_back = ex.get("answer") or ex.get("reponse")
    elif qtype == "cloze":
        ans = normalize_answer(ex.get("answer") or "")
        if qtext.count("____") != 1 or not ans:
            raise ValidationError("invalid CLOZE")
        key_back = ans
    elif qtype == "vf":
        ans = ex.get("answer")
        if ans not in {"Vrai", "Faux"}:
            raise ValidationError("invalid VF")
        key_back = ans
    elif qtype == "rc":
        ans = ex.get("answer")
        if not isinstance(ans, str):
            raise ValidationError("invalid RC")
        key_back = ans
    else:
        raise ValidationError("unknown exercise type")

    h = normalize_key(qtext, str(key_back))
    if h in seen_hashes:
        raise ValidationError("duplicate exercise")
    seen_hashes.add(h)


def validate_items(items: List[Dict]) -> List[Dict]:
    validated = []
    for item in items:
        kind = item.get("kind")
        payload = item.get("payload", {})
        try:
            if kind == "card":
                validate_card(payload)
            elif kind == "exercise":
                validate_exercise(payload)
            else:
                raise ValidationError("unknown kind")
        except ValidationError:
            continue
        validated.append(item)
    return validated
