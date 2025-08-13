#!/bin/bash
# Doctor script to check system health for Studying Coach

echo "==== STUDYING COACH DOCTOR ===="
echo "Checking system health..."
echo

EXIT_CODE=0

# Check if port 5000 is taken
echo "1. Checking port 5000..."
if lsof -nP -iTCP:5000 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "❌ Port 5000 is taken by:"
    lsof -nP -iTCP:5000 -sTCP:LISTEN
    echo "   → Run: kill -9 <PID> to free the port"
    EXIT_CODE=1
else
    echo "✅ Port 5000 is available"
fi
echo

# Check Ollama
echo "2. Checking Ollama..."
if command -v ollama >/dev/null 2>&1; then
    OLLAMA_VERSION=$(ollama --version 2>/dev/null)
    echo "✅ Ollama found: $OLLAMA_VERSION"
    
    # Check Ollama models
    echo "   Checking required models..."
    if ollama list | grep -q "llama3:8b"; then
        echo "   ✅ llama3:8b model found"
    else
        echo "   ❌ llama3:8b model missing"
        echo "      → Run: ollama pull llama3:8b"
        EXIT_CODE=1
    fi
    
    if ollama list | grep -q "nomic-embed-text"; then
        echo "   ✅ nomic-embed-text model found"
    else
        echo "   ❌ nomic-embed-text model missing"
        echo "      → Run: ollama pull nomic-embed-text"
        EXIT_CODE=1
    fi
else
    echo "❌ Ollama not found"
    echo "   → Install with: brew install --cask ollama (macOS)"
    echo "   → Or visit: https://ollama.ai"
    EXIT_CODE=1
fi
echo

# Check backend health (if running)
echo "3. Checking backend health..."
if curl -s http://127.0.0.1:5000/api/health >/dev/null 2>&1; then
    HEALTH_RESP=$(curl -s http://127.0.0.1:5000/api/health)
    echo "✅ Backend health: $HEALTH_RESP"
else
    echo "⚠️  Backend not responding on port 5000 (this is OK if not started yet)"
fi

if curl -s http://127.0.0.1:5000/api/health/llm >/dev/null 2>&1; then
    LLM_HEALTH=$(curl -s http://127.0.0.1:5000/api/health/llm)
    echo "✅ LLM health: $LLM_HEALTH"
else
    echo "⚠️  LLM health endpoint not responding (this is OK if not started yet)"
fi
echo

# Check Python and venv
echo "4. Checking Python environment..."
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python: $PYTHON_VERSION"
else
    echo "❌ Python3 not found"
    EXIT_CODE=1
fi

if [ -d ".venv" ]; then
    echo "✅ Virtual environment found"
else
    echo "⚠️  Virtual environment not found (.venv directory missing)"
    echo "   → Run: python3 -m venv .venv"
fi

if [ -f "requirements.txt" ]; then
    echo "✅ Requirements file found"
else
    echo "❌ requirements.txt not found"
    EXIT_CODE=1
fi
echo

echo "==== SUMMARY ===="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All checks passed! System ready."
else
    echo "❌ Some issues found. Please address them before starting."
fi

echo "Exit code: $EXIT_CODE"
exit $EXIT_CODE