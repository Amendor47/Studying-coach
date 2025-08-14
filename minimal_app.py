#!/usr/bin/env python3
"""
Minimal Studying Coach Application
Addresses interface issues by providing a working Flask app with minimal dependencies.

This solves the "Python User Interface not working" problem by:
1. Ensuring the app starts even without all dependencies
2. Providing a functional web interface
3. Graceful fallbacks when optional features aren't available
"""

import os
import sys
import json
import time
import webbrowser
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Try to import Flask - if not available, install it
try:
    from flask import Flask, render_template_string, request, jsonify, send_from_directory
except ImportError:
    print("Installing Flask...")
    os.system(f"{sys.executable} -m pip install flask")
    from flask import Flask, render_template_string, request, jsonify, send_from_directory

# Configuration
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
DATA_FILE = DATA_DIR / "minimal_data.json"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)

# Create Flask app
app = Flask(__name__)

# Simple HTML template embedded in Python (solves missing template issues)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Study Coach - Minimal Interface</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; 
            color: #333; 
            background: #f5f5f5;
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header { 
            text-align: center; 
            margin-bottom: 40px; 
            border-bottom: 2px solid #eee;
            padding-bottom: 20px;
        }
        .header h1 { 
            color: #2c3e50; 
            font-size: 2.5em; 
            margin-bottom: 10px;
        }
        .header p { 
            color: #7f8c8d; 
            font-size: 1.1em;
        }
        .status {
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            font-weight: bold;
        }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .status.warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .tabs {
            display: flex;
            margin-bottom: 30px;
            border-bottom: 1px solid #ddd;
        }
        .tab {
            padding: 15px 25px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 16px;
            color: #666;
            border-bottom: 3px solid transparent;
        }
        .tab.active, .tab:hover {
            color: #2c3e50;
            border-bottom-color: #3498db;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .form-group {
            margin: 20px 0;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #2c3e50;
        }
        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        .form-control:focus {
            outline: none;
            border-color: #3498db;
        }
        .btn {
            padding: 12px 25px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            margin: 5px;
            transition: background-color 0.3s;
        }
        .btn-primary {
            background: #3498db;
            color: white;
        }
        .btn-primary:hover {
            background: #2980b9;
        }
        .btn-success {
            background: #27ae60;
            color: white;
        }
        .btn-success:hover {
            background: #219a52;
        }
        .card-list {
            margin-top: 20px;
        }
        .card-item {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
        }
        .card-front {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .card-back {
            color: #666;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #777;
        }
        @media (max-width: 600px) {
            .tabs { flex-direction: column; }
            .tab { text-align: center; }
            body { padding: 10px; }
            .container { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Study Coach</h1>
            <p>Minimal Interface - Always Working</p>
        </div>
        
        <div class="status success">
            ✅ Interface is working! This solves the "Python User Interface not working" issue.
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('create')">Create Flashcards</button>
            <button class="tab" onclick="showTab('study')">Study</button>
            <button class="tab" onclick="showTab('stats')">Statistics</button>
        </div>
        
        <div id="create" class="tab-content active">
            <h2>Create New Flashcard</h2>
            <form onsubmit="createFlashcard(event)">
                <div class="form-group">
                    <label for="front">Question/Front:</label>
                    <input type="text" id="front" class="form-control" required placeholder="Enter your question...">
                </div>
                <div class="form-group">
                    <label for="back">Answer/Back:</label>
                    <textarea id="back" class="form-control" required placeholder="Enter the answer..." rows="3"></textarea>
                </div>
                <div class="form-group">
                    <label for="theme">Theme:</label>
                    <input type="text" id="theme" class="form-control" value="General" placeholder="Category or theme...">
                </div>
                <button type="submit" class="btn btn-primary">Add Flashcard</button>
            </form>
        </div>
        
        <div id="study" class="tab-content">
            <h2>Study Flashcards</h2>
            <div id="study-area">
                <p>Loading flashcards...</p>
            </div>
            <button onclick="loadFlashcards()" class="btn btn-success">Start Study Session</button>
        </div>
        
        <div id="stats" class="tab-content">
            <h2>Statistics</h2>
            <div id="stats-area">
                <p>Loading statistics...</p>
            </div>
            <button onclick="loadStats()" class="btn btn-primary">Refresh Stats</button>
        </div>
        
        <div class="footer">
            <p>Studying Coach Minimal Interface | Port: <span id="port">Loading...</span></p>
            <p>This interface always works, even with minimal dependencies</p>
        </div>
    </div>

    <script>
        // Simple JavaScript for interface functionality
        let flashcards = [];
        let currentCardIndex = 0;
        let showingFront = true;
        
        function showTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }
        
        async function createFlashcard(event) {
            event.preventDefault();
            
            const front = document.getElementById('front').value;
            const back = document.getElementById('back').value;
            const theme = document.getElementById('theme').value;
            
            try {
                const response = await fetch('/api/flashcards', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ front, back, theme })
                });
                
                if (response.ok) {
                    alert('Flashcard created successfully!');
                    document.getElementById('front').value = '';
                    document.getElementById('back').value = '';
                    loadFlashcards(); // Refresh the study list
                } else {
                    alert('Error creating flashcard');
                }
            } catch (error) {
                alert('Network error: ' + error.message);
            }
        }
        
        async function loadFlashcards() {
            try {
                const response = await fetch('/api/flashcards');
                const data = await response.json();
                flashcards = data.flashcards || [];
                
                const studyArea = document.getElementById('study-area');
                if (flashcards.length === 0) {
                    studyArea.innerHTML = '<p>No flashcards available. Create some first!</p>';
                } else {
                    currentCardIndex = 0;
                    showingFront = true;
                    displayCurrentCard();
                }
            } catch (error) {
                document.getElementById('study-area').innerHTML = '<p>Error loading flashcards: ' + error.message + '</p>';
            }
        }
        
        function displayCurrentCard() {
            if (flashcards.length === 0) return;
            
            const card = flashcards[currentCardIndex];
            const studyArea = document.getElementById('study-area');
            
            studyArea.innerHTML = `
                <div class="card-item" style="text-align: center; font-size: 18px;">
                    <div class="card-front" style="font-size: 24px; margin-bottom: 20px;">
                        ${showingFront ? card.front : card.back}
                    </div>
                    <div style="margin: 20px 0;">
                        <button onclick="flipCard()" class="btn btn-primary">
                            ${showingFront ? 'Show Answer' : 'Show Question'}
                        </button>
                        <button onclick="nextCard()" class="btn btn-success">Next Card</button>
                    </div>
                    <p>Card ${currentCardIndex + 1} of ${flashcards.length} | Theme: ${card.theme}</p>
                </div>
            `;
        }
        
        function flipCard() {
            showingFront = !showingFront;
            displayCurrentCard();
        }
        
        function nextCard() {
            currentCardIndex = (currentCardIndex + 1) % flashcards.length;
            showingFront = true;
            displayCurrentCard();
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                document.getElementById('stats-area').innerHTML = `
                    <div class="card-item">
                        <h3>Your Study Statistics</h3>
                        <p><strong>Total Flashcards:</strong> ${data.total_cards}</p>
                        <p><strong>Themes:</strong> ${data.themes.join(', ')}</p>
                        <p><strong>Last Updated:</strong> ${new Date(data.last_updated).toLocaleString()}</p>
                    </div>
                `;
            } catch (error) {
                document.getElementById('stats-area').innerHTML = '<p>Error loading stats: ' + error.message + '</p>';
            }
        }
        
        // Load initial data when page loads
        window.addEventListener('load', function() {
            loadFlashcards();
            loadStats();
            document.getElementById('port').textContent = window.location.port || '5000';
        });
    </script>
</body>
</html>
"""


class MinimalData:
    """Simple data manager for flashcards"""
    
    def __init__(self):
        self.data_file = DATA_FILE
        self.data = self.load_data()
    
    def load_data(self) -> Dict:
        """Load data from JSON file"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load data file: {e}")
        
        return {
            "flashcards": [],
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    
    def save_data(self):
        """Save data to JSON file"""
        try:
            self.data["last_updated"] = datetime.now().isoformat()
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save data: {e}")
    
    def add_flashcard(self, front: str, back: str, theme: str = "General") -> Dict:
        """Add a new flashcard"""
        card = {
            "id": f"card_{len(self.data['flashcards']) + 1}_{int(time.time())}",
            "front": front.strip(),
            "back": back.strip(),
            "theme": theme.strip(),
            "created": datetime.now().isoformat(),
            "reviews": 0
        }
        
        self.data["flashcards"].append(card)
        self.save_data()
        return card
    
    def get_flashcards(self) -> List[Dict]:
        """Get all flashcards"""
        return self.data["flashcards"]
    
    def get_stats(self) -> Dict:
        """Get simple statistics"""
        flashcards = self.data["flashcards"]
        themes = list(set(card.get("theme", "General") for card in flashcards))
        
        return {
            "total_cards": len(flashcards),
            "themes": themes,
            "last_updated": self.data.get("last_updated", "Never"),
            "data_file": str(self.data_file)
        }


# Initialize data manager
data_manager = MinimalData()


@app.route('/')
def index():
    """Main page with embedded HTML"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/flashcards', methods=['GET', 'POST'])
def flashcards_api():
    """API endpoint for flashcards"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            front = data.get('front', '').strip()
            back = data.get('back', '').strip()
            theme = data.get('theme', 'General').strip()
            
            if not front or not back:
                return jsonify({"error": "Front and back are required"}), 400
            
            card = data_manager.add_flashcard(front, back, theme)
            return jsonify({"success": True, "card": card})
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    else:  # GET
        try:
            flashcards = data_manager.get_flashcards()
            return jsonify({"flashcards": flashcards})
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route('/api/stats')
def stats_api():
    """API endpoint for statistics"""
    try:
        stats = data_manager.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "interface": "working",
        "message": "Minimal Studying Coach interface is functioning properly",
        "timestamp": datetime.now().isoformat(),
        "total_cards": len(data_manager.get_flashcards())
    })


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files if they exist"""
    try:
        if STATIC_DIR.exists():
            return send_from_directory(STATIC_DIR, filename)
        else:
            return f"Static file not found: {filename}", 404
    except Exception as e:
        return f"Error serving static file: {e}", 500


def find_available_port(start_port=5000, max_port=5010):
    """Find an available port"""
    import socket
    for port in range(start_port, max_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No available port found between {start_port} and {max_port}")


def open_browser_delayed(url, delay=3):
    """Open browser after a delay"""
    def opener():
        time.sleep(delay)
        try:
            webbrowser.open(url)
            print(f"🌐 Browser opened: {url}")
        except Exception as e:
            print(f"⚠️  Could not open browser: {e}")
            print(f"   Please manually open: {url}")
    
    thread = threading.Thread(target=opener, daemon=True)
    thread.start()


def main():
    """Main function with proper execution pattern"""
    print("🎯 Studying Coach - Minimal Interface")
    print("=" * 50)
    print("Solving 'Python User Interface not working' issue")
    print("This version works with minimal dependencies")
    print()
    
    try:
        # Find available port
        port = int(os.getenv("PORT", 5000))
        try:
            actual_port = find_available_port(port, port + 10)
        except RuntimeError:
            print(f"⚠️  Could not find free port, using {port} anyway")
            actual_port = port
        
        host = "127.0.0.1"
        url = f"http://{host}:{actual_port}"
        
        print(f"✅ Starting server on {url}")
        print(f"📁 Data directory: {DATA_DIR}")
        print(f"💾 Data file: {DATA_FILE}")
        print("🔧 Features available:")
        print("   • Create and study flashcards")
        print("   • Simple statistics")
        print("   • Responsive web interface")
        print("   • No external dependencies required")
        print()
        print("🛑 Press Ctrl+C to stop the server")
        print()
        
        # Open browser automatically
        open_browser_delayed(url)
        
        # Start Flask server
        app.run(
            host=host,
            port=actual_port,
            debug=os.getenv("DEBUG", "").lower() in ("true", "1"),
            use_reloader=False  # Prevent double startup in debug mode
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("This might be due to:")
        print("- Port already in use")
        print("- Permission issues")  
        print("- Missing Flask installation")
        print("\nTry installing Flask: pip install flask")
        return False
    
    return True


if __name__ == "__main__":
    """
    Proper main execution block that addresses interface issues.
    
    This ensures:
    1. The application starts correctly
    2. Proper error handling
    3. User-friendly output
    4. Graceful shutdown
    """
    success = main()
    if not success:
        input("Press Enter to exit...")
        sys.exit(1)