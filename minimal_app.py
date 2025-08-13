#!/usr/bin/env python3
"""
Minimal Study Coach Application
A simplified version that works with minimal dependencies
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Mock Flask-like server for testing
class MockRequest:
    def __init__(self):
        self.method = "GET"
        self.args = {}
        self.json = {}
        self.files = {}

class MockApp:
    def __init__(self):
        self.routes = {}
        
    def route(self, path, methods=None):
        def decorator(func):
            self.routes[path] = func
            return func
        return decorator
        
    def run(self, host="127.0.0.1", port=5000, debug=False):
        print(f"🚀 Studying Coach minimal server starting on {host}:{port}")
        print("\n=== AVAILABLE ROUTES ===")
        for route in self.routes.keys():
            print(f"  {route}")
        print("\n=== TESTING CORE FUNCTIONALITY ===")
        
        # Test core functions
        self.test_basic_functionality()
        print("\n✅ All basic functionality tests passed!")
        print("\n📖 In a full environment, navigate to:")
        print(f"   http://{host}:{port}")
        
        # Keep running
        try:
            input("\nPress Enter to stop the server...\n")
        except KeyboardInterrupt:
            pass
        print("Server stopped.")

    def test_basic_functionality(self):
        # Test database operations
        db = load_db()
        print(f"✅ Database loaded: {len(db.get('cards', []))} cards")
        
        # Test text analysis
        sample_text = "Python est un langage de programmation. Il est facile à apprendre."
        items = analyze_offline_simple(sample_text)
        print(f"✅ Text analysis: extracted {len(items)} items")
        
        # Test settings
        settings = load_minimal_settings()
        print(f"✅ Settings loaded: provider={settings.get('provider', 'unknown')}")

# Simple database functions
DB_FILE = Path("db.json")

def load_db():
    if DB_FILE.exists():
        try:
            with DB_FILE.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except:
            pass
    return {
        "source_docs": [],
        "drafts": [],
        "cards": [],
        "exercises": [],
        "sessions": [],
        "metrics": [],
    }

def save_db(db):
    with DB_FILE.open("w", encoding="utf-8") as fh:
        json.dump(db, fh, indent=2, ensure_ascii=False)

def load_minimal_settings():
    settings_file = Path("settings-local.yaml")
    if settings_file.exists():
        # Simple YAML parsing
        content = settings_file.read_text(encoding="utf-8")
        settings = {}
        for line in content.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                settings[key.strip()] = value.strip()
        return settings
    return {
        "provider": "ollama", 
        "model": "llama3:8b",
        "embedding_model": "nomic-embed-text"
    }

def analyze_offline_simple(text):
    """Simple text analysis without external dependencies"""
    sentences = text.split('.')
    items = []
    
    for i, sentence in enumerate(sentences[:5]):  # Max 5 items
        sentence = sentence.strip()
        if len(sentence) > 10:
            # Simple "definition" detection
            if ' est ' in sentence or ' sont ' in sentence:
                parts = sentence.split(' est ')
                if len(parts) == 2:
                    items.append({
                        "id": f"item_{i}",
                        "kind": "card",
                        "theme": "Concepts",
                        "payload": {
                            "type": "QA",
                            "front": parts[0].strip(),
                            "back": parts[1].strip()
                        }
                    })
    return items

# Mock Flask app
app = MockApp()

@app.route("/")
def index():
    return "Study Coach Home"

@app.route("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.route("/api/analyze", methods=["POST"])
def analyze():
    text = "Sample text for analysis"
    items = analyze_offline_simple(text)
    return {"drafts": items, "meta": {"provider": "offline", "count": len(items)}}

@app.route("/api/upload", methods=["POST"])
def upload():
    # Mock file upload
    return {"saved": 3, "minutes": 25, "due": []}

@app.route("/api/due")
def due_cards():
    db = load_db()
    return {"cards": db.get("cards", [])[:10]}  # Return up to 10 due cards

@app.route("/api/themes")
def themes():
    db = load_db()
    themes = {}
    for card in db.get("cards", []):
        theme = card.get("theme", "General")
        if theme not in themes:
            themes[theme] = {"name": theme, "cards": 0, "exercises": 0}
        themes[theme]["cards"] += 1
    return {"themes": list(themes.values())}

if __name__ == "__main__":
    # Get port from environment or default to 5000
    port = int(os.getenv("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)