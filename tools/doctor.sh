#!/bin/bash
# doctor.sh - Système de diagnostic pour Study Coach
# Vérifie les dépendances, ports, services et santé générale

set -e

echo "🩺 STUDY COACH - DIAGNOSTIC SYSTÈME"
echo "=================================="

# Variables de configuration
PORT=${PORT:-5000}
PYTHON_CMD=${PYTHON_CMD:-python}
VENV_PATH=${VENV_PATH:-venv}

# Codes de retour
GLOBAL_STATUS=0
WARNINGS=0
ERRORS=0

# Fonctions utilitaires
log_info() { echo "ℹ️  $1"; }
log_warn() { echo "⚠️  $1"; WARNINGS=$((WARNINGS + 1)); }
log_error() { echo "❌ $1"; ERRORS=$((ERRORS + 1)); GLOBAL_STATUS=1; }
log_ok() { echo "✅ $1"; }

# 1. Vérifier Python et environnement
echo -e "\n📍 ENVIRONNEMENT PYTHON"
if command -v $PYTHON_CMD >/dev/null 2>&1; then
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    log_ok "Python trouvé: $PYTHON_VERSION"
else
    log_error "Python non trouvé avec la commande: $PYTHON_CMD"
fi

# Vérifier l'environnement virtuel (optionnel)
if [ -d "$VENV_PATH" ]; then
    log_info "Environnement virtuel détecté: $VENV_PATH"
else
    log_warn "Aucun environnement virtuel dans $VENV_PATH"
fi

# 2. Vérifier les dépendances Python critiques
echo -e "\n📍 DÉPENDANCES PYTHON"
check_package() {
    local pkg_name="$1"
    local import_name="$2"
    if $PYTHON_CMD -c "import $import_name" 2>/dev/null; then
        log_ok "Package disponible: $pkg_name"
    else
        log_error "Package manquant: $pkg_name"
    fi
}

check_package "flask" "flask"
check_package "flask-cors" "flask_cors"
check_package "python-dotenv" "dotenv"
check_package "requests" "requests"
check_package "beautifulsoup4" "bs4"

# 3. Vérifier port 5000
echo -e "\n📍 PORTS ET SERVICES"
if command -v lsof >/dev/null 2>&1; then
    LSOF_OUTPUT=$(lsof -ti:$PORT 2>/dev/null || true)
    if [ -n "$LSOF_OUTPUT" ]; then
        log_warn "Port $PORT occupé (PID: $LSOF_OUTPUT). Actions suggérées: kill $LSOF_OUTPUT"
    else
        log_ok "Port $PORT disponible"
    fi
else
    log_warn "lsof non disponible - impossible de vérifier le port $PORT"
fi

# 4. Vérifier Ollama (optionnel)
echo -e "\n📍 OLLAMA (LLM LOCAL)"
if command -v ollama >/dev/null 2>&1; then
    OLLAMA_VERSION=$(ollama --version 2>&1 | head -n1 || echo "version inconnue")
    log_ok "Ollama installé: $OLLAMA_VERSION"
    
    # Vérifier les modèles critiques
    REQUIRED_MODELS=("llama3:8b" "nomic-embed-text")
    for model in "${REQUIRED_MODELS[@]}"; do
        if ollama list 2>/dev/null | grep -q "$model"; then
            log_ok "Modèle disponible: $model"
        else
            log_warn "Modèle manquant: $model. Action suggérée: ollama pull $model"
        fi
    done
else
    log_warn "Ollama non installé - fonctionnalités IA limitées"
    log_info "Installation: https://ollama.ai/download"
fi

# 5. Test de santé du backend (si disponible)
echo -e "\n📍 SANTÉ BACKEND"
BASE_URL="http://127.0.0.1:$PORT"

# Test /api/health
if curl -s --connect-timeout 3 "$BASE_URL/api/health" >/dev/null 2>&1; then
    log_ok "Endpoint /api/health accessible"
else
    log_warn "Backend non démarré ou endpoint /api/health inaccessible"
    log_info "Démarrer avec: python app.py ou ./start.sh"
fi

# Test /api/health/llm  
if curl -s --connect-timeout 3 "$BASE_URL/api/health/llm" >/dev/null 2>&1; then
    log_ok "Endpoint /api/health/llm accessible"
else
    log_warn "LLM endpoint non accessible - vérifier Ollama"
fi

# 6. Vérifications des fichiers critiques
echo -e "\n📍 FICHIERS SYSTÈME"
CRITICAL_FILES=("app.py" "templates/index.html" "static/app.js")

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_ok "Fichier trouvé: $file"
    else
        log_error "Fichier manquant: $file"
    fi
done

# Résumé final
echo -e "\n📋 RÉSUMÉ DIAGNOSTIC"
echo "=================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    log_ok "Système entièrement opérationnel"
elif [ $ERRORS -eq 0 ]; then
    log_warn "Système opérationnel avec $WARNINGS avertissement(s)"
else
    log_error "Système avec $ERRORS erreur(s) critique(s) et $WARNINGS avertissement(s)"
fi

echo -e "\n🚀 ACTIONS RECOMMANDÉES:"
if [ $ERRORS -gt 0 ]; then
    echo "  1. Installer les packages Python manquants: pip install -r requirements.txt"
    echo "  2. Vérifier les fichiers critiques manquants"
fi
if [ $WARNINGS -gt 0 ]; then
    echo "  3. Installer Ollama pour les fonctionnalités IA: https://ollama.ai"
    echo "  4. Télécharger les modèles: ollama pull llama3:8b && ollama pull nomic-embed-text"
    echo "  5. Libérer les ports occupés si nécessaire"
fi

echo -e "\nCode de retour: $GLOBAL_STATUS"
exit $GLOBAL_STATUS