import io
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from services.store import DB_FILE


def test_upload_txt(tmp_path):
    if DB_FILE.exists():
        DB_FILE.unlink()
    client = app.test_client()
    data = {
        'file': (io.BytesIO(b"Python: langage de programmation"), 'sample.txt'),
        'use_ai': 'false',
        'session_minutes': '10'
    }
    resp = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    js = resp.get_json()
    assert js['saved'] >= 1
    assert DB_FILE.exists()
    DB_FILE.unlink()
