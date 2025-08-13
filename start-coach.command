#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "==== Studying Coach — LANCEUR CROSS-PLATFORM ===="

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is available
is_port_available() {
  if command_exists lsof; then
    ! lsof -i :$1 >/dev/null 2>&1
  elif command_exists netstat; then
    ! netstat -ln | grep ":$1 " >/dev/null 2>&1
  else
    # Fallback: just try the port
    true
  fi
}

# Check if we have a prebuilt executable
if [ -f "dist/StudyCoach" ] && [ -x "dist/StudyCoach" ]; then
  echo "[*] Utilisation de l'exécutable standalone..."
  
  # Find available port from 5000 to 5010
  PORT=5000
  while [ $PORT -le 5010 ]; do
    if is_port_available $PORT; then
      echo "[*] Port $PORT disponible"
      break
    fi
    PORT=$((PORT + 1))
  done

  if [ $PORT -gt 5010 ]; then
    echo "[!] Aucun port disponible entre 5000 et 5010. Utilisation du port 5000."
    PORT=5000
  fi

  # Export PORT for the application
  export PORT=$PORT
  
  # Open browser to the correct port
  if command_exists open; then
    (sleep 3 && open "http://127.0.0.1:$PORT") &
  elif command_exists xdg-open; then
    (sleep 3 && xdg-open "http://127.0.0.1:$PORT") &
  else
    echo "[*] Ouvrez http://127.0.0.1:$PORT dans votre navigateur"
  fi
  
  echo "[*] Démarrage de Studying Coach (standalone) sur le port $PORT..."
  ./dist/StudyCoach
  exit $?
fi

# Fallback to Python development mode
echo "[*] Exécutable standalone non trouvé, utilisation du mode développement Python..."

# Check Python3 availability
if ! command_exists python3; then
  echo "[!] Python3 requis. Installez via https://www.python.org/downloads/"
  exit 1
fi

# Setup virtual environment
if [ ! -d ".venv" ]; then 
  echo "[*] Création de l'environnement virtuel..."
  python3 -m venv .venv
fi

source .venv/bin/activate

# Install/upgrade dependencies
echo "[*] Vérification des dépendances..."
pip install --upgrade pip >/dev/null 2>&1

if [ -f requirements.txt ]; then 
  pip install -r requirements.txt >/dev/null 2>&1
else 
  pip install flask openai python-docx pdfminer.six python-dotenv pyyaml requests flask-cors >/dev/null 2>&1
fi

# Create settings-local.yaml with offline-friendly defaults
if [ ! -f "settings-local.yaml" ]; then
  echo "[*] Création de settings-local.yaml..."
  cat > settings-local.yaml << EOF
provider: offline
model: local
embedding_model: none
top_k: 5
timeout_s: 30
temperature: 0.1
EOF
fi

# Manage .env file for offline operation
if [ ! -f ".env" ]; then
  echo "[*] Création du fichier .env pour le mode hors-ligne..."
  cat > .env << EOF
SC_PROFILE=offline
LLM_PROVIDER=offline
TRANSFORMERS_OFFLINE=1
TOKENIZERS_PARALLELISM=false
EOF
else
  # Append missing offline-friendly keys only
  if ! grep -q "TRANSFORMERS_OFFLINE" .env; then
    echo "TRANSFORMERS_OFFLINE=1" >> .env
  fi
  if ! grep -q "TOKENIZERS_PARALLELISM" .env; then
    echo "TOKENIZERS_PARALLELISM=false" >> .env
  fi
fi

# Find available port from 5000 to 5010
PORT=5000
while [ $PORT -le 5010 ]; do
  if is_port_available $PORT; then
    echo "[*] Port $PORT disponible, démarrage du serveur..."
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
if command_exists open; then
  (sleep 3 && open "http://127.0.0.1:$PORT") &
elif command_exists xdg-open; then
  (sleep 3 && xdg-open "http://127.0.0.1:$PORT") &
else
  echo "[*] Ouvrez http://127.0.0.1:$PORT dans votre navigateur"
fi

echo "[*] Démarrage de Studying Coach sur le port $PORT..."
python3 app.py
