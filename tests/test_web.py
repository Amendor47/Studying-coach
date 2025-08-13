import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app


def test_web_search_empty():
    client = app.test_client()
    resp = client.get('/api/web/search?q=')
    assert resp.status_code == 200
    assert resp.get_json()['results'] == []


def test_web_enrich_empty():
    client = app.test_client()
    resp = client.post('/api/web/enrich', json={'query': '', 'use_ai': False})
    js = resp.get_json()
    assert resp.status_code == 200
    assert js['added'] == 0
    assert js['drafts'] == []
