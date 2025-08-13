#!/bin/bash
# run_front_debug.sh - Lancer l'application avec outils de debug frontend

echo "🐛 STUDY COACH - DEBUG FRONTEND"
echo "==============================="

# Variables de configuration
PORT=${PORT:-5000}
BASE_URL="http://127.0.0.1:$PORT"

echo "📋 Instructions de debug:"
echo "  1. L'application va se lancer sur $BASE_URL"
echo "  2. Appuyez sur la touche ~ (backquote) pour activer la sonde DOM"
echo "  3. En mode debug:"
echo "     - Survolez les éléments pour voir leurs propriétés"
echo "     - Ctrl+Clic sur un élément pour actions de correction"
echo "     - Utilisez les boutons de debug en bas à droite"
echo "  4. Copiez les messages de la console pour reporting"
echo ""

# Démarrer l'application
echo "🚀 Démarrage de l'application..."

if [ -f "start.sh" ]; then
    echo "   Utilisation de start.sh"
    bash start.sh &
elif [ -f "app.py" ]; then
    echo "   Démarrage avec Python"
    python app.py &
else
    echo "❌ Aucun script de démarrage trouvé"
    exit 1
fi

APP_PID=$!
echo "   Application démarrée (PID: $APP_PID)"

# Attendre que l'application soit prête
echo "⏳ Attente du démarrage..."
for i in {1..30}; do
    if curl -s --connect-timeout 1 "$BASE_URL/api/health" >/dev/null 2>&1; then
        echo "✅ Application prête"
        break
    fi
    sleep 1
done

# Ouvrir le navigateur (si disponible)
if command -v xdg-open >/dev/null 2>&1; then
    echo "🌐 Ouverture dans le navigateur..."
    xdg-open "$BASE_URL" 2>/dev/null &
elif command -v open >/dev/null 2>&1; then
    echo "🌐 Ouverture dans le navigateur..."
    open "$BASE_URL" 2>/dev/null &
else
    echo "🌐 Ouvrez manuellement: $BASE_URL"
fi

echo ""
echo "🔧 OUTILS DE DEBUG DISPONIBLES:"
echo "  • DOM Probe (touche ~): Analyse interactive des éléments"
echo "  • Error Overlay: Affichage des erreurs JS en temps réel"
echo "  • Base URL handler: Normalisation automatique des fetch"
echo "  • Debug CSS: Classes utilitaires et visualisations"
echo ""

echo "📝 TESTS À EFFECTUER:"
echo "  1. Glisser-déposer un fichier sur la zone d'upload"
echo "  2. Cliquer sur tous les boutons et vérifier les réponses"
echo "  3. Activer la sonde DOM (touche ~) et analyser les overlays"
echo "  4. Vérifier les appels fetch dans les DevTools > Network"
echo "  5. Noter toute erreur dans la console"
echo ""

echo "⏹️  Appuyez sur Ctrl+C pour arrêter l'application"

# Attendre l'arrêt
wait $APP_PID