import json
from services.analyzer import _sections, _extract_pairs, analyze_offline
from services.validate import validate_items

SAMPLE_TEXT = """# Chapitre 1
Photosynthèse : transformation de l'énergie lumineuse en énergie chimique.
Chlorophylle est un pigment vert.
"""

def test_extract_pairs():
    sections = _sections(SAMPLE_TEXT)
    pairs = _extract_pairs(sections)
    assert ("Chapitre 1", "Photosynthèse", "transformation de l'\u00e9nergie lumineuse en \u00e9nergie chimique.") in pairs


def test_analyze_offline_generates_valid_items():
    drafts = analyze_offline(SAMPLE_TEXT)
    items = validate_items(drafts)
    # Expect at least one QA card and one course summary
    assert any(d["kind"] == "card" and d["payload"]["type"] == "QA" for d in items)
    assert any(d["kind"] == "course" for d in items)
