#!/bin/bash
# test_oneclick.sh - Test automatisé du système one-click
# Usage: ./test_oneclick.sh

set -e

echo "==== TEST ONE-CLICK FUNCTIONALITY ===="
echo "$(date)"
echo

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_test() { echo -e "🧪 TEST: $1"; }
print_ok() { echo -e "${GREEN}✓ PASS:${NC} $1"; }
print_fail() { echo -e "${RED}✗ FAIL:${NC} $1"; }
print_warn() { echo -e "${YELLOW}⚠ WARN:${NC} $1"; }

TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    print_test "$test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        print_ok "$test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        print_fail "$test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# 1. Test script presence
print_test "Scripts de lancement présents"
if [ -f "start-coach.command" ] && [ -f "start-coach.sh" ] && [ -f "start-coach.bat" ]; then
    print_ok "Scripts de lancement présents"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_fail "Scripts de lancement manquants"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 2. Test script permissions
print_test "Permissions des scripts"
if [ -x "start-coach.command" ] && [ -x "start-coach.sh" ]; then
    print_ok "Permissions des scripts"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_fail "Permissions des scripts"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 3. Test diagnostic tools
run_test "Diagnostic tools présents" "[ -f 'tools/doctor.sh' ] && [ -f 'tools/smoke.sh' ]"
run_test "Diagnostic tools exécutables" "[ -x 'tools/doctor.sh' ] && [ -x 'tools/smoke.sh' ]"

# 4. Test core files
run_test "Flask app présente" "[ -f 'app.py' ]"
run_test "Templates présents" "[ -f 'templates/index.html' ]"
run_test "Assets statiques présents" "[ -f 'static/app.js' ] && [ -f 'static/style.css' ]"

# 5. Test Python requirements
print_test "Requirements.txt valide"
if [ -f "requirements.txt" ] && [ -s "requirements.txt" ]; then
    print_ok "Requirements.txt valide"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_fail "Requirements.txt valide"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 6. Test enhanced functionality
run_test "Mode dégradé supporté" "[ -f 'static/degraded_mode.js' ]"
run_test "Base URL dynamique" "grep -q '__BASE_URL__.*window.location' templates/index.html"
run_test "Debug tools présents" "[ -f 'static/debug.css' ] && [ -f 'static/dom_probe.js' ]"

# 7. Test README
run_test "Documentation one-click" "[ -f 'README_ONE_CLICK.md' ]"

# 8. Test configuration files
print_test "Fichiers de configuration"
if [ -f ".env.example" ] || [ -f "settings-local.yaml" ]; then
    print_ok "Fichiers de configuration"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_warn "Fichiers de configuration par défaut créés à l'exécution"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# 9. Test structure directories
run_test "Structure directories" "[ -d 'tools' ] && [ -d 'static' ] && [ -d 'templates' ] && [ -d 'services' ]"

# 10. Test JavaScript modules
print_test "Modules JavaScript essentiels"
js_modules=("baseurl.js" "ui_error_overlay.js" "dom_probe.js" "degraded_mode.js")
missing=0
for module in "${js_modules[@]}"; do
    if [ ! -f "static/$module" ]; then
        missing=$((missing + 1))
    fi
done

if [ $missing -eq 0 ]; then
    print_ok "Modules JavaScript essentiels"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_fail "Modules JavaScript essentiels ($missing manquants)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Summary
echo
echo "==== RÉSULTATS DES TESTS ===="
echo "Tests passés: $TESTS_PASSED"
echo "Tests échoués: $TESTS_FAILED"
echo "Total: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}"
    echo "🎉 TOUS LES TESTS PASSENT!"
    echo "Le système one-click est prêt à l'emploi."
    echo -e "${NC}"
    exit 0
else
    echo -e "${RED}"
    echo "❌ $TESTS_FAILED test(s) ont échoué."
    echo "Vérifiez les éléments manquants avant le déploiement."
    echo -e "${NC}"
    exit 1
fi