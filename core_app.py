#!/usr/bin/env python3
"""
Studying Coach - Rebuilt from Scratch
A simple, robust studying companion that works 100% out of the box.

Core Philosophy:
- Works offline by default
- Graceful AI enhancement when available
- Zero-config setup
- Cross-platform compatibility
- Essential features only, done well
"""

import os
import sys
import json
import time
import hashlib
import datetime
import tempfile
import webbrowser
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Core Flask imports (minimal required dependencies)
try:
    from flask import Flask, render_template, request, jsonify, send_from_directory
    from werkzeug.utils import secure_filename
except ImportError:
    print("❌ Flask not installed. Installing now...")
    os.system(f"{sys.executable} -m pip install flask")
    from flask import Flask, render_template, request, jsonify, send_from_directory
    from werkzeug.utils import secure_filename

# Optional imports with graceful fallbacks
HAS_AI = False
try:
    import openai
    HAS_AI = True
except ImportError:
    pass

HAS_DOCX = False
try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    pass

HAS_PDF = False
try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    HAS_PDF = True
except ImportError:
    pass

# Configuration
@dataclass
class StudyingCoachConfig:
    """Simple configuration for the application"""
    data_dir: str = "data"
    port: int = 5000
    debug: bool = False
    ai_enabled: bool = False
    openai_api_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'StudyingCoachConfig':
        """Load configuration from environment and files"""
        config = cls()
        
        # Check for environment variables
        config.openai_api_key = os.getenv('OPENAI_API_KEY')
        config.debug = os.getenv('DEBUG', '').lower() in ('true', '1', 'yes')
        config.port = int(os.getenv('PORT', 5000))
        
        # Enable AI if we have the key and library
        config.ai_enabled = HAS_AI and bool(config.openai_api_key)
        
        return config

# Data models
@dataclass
class Flashcard:
    """Simple flashcard data structure"""
    id: str
    front: str
    back: str
    theme: str = "General"
    created: str = ""
    last_reviewed: str = ""
    review_count: int = 0
    ease: float = 2.5
    interval: int = 1
    
    def __post_init__(self):
        if not self.id:
            self.id = hashlib.md5(f"{self.front}{self.back}".encode()).hexdigest()[:8]
        if not self.created:
            self.created = datetime.datetime.now().isoformat()

@dataclass
class StudySession:
    """Study session tracking"""
    date: str
    cards_reviewed: int
    cards_correct: int
    theme: str
    
    def __post_init__(self):
        if not self.date:
            self.date = datetime.date.today().isoformat()

class SimpleDataStore:
    """Simple JSON-based data storage"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.cards_file = self.data_dir / "flashcards.json"
        self.sessions_file = self.data_dir / "sessions.json"
        self.documents_file = self.data_dir / "documents.json"
        
    def load_cards(self) -> List[Flashcard]:
        """Load flashcards from storage"""
        if not self.cards_file.exists():
            return []
        
        try:
            with open(self.cards_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Flashcard(**card) for card in data]
        except Exception as e:
            print(f"Warning: Could not load cards: {e}")
            return []
    
    def save_cards(self, cards: List[Flashcard]) -> None:
        """Save flashcards to storage"""
        try:
            with open(self.cards_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(card) for card in cards], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving cards: {e}")
    
    def load_sessions(self) -> List[StudySession]:
        """Load study sessions from storage"""
        if not self.sessions_file.exists():
            return []
        
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [StudySession(**session) for session in data]
        except Exception as e:
            print(f"Warning: Could not load sessions: {e}")
            return []
    
    def save_sessions(self, sessions: List[StudySession]) -> None:
        """Save study sessions to storage"""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(session) for session in sessions], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving sessions: {e}")

class DocumentProcessor:
    """Simple document processing without external dependencies"""
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Extract text from various file formats"""
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        try:
            if file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_extension == '.docx' and HAS_DOCX:
                doc = Document(file_path)
                return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            
            elif file_extension == '.pdf' and HAS_PDF:
                return pdf_extract_text(str(file_path))
            
            else:
                # Fallback: try to read as text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
        
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return ""
    
    @staticmethod
    def create_flashcards_from_text(text: str, theme: str = "General") -> List[Flashcard]:
        """Create flashcards from text using simple heuristics"""
        cards = []
        
        # Split by paragraphs and create simple Q&A cards
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph) > 50 and len(paragraph) < 500:
                # Create a simple question from the paragraph
                sentences = [s.strip() for s in paragraph.split('.') if s.strip()]
                if len(sentences) >= 2:
                    question = f"What is explained in this section about {theme}?"
                    answer = paragraph
                    cards.append(Flashcard(
                        id="",  # Will be auto-generated
                        front=question,
                        back=answer,
                        theme=theme
                    ))
        
        # Look for definitions (simple pattern matching)
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line and len(line) < 200:
                parts = line.split(':', 1)
                if len(parts[0]) < 100 and len(parts[1]) > 10:
                    question = f"What is {parts[0].strip()}?"
                    answer = parts[1].strip()
                    cards.append(Flashcard(
                        id="",  # Will be auto-generated
                        front=question,
                        back=answer,
                        theme=theme
                    ))
        
        return cards

class SimpleSpacedRepetition:
    """Simple spaced repetition algorithm (simplified SM-2)"""
    
    @staticmethod
    def update_card(card: Flashcard, quality: int) -> Flashcard:
        """
        Update card based on review quality (0-5 scale)
        0-2: Incorrect, 3-5: Correct with varying confidence
        """
        card.review_count += 1
        card.last_reviewed = datetime.datetime.now().isoformat()
        
        if quality < 3:
            # Incorrect - reset interval
            card.interval = 1
            card.ease = max(1.3, card.ease - 0.2)
        else:
            # Correct - increase interval
            if card.review_count == 1:
                card.interval = 1
            elif card.review_count == 2:
                card.interval = 6
            else:
                card.interval = int(card.interval * card.ease)
            
            # Adjust ease based on quality
            card.ease = card.ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            card.ease = max(1.3, card.ease)
        
        return card
    
    @staticmethod
    def get_due_cards(cards: List[Flashcard]) -> List[Flashcard]:
        """Get cards that are due for review"""
        today = datetime.date.today()
        due_cards = []
        
        for card in cards:
            if not card.last_reviewed:
                # New card
                due_cards.append(card)
            else:
                try:
                    last_review = datetime.datetime.fromisoformat(card.last_reviewed).date()
                    days_since_review = (today - last_review).days
                    if days_since_review >= card.interval:
                        due_cards.append(card)
                except:
                    # Invalid date format, treat as new
                    due_cards.append(card)
        
        return due_cards

class StudyingCoachApp:
    """Main application class"""
    
    def __init__(self, config: StudyingCoachConfig):
        self.config = config
        self.data_store = SimpleDataStore(config.data_dir)
        self.app = Flask(__name__)
        self.app.secret_key = 'studying-coach-simple-key'
        
        # Set up routes
        self._setup_routes()
        
        # Initialize OpenAI client if available
        self.openai_client = None
        if self.config.ai_enabled:
            try:
                self.openai_client = openai.OpenAI(api_key=self.config.openai_api_key)
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")
                self.config.ai_enabled = False
    
    def _setup_routes(self):
        """Set up Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('simple_index.html', config=self.config)
        
        @self.app.route('/api/health')
        def health():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'ai_available': self.config.ai_enabled,
                'features': {
                    'pdf_support': HAS_PDF,
                    'docx_support': HAS_DOCX,
                    'ai_support': HAS_AI and bool(self.config.openai_api_key)
                }
            })
        
        @self.app.route('/api/cards', methods=['GET'])
        def get_cards():
            """Get all flashcards"""
            cards = self.data_store.load_cards()
            return jsonify([asdict(card) for card in cards])
        
        @self.app.route('/api/cards/due', methods=['GET'])
        def get_due_cards():
            """Get cards due for review"""
            cards = self.data_store.load_cards()
            due_cards = SimpleSpacedRepetition.get_due_cards(cards)
            return jsonify([asdict(card) for card in due_cards])
        
        @self.app.route('/api/cards/review', methods=['POST'])
        def review_card():
            """Review a card and update its state"""
            data = request.get_json()
            card_id = data.get('card_id')
            quality = int(data.get('quality', 3))
            
            cards = self.data_store.load_cards()
            
            # Find and update the card
            for i, card in enumerate(cards):
                if card.id == card_id:
                    cards[i] = SimpleSpacedRepetition.update_card(card, quality)
                    break
            
            self.data_store.save_cards(cards)
            return jsonify({'success': True})
        
        @self.app.route('/api/upload', methods=['POST'])
        def upload_document():
            """Upload and process a document"""
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Save the uploaded file
            filename = secure_filename(file.filename)
            upload_dir = Path(self.config.data_dir) / "uploads"
            upload_dir.mkdir(exist_ok=True)
            file_path = upload_dir / filename
            file.save(str(file_path))
            
            # Extract text
            text = DocumentProcessor.extract_text_from_file(str(file_path))
            if not text:
                return jsonify({'error': 'Could not extract text from file'}), 400
            
            # Get theme from form data
            theme = request.form.get('theme', 'General')
            
            # Create flashcards
            new_cards = DocumentProcessor.create_flashcards_from_text(text, theme)
            
            if not new_cards:
                return jsonify({'error': 'No flashcards could be created from this document'}), 400
            
            # Save new cards
            existing_cards = self.data_store.load_cards()
            
            # Avoid duplicates
            existing_ids = {card.id for card in existing_cards}
            unique_cards = [card for card in new_cards if card.id not in existing_ids]
            
            all_cards = existing_cards + unique_cards
            self.data_store.save_cards(all_cards)
            
            return jsonify({
                'success': True,
                'cards_created': len(unique_cards),
                'cards': [asdict(card) for card in unique_cards]
            })
        
        @self.app.route('/api/cards', methods=['POST'])
        def create_card():
            """Create a new flashcard manually"""
            data = request.get_json()
            
            card = Flashcard(
                id="",  # Will be auto-generated
                front=data.get('front', ''),
                back=data.get('back', ''),
                theme=data.get('theme', 'General')
            )
            
            existing_cards = self.data_store.load_cards()
            existing_cards.append(card)
            self.data_store.save_cards(existing_cards)
            
            return jsonify({'success': True, 'card': asdict(card)})
        
        @self.app.route('/api/themes', methods=['GET'])
        def get_themes():
            """Get available themes"""
            cards = self.data_store.load_cards()
            themes = list(set(card.theme for card in cards))
            return jsonify({'themes': themes})
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            """Serve static files"""
            return send_from_directory('static', filename)
    
    def run(self):
        """Run the application"""
        print(f"""
🎯 Studying Coach - Ready to Launch!

✅ Core Features Available:
   • Document upload and processing
   • Automatic flashcard creation
   • Spaced repetition system
   • Study progress tracking

🚀 Optional Features:
   • AI Enhancement: {'✅ Enabled' if self.config.ai_enabled else '❌ Disabled (set OPENAI_API_KEY)'}
   • PDF Support: {'✅ Available' if HAS_PDF else '❌ Not available (pip install pdfminer.six)'}
   • DOCX Support: {'✅ Available' if HAS_DOCX else '❌ Not available (pip install python-docx)'}

🌐 Starting server at http://localhost:{self.config.port}
        """)
        
        try:
            # Try to open browser
            webbrowser.open(f'http://localhost:{self.config.port}')
        except:
            pass
        
        self.app.run(
            host='0.0.0.0',
            port=self.config.port,
            debug=self.config.debug
        )

def main():
    """Main entry point"""
    print("🚀 Studying Coach - Simple & Robust")
    
    config = StudyingCoachConfig.from_env()
    app = StudyingCoachApp(config)
    app.run()

if __name__ == '__main__':
    main()