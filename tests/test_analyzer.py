import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.analyzer import finalize_qcm_item


def test_distractors_deduplication():
    item = {
        "type": "QCM",
        "front": "Quelle est la capitale de la France ?",
        "answer": "Paris",
        "distractors": ["Londres", "Berlin", "Rome", "Berlin", "Paris"],
    }
    fixed = finalize_qcm_item(item)
    assert fixed["type"] == "QCM"
    assert sorted(fixed["options"]) == sorted(["Londres", "Berlin", "Rome", "Paris"])


def test_insufficient_distractors_converts():
    item = {
        "type": "QCM",
        "front": "Le soleil est une étoile.",
        "answer": "étoile",
        "distractors": ["planète", "planète", "étoile"],
    }
    fixed = finalize_qcm_item(item)
    assert fixed["type"] in {"VF", "CLOZE"}
