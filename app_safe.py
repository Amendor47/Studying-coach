#!/usr/bin/env python3
"""
Study Coach - Safe Bootstrap Version
Handles missing dependencies gracefully and provides fallback implementations.
"""

import io
import csv
import os
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Try to import Flask, provide fallback if not available
try:
    from flask import Flask, jsonify, request, render_template, Response, send_file
    HAS_FLASK = True
except ImportError:
    print("⚠️  Flask not available, using minimal server")
    HAS_FLASK = False

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Create a simple .env loader
    def load_dotenv():
        env_file = Path('.env')
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    load_dotenv()

# Try to import services with fallbacks
try:
    from services.store import load_db, save_db
except ImportError:
    # Fallback database functions
    DB_FILE = Path("db.json")
    def load_db() -> Dict[str, Any]:
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
    
    def save_db(db: Dict[str, Any]) -> None:
        with DB_FILE.open("w", encoding="utf-8") as fh:
            json.dump(db, fh, indent=2, ensure_ascii=False)

# Import analyzer with fallback
try:
    from services.analyzer import analyze_offline
except ImportError:
    def analyze_offline(text: str) -> List[Dict[str, Any]]:
        """Fallback offline analysis"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        items = []
        
        for i, sentence in enumerate(sentences[:10]):  # Max 10 items
            if len(sentence) > 20:
                # Simple definition detection
                if ' est ' in sentence.lower():
                    parts = sentence.split(' est ', 1)
                    if len(parts) == 2:
                        items.append({
                            "id": f"fallback_{i}",
                            "kind": "card", 
                            "theme": "Concepts",
                            "payload": {
                                "type": "QA",
                                "front": parts[0].strip(),
                                "back": parts[1].strip()
                            }
                        })
                elif len(sentence) > 30:
                    # Create a simple flashcard
                    words = sentence.split()
                    if len(words) > 5:
                        items.append({
                            "id": f"fallback_{i}",
                            "kind": "card",
                            "theme": "Review", 
                            "payload": {
                                "type": "QA",
                                "front": f"Que savez-vous sur: {' '.join(words[:5])}...",
                                "back": sentence
                            }
                        })
        return items

# Import other services with fallbacks
try:
    from services.config import load_settings
except ImportError:
    def load_settings():
        settings_file = Path("settings-local.yaml")
        if settings_file.exists():
            content = settings_file.read_text(encoding="utf-8")
            settings = {}
            for line in content.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    settings[key.strip()] = value.strip()
            return type('Settings', (), settings)()
        return type('Settings', (), {
            'provider': 'ollama',
            'model': 'llama3:8b',
            'embedding_model': 'nomic-embed-text'
        })()

# Mock missing functions
def validate_items(items): 
    return items

def seed_seen_hashes():
    pass

def ai_needed(text, items):
    return len(items) < 3

def readability(text):
    return 0.8

def density(text, items):
    return len(items) / max(len(text.split()), 100) * 100

def get_context(query, k=3):
    return []

def generate_plan(text):
    return {"sessions": 3, "minutes": 45}

def due_cards():
    db = load_db()
    return db.get("cards", [])

def update_srs(card_id, result):
    pass

def build_exercises_from_cards(cards):
    return []

def save_progress(session_data):
    pass

def extract_text(filepath, filename):
    """Simple text extractor"""
    ext = Path(filename).suffix.lower()
    try:
        if ext == '.txt' or ext == '.md':
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
    except:
        pass
    return f"Could not extract text from {filename}"

# Initialize Flask app if available
if HAS_FLASK:
    BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        static_folder=os.path.join(BASE_DIR, "static"),
        template_folder=os.path.join(BASE_DIR, "templates"),
    )

    # Try to configure CORS
    try:
        from flask_cors import CORS
        cors_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
        if cors_origins:
            CORS(app, origins=cors_origins)
    except ImportError:
        pass

    # Routes
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "has_flask": HAS_FLASK,
            "version": "safe-bootstrap"
        })

    @app.route("/api/analyze", methods=["POST"])
    def analyze():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data"}), 400
            
            text = data.get("text", "")
            if not text:
                return jsonify({"error": "No text provided"}), 400

            # Analyze the text
            items = analyze_offline(text)
            validated_items = validate_items(items)
            
            return jsonify({
                "drafts": validated_items,
                "meta": {
                    "provider": "offline",
                    "model": "fallback",
                    "count": len(validated_items),
                    "readability": readability(text),
                    "ai_needed": ai_needed(text, validated_items)
                }
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/upload", methods=["POST"])
    def upload():
        try:
            if 'file' not in request.files:
                return jsonify({"error": "No file provided"}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400

            # Save uploaded file temporarily
            temp_path = Path("temp_uploads")
            temp_path.mkdir(exist_ok=True)
            
            filepath = temp_path / file.filename
            file.save(str(filepath))
            
            # Extract text
            text = extract_text(str(filepath), file.filename)
            
            # Clean up
            filepath.unlink(missing_ok=True)
            
            # Analyze the text
            items = analyze_offline(text)
            validated_items = validate_items(items)
            
            # Save to database
            db = load_db()
            
            # Add source document
            db["source_docs"].append({
                "id": f"doc_{int(time.time())}",
                "filename": file.filename,
                "timestamp": datetime.now().isoformat(),
                "text_length": len(text),
                "items_count": len(validated_items)
            })
            
            # Add cards
            for item in validated_items:
                item["id"] = f"card_{int(time.time() * 1000)}_{len(db['cards'])}"
                item["created_at"] = datetime.now().isoformat()
                item["due_date"] = (datetime.now() + timedelta(days=1)).isoformat()
                db["cards"].append(item)
            
            save_db(db)
            
            return jsonify({
                "saved": len(validated_items),
                "minutes": max(25, len(text) // 100),  # Rough estimate
                "due": due_cards()
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/due")
    def get_due_cards():
        try:
            cards = due_cards()
            return jsonify({"cards": cards[:20]})  # Limit to 20 cards
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/themes")
    def get_themes():
        try:
            db = load_db()
            themes = {}
            
            for card in db.get("cards", []):
                theme_name = card.get("theme", "General")
                if theme_name not in themes:
                    themes[theme_name] = {"name": theme_name, "cards": 0, "exercises": 0}
                themes[theme_name]["cards"] += 1
            
            return jsonify({"themes": list(themes.values())})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/fiches/<theme>")
    def get_course_cards(theme):
        try:
            db = load_db()
            cards = [card for card in db.get("cards", []) if card.get("theme") == theme]
            return jsonify({
                "theme": theme,
                "cards": cards,
                "total": len(cards)
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/card/<card_id>/status", methods=["POST"])
    def update_card_status(card_id):
        try:
            data = request.get_json()
            status = data.get("status")
            
            # Update SRS
            update_srs(card_id, status)
            
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/web/search", methods=["POST"])
    def web_search():
        # Placeholder for web search functionality
        return jsonify({
            "results": [],
            "message": "Web search not available in safe mode"
        })

    @app.route("/api/settings", methods=["GET", "POST"])
    def settings_endpoint():
        if request.method == "GET":
            settings = load_settings()
            return jsonify({
                "provider": getattr(settings, 'provider', 'ollama'),
                "model": getattr(settings, 'model', 'llama3:8b'),
                "embedding_model": getattr(settings, 'embedding_model', 'nomic-embed-text')
            })
        else:
            # Save settings (placeholder)
            return jsonify({"success": True})

    if __name__ == "__main__":
        port = int(os.getenv("PORT", 5000))
        print(f"🚀 Study Coach starting on port {port}")
        print(f"🔧 Safe mode - Flask available: {HAS_FLASK}")
        app.run(host="127.0.0.1", port=port, debug=True)

else:
    # Fallback server without Flask
    print("❌ Flask not available. Please install Flask to run the full application.")
    print("Run: pip install flask python-dotenv")
    sys.exit(1)