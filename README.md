# Studying-coach

Prototype studying coach backend inspired by SPEC-2 (V2 "Réussite Max").

## Features
- Text normalization and chunking utilities (`services/chunker.py`).
- Offline analyzer that segments chapters/paragraphed text, extracts mots-clés and
  generates QA, QCM, Vrai/Faux and Cloze drafts (`services/analyzer.py`).
- Strict validation and deduplication of items (`services/validate.py`).
- Heuristics to decide if AI is needed (`services/heuristics.py`) with optional
  "Améliorer via IA" button.
- Cache and log wrapper for LLM calls (`services/ai.py`).
- Optional local semantic search feeding AI context (`services/rag.py`).
- JSON store helpers (`services/store.py`).
- Planner and SM‑2 scheduler (`services/planner.py`, `services/scheduler.py`) with
  API routes to fetch due cards and record reviews.
- Export of validated fiches to CSV, PDF or DOCX (`/api/export/<fmt>`).
- Web interface with tabs *Importer*, *Fiches de cours*, *Flashcards*, *Exercices* and a floating Pomodoro timer. Modern cards use gradient backgrounds with light/dark themes.
- Cached LLM calls stored under `cache/` and traces written to `logs/`.

## Quick start

Use one of the launcher scripts at the project root depending on your platform:

- **Windows (CMD):** `Start-Coach.bat`
- **Windows (PowerShell):** `Start-Coach.ps1`
- **macOS:** `./start-coach.command`

Each script creates a virtual environment, installs dependencies and runs the Flask server.
Once démarré, ouvrez `http://127.0.0.1:5000` pour accéder à l'interface.

Importer un texte puis cliquez sur **Analyser** pour générer des fiches hors IA.
Si la heuristique le suggère ou via le bouton **Améliorer via IA**, un appel à
l'API OpenAI peut compléter les fiches. La première visite affiche un
dialogue pour saisir la clé `OPENAI_API_KEY` stockée localement dans `.env`.
Les fiches acceptées
sont planifiées automatiquement et apparaissent ensuite dans l'onglet
**Flashcards** pour les révisions espacées.

## Standalone executables

To bundle the coach as a single binary (`.exe` on Windows, Unix binary on macOS/Linux),
install PyInstaller and run:

```
python build.py
```

The resulting file appears in `dist/` as `coach.exe` (Windows) or `coach`
(macOS/Linux). Launch it directly to start the server without Python.
