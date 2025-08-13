# Studying-coach

Prototype studying coach backend inspired by SPEC-2 (V2 "Réussite Max").

## ✨ Latest Features

### 🎯 Enhanced Drag & Drop
- **Robust reordering**: Works on desktop and mobile with unified pointer/touch events
- **Backend persistence**: Card order automatically saves via `/api/flashcards/reorder`
- **Keyboard accessibility**: Ctrl+↑/↓ to reorder cards
- **Visual feedback**: Smooth animations with drag handles and drop indicators

### 🤖 Local LLM Integration
- **Ollama support** (default): Connect to local Ollama server
- **Multiple providers**: GPT4All, llama.cpp, with automatic fallback
- **Streaming responses**: Real-time text generation via Server-Sent Events
- **Health monitoring**: `/api/health` endpoint reports LLM availability

### 🧠 AI Analysis Pipeline
- **Enhanced analysis**: `/api/ai/analyze` with structured insights
- **Study material generation**: `/api/ai/exercises` creates flashcards, quizzes, mnemonics
- **RAG integration**: Context-aware responses using advanced retrieval
- **Graceful fallbacks**: Works offline when LLM unavailable

## Features
- Text normalization and chunking utilities (`services/chunker.py`).
- Offline analyzer that segments chapters/paragraphed text, extracts mots-clés and
  generates QA, QCM, Vrai/Faux and Cloze drafts (`services/analyzer.py`).
- Strict validation and deduplication of items (`services/validate.py`).
- Heuristics to decide if AI is needed (`services/heuristics.py`) with optional
  "Améliorer via IA" button.
- Cache and log wrapper for LLM calls (`services/ai.py`).
- **NEW**: Unified local LLM adapter (`services/local_llm.py`) with Ollama, GPT4All, llama.cpp support
- **NEW**: AI pipeline orchestration (`services/ai_pipeline.py`) for educational analysis
- Configurable local LLM support: choose a provider via environment variables
- Optional local semantic search feeding AI context (`services/rag.py`).
- Optional web enrichment: DuckDuckGo search + scraping with caching
  (`services/webfetch.py`) and UI button to add results as new fiches.
- JSON store helpers (`services/store.py`).
- Planner and SM‑2 scheduler (`services/planner.py`, `services/scheduler.py`) with
  interleaving of due cards across themes and API routes to fetch and record reviews.
- Export of validated fiches to CSV, PDF or DOCX (`/api/export/<fmt>`).
- **NEW**: Enhanced drag & drop interface with reordering persistence
- Cached LLM calls stored under `cache/` and traces written to `logs/`.

## 🚀 Quick start

### 🍎 macOS One-Click Setup (Recommended)
For the best experience on macOS with Ollama:

1. **Install Ollama**: Download from [ollama.com](https://ollama.com/download)
2. **Pull required models**:
   ```bash
   ollama pull llama3:8b
   ollama pull nomic-embed-text
   ```
3. **Start Ollama server**: `ollama serve` (runs in background)
4. **Launch Studying Coach**: `./start-coach.command`

That's it! The launcher script will:
- ✅ Create a virtual environment and install dependencies
- ✅ Auto-generate `settings-local.yaml` with Ollama defaults
- ✅ Configure `.env` with proper Ollama settings (preserving existing keys)
- ✅ Find a free port (5000-5010) to avoid conflicts
- ✅ Open your browser automatically to the correct URL
- ✅ Enable drag & drop without OCR dependencies (advanced analysis is opt-in)

### Platform Launchers
Use one of the launcher scripts at the project root depending on your platform:

- **macOS (One-Click):** `./start-coach.command` ⭐ 
- **Windows (CMD):** `Start-Coach.bat`
- **Windows (PowerShell):** `Start-Coach.ps1`

### Manual Setup
```bash
# Clone and install dependencies
git clone <repo-url>
cd Studying-coach
pip install -r requirements.txt

# Set up local LLM (optional)
cp .env.example .env
# Edit .env to configure your LLM provider

# Start the server
python app.py
```

**Note:** The macOS launcher uses intelligent port selection - if port 5000 is busy, it automatically tries 5001, 5002, etc. until it finds an available port.

## 🤖 Local AI Setup

### Ollama (Default with macOS launcher)
The macOS launcher automatically configures Ollama, but for manual setup:

1. **Install Ollama**: Download from [ollama.com](https://ollama.com/download)
2. **Pull models**: 
   ```bash
   ollama pull llama3:8b
   ollama pull nomic-embed-text
   ```
3. **Configure** (auto-configured by launcher): Set in `.env`:
   ```
   LLM_PROVIDER=ollama
   OLLAMA_HOST=http://127.0.0.1:11434
   OLLAMA_MODEL=llama3:8b
   ```

### GPT4All Alternative
1. **Install**: `pip install gpt4all`
2. **Configure**: Set in `.env`:
   ```
   LLM_PROVIDER=gpt4all
   GPT4ALL_MODEL=mistral-7b-instruct-v0.1.Q4_0.gguf
   ```

### llama.cpp Alternative
1. **Install**: `pip install llama-cpp-python`
2. **Download model**: Get a GGUF model file
3. **Configure**: Set in `.env`:
   ```
   LLM_PROVIDER=llama_cpp
   LLAMA_CPP_MODEL_PATH=/path/to/model.gguf
   ```

## 📚 Usage

Importer un texte puis cliquez sur **Analyser** pour générer des fiches hors IA.
Si la heuristique le suggère ou via le bouton **Améliorer via IA**, un appel à
l'LLM local peut compléter les fiches. 

### New AI Features
- **Enhanced analysis**: Use `enhanced: true` in analysis requests for structured insights
- **Exercise generation**: `/api/ai/exercises` creates diverse study materials
- **Drag & drop reordering**: Rearrange flashcards with mouse/touch, order persists automatically
- **Health monitoring**: Check `/api/health` to see LLM and system status

Les fiches acceptées sont planifiées automatiquement et apparaissent ensuite dans l'onglet
**Flashcards** pour les révisions espacées.

## Standalone executables

To bundle the coach as a single binary (`.exe` on Windows, Unix binary on macOS/Linux),
install PyInstaller and run:

```
python build.py
```

The resulting file appears in `dist/` as `coach.exe` (Windows) or `coach`
(macOS/Linux). Launch it directly to start the server without Python.
