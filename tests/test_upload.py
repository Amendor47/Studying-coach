import json
import sys
from pathlib import Path

# Ensure repository root is on the Python path so ``app`` can be imported
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import app
from services import store


def test_duplicate_upload(tmp_path, monkeypatch):
    # Point the database to a temporary location for isolation
    db_file = tmp_path / "db.json"
    monkeypatch.setattr(store, "DB_FILE", db_file)

    client = app.test_client()

    items = [{"kind": "card", "payload": {"front": "Q1", "back": "A1"}}]

    # First upload inserts the card
    resp1 = client.post("/api/upload", json=items)
    assert resp1.status_code == 200
    db = store.load_db()
    assert len(db["cards"]) == 1

    # Second upload with the same data should not create a duplicate
    resp2 = client.post("/api/upload", json=items)
    assert resp2.status_code == 200
    db = store.load_db()
    assert len(db["cards"]) == 1

