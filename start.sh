#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "🎓 Starting Studying Coach - Minimal FastAPI Backend"
echo "=============================================="

# Check Python3
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python3 required. Install from https://www.python.org/downloads/"
  exit 1
fi

# Find available port
PORT=8000
while [ $PORT -le 8010 ]; do
  if ! lsof -i :$PORT >/dev/null 2>&1; then
    echo "✅ Port $PORT available"
    break
  fi
  PORT=$((PORT + 1))
done

if [ $PORT -gt 8010 ]; then
  echo "⚠️  No port available between 8000-8010. Using 8000 anyway."
  PORT=8000
fi

# Export PORT for the server
export PORT=$PORT

echo "🚀 Starting server on http://127.0.0.1:$PORT"
echo "📖 Features:"
echo "   • File upload (TXT, PDF, DOCX)"
echo "   • Automatic flashcard generation"
echo "   • Modern responsive UI"
echo "   • Zero external dependencies"

# Open browser after delay
if command -v open >/dev/null 2>&1; then
  (sleep 3 && open "http://127.0.0.1:$PORT") &
elif command -v xdg-open >/dev/null 2>&1; then
  (sleep 3 && xdg-open "http://127.0.0.1:$PORT") &
else
  echo "🌐 Open http://127.0.0.1:$PORT in your browser"
fi

echo "🔥 Press Ctrl+C to stop the server"
echo ""

# Start the simple server
python3 simple_server.py