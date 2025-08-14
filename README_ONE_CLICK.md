# 🚀 Coach de Révision - Lancement en 1 Clic

## 🎯 Démarrage Ultra-Rapide

### macOS / Linux
```bash
./start-coach.command
```
ou
```bash
./start-coach.sh
```

### Windows
Double-cliquez sur `start-coach.bat` ou exécutez dans PowerShell/CMD:
```cmd
start-coach.bat
```

## ✨ Ce qui se passe automatiquement

1. **Vérification système** - Python3, dépendances
2. **Installation automatique** - Environnement virtuel + packages
3. **Configuration Ollama** - Détection et téléchargement des modèles IA
4. **Port libre** - Sélection automatique (5000-5010)
5. **Lancement** - Serveur + ouverture navigateur
6. **Mode dégradé** - Fonctionne même sans Ollama

## 🛠️ Diagnostic et Dépannage

### Scripts de diagnostic
```bash
# Diagnostic complet du système
./tools/doctor.sh

# Tests de fumée (endpoints)
./tools/smoke.sh
```

### Modes de fonctionnement

#### Mode Complet (Ollama + Modèles)
- ✅ Analyse IA avancée
- ✅ Amélioration de texte par LLM
- ✅ Génération de fiches intelligente
- ✅ Embeddings sémantiques

#### Mode Dégradé (Sans Ollama)
- ✅ Analyse hors-ligne des documents
- ✅ Extraction de concepts automatique  
- ✅ Génération de QCM/QA basique
- ⚠️ Amélioration IA simulée (mock)

## 📋 Fonctionnalités Disponibles

### 📚 Import et Analyse
- **Drag & Drop** - PDF, DOCX, TXT, MD
- **Analyse automatique** - Structure, concepts, résumé
- **OCR** - Extraction depuis images (si Tesseract installé)

### 🎯 Système de Révision
- **Flashcards adaptatifs** - Algorithme de répétition espacée
- **QCM intelligents** - Questions à choix multiples
- **Exercices pratiques** - Textes à trous, associations
- **Pomodoro intégré** - Sessions chronométrées

### 🤖 IA Optionnelle
- **Amélioration de contenu** - Via Ollama/LLM
- **Génération de questions** - Contextuelle et pertinente
- **Résumés automatiques** - Extraction des points clés

## 🔧 Configuration Avancée

### Variables d'environnement (.env)
```bash
# Ollama
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=llama3:8b

# Développement
CORS_ORIGINS=http://127.0.0.1:5000,http://localhost:5000
FLASK_ENV=development
DEBUG=true
```

### Configuration LLM (settings-local.yaml)
```yaml
provider: ollama
model: llama3:8b
embedding_model: nomic-embed-text
timeout_s: 60
temperature: 0.1
```

## 🐛 Debug et Développement

### Outils de debug intégrés
- **Mode debug CSS** - Touche `~` pour visualiser zones cliquables
- **Overlay d'erreur JS** - Affichage automatique des erreurs
- **Sonde DOM** - Inspection interactive des éléments
- **Monitor de performance** - Suivi des métriques temps réel

### Endpoints utiles
```
GET  /api/health          # Santé générale
GET  /api/health/llm      # Santé LLM/Ollama  
POST /api/upload          # Upload fichier
POST /api/improve         # Amélioration IA
POST /api/offline/analyze # Analyse hors-ligne
```

## 🚨 Dépannage Courant

### "Python non trouvé"
- **macOS/Linux**: `brew install python3` ou gestionnaire de paquets
- **Windows**: Télécharger depuis [python.org](https://python.org/downloads/) et cocher "Add to PATH"

### "Ollama non accessible" 
- **Installation**: [ollama.ai/download](https://ollama.ai/download)
- **Démarrage**: `ollama serve` dans un terminal séparé
- **Modèles**: `ollama pull llama3:8b && ollama pull nomic-embed-text`

### "Port occupé"
- Le script trouve automatiquement un port libre (5000-5010)
- Forcer un port: `PORT=5005 ./start-coach.sh`

### Interface ne s'affiche pas
- Vérifier dans la console du navigateur (F12)
- Activer debug mode: touche `~` sur la page
- Consulter les logs: `logs/app.log`

## 📈 Performance et Optimisation

### Recommandations système
- **RAM**: 4GB minimum, 8GB recommandé pour Ollama
- **Stockage**: 10GB libres pour modèles Ollama
- **Navigateur**: Chrome/Firefox/Safari récent

### Optimisations automatiques
- Cache intelligent des réponses LLM
- Compression des assets statiques
- Chargement différé des scripts
- Service Worker désactivé en dev

## 🔒 Sécurité et Données

### Protection des données
- **Traitement local** - Aucune donnée envoyée à des serveurs externes
- **Modèles locaux** - Ollama fonctionne entièrement hors-ligne
- **Cache sécurisé** - Données temporaires chiffrées
- **CORS limité** - Origines restreintes en production

---

## 💡 Support et Contribution

- **Issues**: Utiliser le système de tickets GitHub
- **Debug**: Joindre la sortie de `./tools/doctor.sh`
- **Logs**: Fichier `logs/app.log` pour les erreurs détaillées
- **Tests**: Exécuter `./tools/smoke.sh` pour valider le fonctionnement