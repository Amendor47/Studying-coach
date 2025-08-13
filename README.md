# Studying-coach
Studying coach that will help me improve in learning. 

Prototype studying coach backend inspired by SPEC-2 (V2 "Réussite Max").

## Features
- Text chunking utilities (`services/chunker.py`).
- Draft generation and validation (`services/analyzer.py`, `services/validate.py`).
- Heuristics to decide if AI is needed (`services/heuristics.py`).
- Simple cache and log wrapper for AI calls (`services/ai.py`).
- JSON store helpers (`services/store.py`).
- Minimal Flask app with offline analysis and save endpoints (`app.py`).
- Lightweight front-end with modern 2025 design (`templates/index.html`, `static/`).

## Quick start

Use one of the launcher scripts at the project root depending on your platform:

- **Windows (CMD):** `Start-Coach.bat`
- **Windows (PowerShell):** `Start-Coach.ps1`
- **macOS:** `./start-coach.command`

Each script creates a virtual environment, installs dependencies and runs the Flask server.