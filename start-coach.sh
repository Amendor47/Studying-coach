#!/bin/bash
cd "$(dirname "$0")"
echo "==== Coach de Révision — LANCEUR ONE-CLICK LINUX/WSL ===="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() { echo -e "${BLUE}[STEP]${NC} $1"; }
print_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 1. DIAGNOSTIC INITIAL
print_step "Diagnostic initial du système..."
if [ -f "tools/doctor.sh" ]; then
    chmod +x tools/doctor.sh
    if ./tools/doctor.sh; then
        print_ok "Diagnostic initial passé"
    else
        print_warn "Diagnostic détecte des problèmes - continuation avec installation automatique"
    fi
fi

# 2. PYTHON ET ENVIRONNEMENT
print_step "Vérification Python3..."
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_VERSION=$(python --version 2>&1)
    if [[ $PYTHON_VERSION == *"Python 3"* ]]; then
        PYTHON_CMD="python"
    else
        print_error "Python 3 requis. Version détectée: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python3 requis. Installez via votre gestionnaire de paquets:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "  CentOS/RHEL:   sudo yum install python3 python3-venv python3-pip"
    echo "  Arch:          sudo pacman -S python python-pip"
    exit 1
fi
PYTHON_VERSION=$($PYTHON_CMD --version)
print_ok "Python trouvé: $PYTHON_VERSION"

# 3. ENVIRONNEMENT VIRTUEL
print_step "Configuration environnement virtuel..."
if [ ! -d ".venv" ]; then 
    print_step "Création de l'environnement virtuel..."
    $PYTHON_CMD -m venv .venv
fi
source .venv/bin/activate
print_ok "Environnement virtuel activé"

# 4. INSTALLATION DÉPENDANCES
print_step "Installation des dépendances Python..."
pip install --upgrade pip >/dev/null 2>&1
if [ -f requirements.txt ]; then 
    pip install -r requirements.txt --timeout 60 --retries 3 >/dev/null 2>&1 || {
        print_warn "Installation complète échouée, installation des packages essentiels..."
        pip install flask flask-cors python-dotenv requests pyyaml beautifulsoup4 python-docx >/dev/null 2>&1
    }
else 
    pip install flask flask-cors python-dotenv requests pyyaml beautifulsoup4 python-docx >/dev/null 2>&1
fi
print_ok "Dépendances installées"

# 5. CONFIGURATION
print_step "Configuration de l'application..."
# Create settings-local.yaml with Ollama defaults if missing
if [ ! -f "settings-local.yaml" ]; then
  print_step "Création de settings-local.yaml avec les paramètres Ollama par défaut..."
  cat > settings-local.yaml << EOF
provider: ollama
model: llama3:8b
embedding_model: nomic-embed-text
top_k: 5
timeout_s: 60
temperature: 0.1
EOF
fi

# Create .env if missing 
if [ ! -f ".env" ]; then
  print_step "Création fichier .env..."
  cat > .env << EOF
# Configuration Coach de Révision
OLLAMA_HOST=http://127.0.0.1:11434
CORS_ORIGINS=http://127.0.0.1:5000,http://localhost:5000,http://127.0.0.1:5001,http://localhost:5001
FLASK_ENV=development
DEBUG=true
EOF
else
  # Append missing keys only
  if ! grep -q "OLLAMA_HOST" .env; then
    echo "OLLAMA_HOST=http://127.0.0.1:11434" >> .env
  fi
  if ! grep -q "CORS_ORIGINS" .env; then
    echo "CORS_ORIGINS=http://127.0.0.1:5000,http://localhost:5000" >> .env
  fi
fi

# 6. INSTALLATION OLLAMA (optionnel)
print_step "Vérification Ollama..."
if command -v ollama >/dev/null 2>&1; then
    print_ok "Ollama trouvé"
    
    # Check if ollama is running
    if ! curl -s --connect-timeout 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
        print_step "Démarrage Ollama..."
        nohup ollama serve >/dev/null 2>&1 &
        sleep 3
    fi
    
    # Pull required models if not present (non-blocking for faster startup)
    if curl -s --connect-timeout 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
        models=$(curl -s --connect-timeout 5 http://127.0.0.1:11434/api/tags 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
        
        if ! echo "$models" | grep -q "llama3:8b"; then
            print_step "Téléchargement modèle llama3:8b en arrière-plan..."
            nohup ollama pull llama3:8b >/dev/null 2>&1 &
        else
            print_ok "Modèle llama3:8b disponible"
        fi
        
        if ! echo "$models" | grep -q "nomic-embed-text"; then
            print_step "Téléchargement modèle nomic-embed-text en arrière-plan..."
            nohup ollama pull nomic-embed-text >/dev/null 2>&1 &
        else
            print_ok "Modèle nomic-embed-text disponible"
        fi
    else
        print_warn "Ollama serveur non accessible - les modèles ne seront pas téléchargés"
    fi
else
    print_warn "Ollama non trouvé - installation recommandée:"
    echo "  curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  Ou via https://ollama.ai/download"
    print_warn "L'application fonctionnera en mode dégradé (sans IA)"
fi

# Function to check if a port is available
is_port_available() {
  if command -v lsof >/dev/null 2>&1; then
    ! lsof -i :$1 >/dev/null 2>&1
  elif command -v netstat >/dev/null 2>&1; then
    ! netstat -ln | grep :$1 >/dev/null 2>&1
  else
    # Fallback - assume port is available
    true
  fi
}

# 7. RECHERCHE PORT LIBRE
print_step "Recherche d'un port libre..."
PORT=5000
while [ $PORT -le 5010 ]; do
  if is_port_available $PORT; then
    print_ok "Port $PORT sélectionné"
    break
  fi
  PORT=$((PORT + 1))
done

if [ $PORT -gt 5010 ]; then
  print_warn "Tous les ports 5000-5010 occupés, utilisation du port 5000 par défaut"
  PORT=5000
fi

# Export PORT for the Flask app
export PORT=$PORT

# 8. TEST DE SANTÉ PRE-LANCEMENT
print_step "Vérification santé système..."
if [ -f "tools/doctor.sh" ]; then
    if ! ./tools/doctor.sh >/dev/null 2>&1; then
        print_warn "Diagnostic détecte des problèmes - voir ./tools/doctor.sh pour détails"
    fi
fi

# 9. DÉMARRAGE ET OUVERTURE NAVIGATEUR
print_step "Démarrage Coach de Révision sur http://127.0.0.1:$PORT"

# Open browser automatically after a short delay
if command -v xdg-open >/dev/null 2>&1; then
  (sleep 3 && xdg-open "http://127.0.0.1:$PORT") &
elif command -v firefox >/dev/null 2>&1; then
  (sleep 3 && firefox "http://127.0.0.1:$PORT") &
elif command -v google-chrome >/dev/null 2>&1; then
  (sleep 3 && google-chrome "http://127.0.0.1:$PORT") &
elif command -v chromium >/dev/null 2>&1; then
  (sleep 3 && chromium "http://127.0.0.1:$PORT") &
else
  echo "🌐 Ouvrez http://127.0.0.1:$PORT dans votre navigateur"
fi

echo ""
print_ok "======================================"
print_ok "🚀 COACH DE RÉVISION LANCÉ"
print_ok "📱 Interface: http://127.0.0.1:$PORT"
print_ok "🛠️  Diagnostic: ./tools/doctor.sh"
print_ok "🧪 Tests: ./tools/smoke.sh"  
print_ok "======================================"
echo ""

# Start the application
$PYTHON_CMD app.py