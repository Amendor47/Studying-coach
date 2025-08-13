#!/bin/bash
# smoke.sh - Tests de fumée pour Study Coach
# Lance l'application et teste les endpoints critiques

set -e

echo "🔥 STUDY COACH - TESTS DE FUMÉE"
echo "==============================="

# Variables de configuration  
PORT=${PORT:-5000}
PYTHON_CMD=${PYTHON_CMD:-python}
BASE_URL="http://127.0.0.1:$PORT"
APP_SCRIPT=${APP_SCRIPT:-app.py}
TIMEOUT=30

# Compteurs
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Fonctions utilitaires
log_info() { echo "ℹ️  $1"; }
log_warn() { echo "⚠️  $1"; }
log_error() { echo "❌ $1"; }
log_ok() { echo "✅ $1"; }

test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="${4:-200}"
    local curl_args="${5:-}"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -n "🧪 Test $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" --connect-timeout 5 --max-time 10 \
                   "$BASE_URL$endpoint" 2>/dev/null || echo "HTTPSTATUS:000")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" --connect-timeout 5 --max-time 10 \
                   -X POST $curl_args "$BASE_URL$endpoint" 2>/dev/null || echo "HTTPSTATUS:000")  
    fi
    
    http_status=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    
    if [ "$http_status" = "$expected_status" ]; then
        echo "OK ($http_status)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo "KO (attendu: $expected_status, reçu: $http_status)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Fonction pour démarrer l'application
start_app() {
    log_info "Démarrage de l'application..."
    
    # Vérifier si l'app tourne déjà
    if curl -s --connect-timeout 2 "$BASE_URL/api/health" >/dev/null 2>&1; then
        log_info "Application déjà démarrée sur $BASE_URL"
        return 0
    fi
    
    # Chercher le script de démarrage
    if [ -f "start.sh" ]; then
        log_info "Utilisation de start.sh"
        nohup bash start.sh >/dev/null 2>&1 &
    elif [ -f "$APP_SCRIPT" ]; then
        log_info "Démarrage direct avec $PYTHON_CMD $APP_SCRIPT"
        nohup $PYTHON_CMD "$APP_SCRIPT" >/dev/null 2>&1 &
    else
        log_error "Aucun script de démarrage trouvé"
        return 1
    fi
    
    APP_PID=$!
    log_info "Application démarrée (PID: $APP_PID)"
    
    # Attendre que l'application soit prête
    echo -n "⏳ Attente du démarrage"
    for i in {1..30}; do
        if curl -s --connect-timeout 1 "$BASE_URL/api/health" >/dev/null 2>&1; then
            echo " OK"
            log_ok "Application prête sur $BASE_URL"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo " TIMEOUT"
    log_error "Timeout - l'application n'a pas démarré en $TIMEOUT secondes"
    return 1
}

# Créer un fichier test temporaire
create_test_file() {
    echo "# Fichier test pour Study Coach

## Introduction
Ceci est un test de document pour vérifier l'upload.

### Section 1
Contenu de test avec quelques concepts clés.

### Section 2  
Plus de contenu pour analyser." > /tmp/test_document.md

    log_info "Fichier test créé: /tmp/test_document.md"
}

# Démarrer l'application
if ! start_app; then
    log_error "Impossible de démarrer l'application - abandon des tests"
    exit 1
fi

# Créer fichier de test
create_test_file

echo -e "\n🧪 EXÉCUTION DES TESTS"
echo "====================="

# Test 1: Health endpoint
test_endpoint "Health" "GET" "/api/health" 200

# Test 2: LLM Health (peut échouer si Ollama absent)
if test_endpoint "LLM Health" "GET" "/api/health/llm" 200; then
    log_info "LLM endpoint opérationnel"
else
    log_warn "LLM endpoint en erreur - vérifier Ollama"
fi

# Test 3: Upload de fichier
test_endpoint "Upload fichier" "POST" "/api/upload" 200 "-F \"file=@/tmp/test_document.md\""

# Test 4: Amélioration de texte
test_endpoint "Amélioration texte" "POST" "/api/improve" 200 "-H \"Content-Type: application/json\" -d '{\"text\":\"ping test\"}'"

# Test 5: Analyse hors ligne
test_endpoint "Analyse offline" "POST" "/api/offline/analyze" 200 "-H \"Content-Type: application/json\" -d '{\"text\":\"Concept important à retenir\"}'"

# Test 6: Récupération des thèmes
test_endpoint "Thèmes" "GET" "/api/themes" 200

# Test 7: Interface principale
test_endpoint "Interface" "GET" "/" 200

echo -e "\n📊 RÉSULTATS DES TESTS"
echo "====================="
echo "Total: $TESTS_TOTAL tests"
echo "Réussis: $TESTS_PASSED tests" 
echo "Échecs: $TESTS_FAILED tests"

# Nettoyage
rm -f /tmp/test_document.md

if [ $TESTS_FAILED -eq 0 ]; then
    log_ok "Tous les tests sont passés - application opérationnelle !"
    exit 0
else
    log_error "$TESTS_FAILED test(s) ont échoué"
    echo -e "\n🔧 ACTIONS RECOMMANDÉES:"
    echo "  1. Vérifier les logs de l'application"
    echo "  2. Exécuter tools/doctor.sh pour un diagnostic complet"
    echo "  3. Vérifier la configuration Ollama si LLM en erreur"
    echo "  4. Vérifier les dépendances Python"
    exit 1
fi