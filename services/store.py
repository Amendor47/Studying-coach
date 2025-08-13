import json
from pathlib import Path
from typing import Any, Dict

DB_FILE = Path("db.json")

def load_db() -> Dict[str, Any]:
    if DB_FILE.exists():
        with DB_FILE.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    return {
        "source_docs": [],
        "drafts": [],
        "cards": [],
        "exercises": [],
        "sessions": [],
        "metrics": [],
    }

def save_db(db: Dict[str, Any]) -> None:
    with DB_FILE.open("w", encoding="utf-8") as fh:
        json.dump(db, fh, indent=2, ensure_ascii=False)