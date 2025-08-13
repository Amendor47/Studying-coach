#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "==== Coach de Révision — LANCEUR MAC ===="

# Check Python3 availability
if ! command -v python3 >/dev/null 2>&1; then
  echo "[!] Python3 requis. Installez via https://www.python.org/downloads/"; exit 1
fi

# Setup virtual environment
if [ ! -d ".venv" ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install --upgrade pip >/dev/null
if [ -f requirements.txt ]; then pip install -r requirements.txt; else pip install flask openai python-docx pdfminer.six python-dotenv pyyaml requests; fi

# Create settings-local.yaml with Ollama defaults if missing
if [ ! -f "settings-local.yaml" ]; then
  echo "Création de settings-local.yaml avec les paramètres Ollama par défaut..."
  cat > settings-local.yaml << EOF
provider: ollama
model: llama3:8b
embedding_model: nomic-embed-text
top_k: 5
timeout_s: 60
temperature: 0.1
EOF
fi

# Manage .env file - append missing Ollama config without overwriting existing keys
if [ ! -f ".env" ]; then
  echo "Création du fichier .env avec la configuration Ollama par défaut..."
  cat > .env << EOF
SC_PROFILE=local
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3:8b
OLLAMA_HOST=http://127.0.0.1:11434
EOF
else
  # Append missing keys only
  if ! grep -q "SC_PROFILE" .env; then
    echo "SC_PROFILE=local" >> .env
  fi
  if ! grep -q "LLM_PROVIDER" .env; then
    echo "LLM_PROVIDER=ollama" >> .env
  fi
  if ! grep -q "OLLAMA_MODEL" .env; then
    echo "OLLAMA_MODEL=llama3:8b" >> .env
  fi
  if ! grep -q "OLLAMA_HOST" .env; then
    echo "OLLAMA_HOST=http://127.0.0.1:11434" >> .env
  fi
fi

# Function to check if a port is available
is_port_available() {
  ! lsof -i :$1 >/dev/null 2>&1
}

# Find available port from 5000 to 5010
PORT=5000
while [ $PORT -le 5010 ]; do
  if is_port_available $PORT; then
    echo "Port $PORT disponible, démarrage du serveur..."
    break
  fi
  PORT=$((PORT + 1))
done

if [ $PORT -gt 5010 ]; then
  echo "[!] Aucun port disponible entre 5000 et 5010. Utilisation du port 5000 par défaut."
  PORT=5000
fi

# Export PORT for the Flask app
export PORT=$PORT

# Open browser to the correct port
if command -v open >/dev/null 2>&1; then
  (sleep 2 && open "http://127.0.0.1:$PORT") &
elif command -v xdg-open >/dev/null 2>&1; then
  (sleep 2 && xdg-open "http://127.0.0.1:$PORT") &
else
  echo "Ouvrez http://127.0.0.1:$PORT dans votre navigateur"
fi

echo "Démarrage de Studying Coach sur le port $PORT..."
python3 app.py
