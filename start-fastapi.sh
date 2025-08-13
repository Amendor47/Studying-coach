#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "==== Starting Studying Coach FastAPI Backend ===="

# Check Python3 availability
if ! command -v python3 >/dev/null 2>&1; then
  echo "[!] Python3 required. Install via https://www.python.org/downloads/"; exit 1
fi

# Setup virtual environment for backend
if [ ! -d "backend/venv" ]; then 
  echo "Creating virtual environment..."
  python3 -m venv backend/venv
fi

# Activate environment
source backend/venv/bin/activate

# Install dependencies
echo "Installing FastAPI dependencies..."
pip install --upgrade pip >/dev/null
pip install -r backend/requirements.txt

# Function to check if a port is available
is_port_available() {
  ! lsof -i :$1 >/dev/null 2>&1
}

# Find available port from 8000 to 8010 
PORT=8000
while [ $PORT -le 8010 ]; do
  if is_port_available $PORT; then
    echo "Port $PORT available, starting server..."
    break
  fi
  PORT=$((PORT + 1))
done

if [ $PORT -gt 8010 ]; then
  echo "[!] No port available between 8000-8010. Using port 8000 by default."
  PORT=8000
fi

# Export PORT for the FastAPI app
export PORT=$PORT

# Open browser to the correct port
if command -v open >/dev/null 2>&1; then
  (sleep 3 && open "http://127.0.0.1:$PORT") &
elif command -v xdg-open >/dev/null 2>&1; then
  (sleep 3 && xdg-open "http://127.0.0.1:$PORT") &
else
  echo "Open http://127.0.0.1:$PORT in your browser"
fi

echo "Starting Studying Coach FastAPI backend on port $PORT..."
cd backend && python main.py