#!/usr/bin/env python3
"""
Minimal FastAPI backend for Studying Coach
Replaces the complex Flask app with basic functionality
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Studying Coach API",
    description="Minimal backend for the studying coach application",
    version="1.0.0"
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving
BASE_DIR = Path(__file__).parent.parent
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Simple in-memory storage (will persist to JSON file)
DATA_FILE = BASE_DIR / "data" / "studying_data.json"
DATA_FILE.parent.mkdir(exist_ok=True)

def load_data() -> Dict[str, Any]:
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

def save_data(data: Dict[str, Any]):
    """Save data to JSON file"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Could not save data: {e}")

# Health endpoint
@app.get("/api/health/llm")
async def health_llm():
    """Check LLM health - simplified version"""
    # For now, just return a basic response
    # In a full implementation, this would check Ollama or OpenAI API
    return {
        "provider": "local", 
        "model": "llama3:8b", 
        "ok": True, 
        "msg": "LLM service is running"
    }

@app.get("/api/health")
async def health():
    """Basic health check"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# File upload endpoint
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    use_ai: bool = Form(False),
    session_minutes: int = Form(25)
):
    """Handle file upload and basic processing"""
    try:
        # Read file content
        content = await file.read()
        
        # For now, just create a simple text extraction
        # In a full implementation, this would use OCR/text extraction
        text_content = content.decode('utf-8', errors='ignore')
        
        # Create basic flash cards from text
        data = load_data()
        
        # Simple text processing to create flashcards
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
        
        logger.info(f"Processed file: {file.filename}, created {len(new_cards)} cards")
        
        return {
            "saved": len(new_cards),
            "filename": file.filename,
            "minutes": session_minutes,
            "due": new_cards,
            "message": f"Successfully created {len(new_cards)} flashcards"
        }
        
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

# Get themes
@app.get("/api/themes")
async def get_themes():
    """Return available themes"""
    data = load_data()
    themes = {}
    
    for card in data.get("flashcards", []):
        theme = card.get("theme", "General")
        themes[theme] = themes.get(theme, 0) + 1
    
    return themes

# Get due cards
@app.get("/api/due")
async def get_due_cards():
    """Return cards due for review"""
    data = load_data()
    cards = data.get("flashcards", [])
    
    # For simplicity, return all cards as "due"
    return {
        "cards": cards,
        "total": len(cards)
    }

# Review a card
@app.post("/api/review/{card_id}")
async def review_card(card_id: str, quality: int = Form(...)):
    """Update card review status"""
    data = load_data()
    
    for card in data.get("flashcards", []):
        if card.get("id") == card_id:
            card["last_review"] = datetime.now().isoformat()
            card["quality"] = quality
            save_data(data)
            return {"success": True, "card_id": card_id}
    
    raise HTTPException(status_code=404, detail="Card not found")

# Simple AI endpoint for text improvement
@app.post("/api/ai/analyze")
async def analyze_text(text: str = Form(...)):
    """Simple text analysis - placeholder for AI processing"""
    # This is a placeholder - in real implementation would call LLM
    words = len(text.split())
    
    return {
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

# Serve main page
@app.get("/")
async def serve_index():
    """Serve the main HTML page"""
    index_file = templates_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        return {"message": "Welcome to Studying Coach API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Studying Coach backend on http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, reload=True)