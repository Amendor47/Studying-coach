#!/usr/bin/env python3
"""
Simple HTTP server to test basic functionality
Uses only Python standard library - no external dependencies
"""

import http.server
import socketserver
import json
import os
import urllib.parse
from pathlib import Path
import cgi
import io
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BASE_DIR = Path(__file__).parent  # This file is in the repo root
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "studying_data.json"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

def load_data():
    """Load data from JSON file"""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load data file: {e}")
    
    return {
        "drafts": [],
        "flashcards": [],
        "courses": [],
        "exercises": [],
        "settings": {}
    }

def save_data(data):
    """Save data to JSON file"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Could not save data: {e}")

class StudyingCoachHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for the Studying Coach application"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            # Serve index.html
            self.serve_index()
        elif self.path == '/api/health':
            self.send_json_response({"status": "ok", "timestamp": datetime.now().isoformat()})
        elif self.path == '/api/health/llm':
            self.send_json_response({
                "provider": "local", 
                "model": "llama3:8b", 
                "ok": True, 
                "msg": "LLM service is running"
            })
        elif self.path == '/api/themes':
            data = load_data()
            themes = {}
            for card in data.get("flashcards", []):
                theme = card.get("theme", "General")
                themes[theme] = themes.get(theme, 0) + 1
            self.send_json_response(themes)
        elif self.path == '/api/due':
            data = load_data()
            cards = data.get("flashcards", [])
            self.send_json_response({"cards": cards, "total": len(cards)})
        else:
            # Default file serving
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/upload':
            self.handle_upload()
        elif self.path == '/api/ai/analyze':
            self.handle_ai_analyze()
        elif self.path.startswith('/api/review/'):
            self.handle_review()
        else:
            self.send_error(404, "Endpoint not found")
    
    def serve_index(self):
        """Serve the main HTML page"""
        # Use the simple_index.html template that doesn't require Flask templating
        index_file = TEMPLATES_DIR / "simple_index.html"
        logger.info(f"Looking for simple_index.html at: {index_file}, exists: {index_file.exists()}")
        if index_file.exists():
            try:
                with open(index_file, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                logger.error(f"Error serving index: {e}")
                self.send_error(500, "Internal server error")
        else:
            logger.error(f"Index file not found at {index_file}")
            self.send_json_response({"message": "Welcome to Studying Coach", "status": "running"})
    
    def handle_upload(self):
        """Handle file upload"""
        try:
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                self.send_error(400, "Invalid content type")
                return
            
            # Parse multipart form data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            if 'file' not in form:
                self.send_error(400, "No file uploaded")
                return
            
            file_item = form['file']
            if not file_item.filename:
                self.send_error(400, "No file selected")
                return
            
            # Read file content
            file_content = file_item.file.read()
            text_content = file_content.decode('utf-8', errors='ignore')
            
            # Create basic flashcards from text
            data = load_data()
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            new_cards = []
            
            for i, line in enumerate(lines[:10]):  # Limit to 10 cards for demo
                if len(line) > 20:  # Only process meaningful lines
                    card = {
                        "id": f"card_{datetime.now().timestamp()}_{i}",
                        "recto": line[:50] + "..." if len(line) > 50 else line,
                        "verso": "Generated from uploaded document",
                        "theme": "Upload",
                        "created": datetime.now().isoformat(),
                        "due": datetime.now().isoformat()
                    }
                    new_cards.append(card)
            
            data["flashcards"].extend(new_cards)
            save_data(data)
            
            logger.info(f"Processed file: {file_item.filename}, created {len(new_cards)} cards")
            
            response = {
                "saved": len(new_cards),
                "filename": file_item.filename,
                "minutes": 25,
                "due": new_cards,
                "message": f"Successfully created {len(new_cards)} flashcards"
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Error processing upload: {e}")
            self.send_error(500, f"Upload processing failed: {str(e)}")
    
    def handle_ai_analyze(self):
        """Handle AI text analysis"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "No content")
                return
            
            post_data = self.rfile.read(content_length)
            # Parse form data
            form_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
            text = form_data.get('text', [''])[0]
            
            if not text.strip():
                self.send_error(400, "No text provided")
                return
            
            words = len(text.split())
            
            response = {
                "drafts": [
                    {
                        "id": f"draft_{datetime.now().timestamp()}",
                        "recto": "Sample question from analysis",
                        "verso": "Sample answer from analysis", 
                        "theme": "AI Generated",
                        "created": datetime.now().isoformat()
                    }
                ],
                "meta": {
                    "word_count": words,
                    "estimated_cards": min(words // 50, 10)
                }
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Error in AI analyze: {e}")
            self.send_error(500, f"AI analysis failed: {str(e)}")
    
    def handle_review(self):
        """Handle card review"""
        try:
            # Extract card ID from path
            card_id = self.path.split('/')[-1]
            
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "No content")
                return
            
            post_data = self.rfile.read(content_length)
            form_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
            quality = int(form_data.get('quality', [0])[0])
            
            data = load_data()
            
            for card in data.get("flashcards", []):
                if card.get("id") == card_id:
                    card["last_review"] = datetime.now().isoformat()
                    card["quality"] = quality
                    save_data(data)
                    self.send_json_response({"success": True, "card_id": card_id})
                    return
            
            self.send_error(404, "Card not found")
            
        except Exception as e:
            logger.error(f"Error in review: {e}")
            self.send_error(500, f"Review failed: {str(e)}")
    
    def send_json_response(self, data):
        """Send JSON response"""
        response = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8000))
    
    print(f"Starting Studying Coach server on http://127.0.0.1:{PORT}")
    print(f"Base directory: {BASE_DIR}")
    
    with socketserver.TCPServer(("127.0.0.1", PORT), StudyingCoachHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()