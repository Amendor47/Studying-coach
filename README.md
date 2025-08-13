# Studying Coach

Coach d'étude personnel avec intelligence artificielle et fonctionnalités hors-ligne.

## ✨ Nouvelles Fonctionnalités

### 🖥️ Application Desktop Standalone  
- **Exécutable autonome**: Lance directement sur votre ordinateur sans navigateur requis
- **Interface native**: Utilise pywebview pour une expérience desktop authentique
- **Mode hors-ligne complet**: Fonctionne entièrement sans connexion internet
- **Lancement automatique**: Scripts intelligents qui détectent et utilisent la meilleure méthode

### 🌐 Mode Hors-ligne Renforcé
- **Analyse sans IA**: Générateur de fiches robuste basé sur l'analyse de texte
- **Pas de dépendances réseau**: Toutes les fonctionnalités de base disponibles offline
- **Modèles locaux optionnels**: Support pour Ollama, GPT4All, et llama.cpp
- **Basculement gracieux**: Fallback automatique quand l'IA n'est pas disponible

### 🎯 Interface Améliorée
- **Drag & Drop avancé**: Réorganisation des cartes sur desktop et mobile
- **Persistence automatique**: L'ordre des cartes est sauvegardé automatiquement
- **Accessibilité clavier**: Ctrl+↑/↓ pour réorganiser les cartes
- **Animations fluides**: Feedback visuel avec indicateurs de glisser-déposer

### 🤖 IA Locale Intégrée
- **Support multi-providers**: Ollama, GPT4All, llama.cpp avec fallback automatique
- **Streaming en temps réel**: Génération de texte via Server-Sent Events
- **Monitoring de santé**: Endpoint `/api/health` pour vérifier la disponibilité
- **Configuration flexible**: Variables d'environnement pour personnalisation

## 🚀 Démarrage Rapide

### 🖥️ Application Desktop (Recommandé)

**Option 1: Utiliser l'exécutable précompilé**
1. Téléchargez `StudyCoach.exe` (Windows) ou `StudyCoach` (macOS/Linux)
2. Double-cliquez pour lancer l'application
3. L'interface s'ouvre automatiquement - pas de navigateur requis!

**Option 2: Compiler depuis les sources**
```bash
git clone <repo-url>
cd Studying-coach
pip install -r requirements-desktop.txt
python build.py desktop
./dist/StudyCoach  # ou StudyCoach.exe sur Windows
```

### 🌐 Mode Navigateur (Développement)

**Lanceurs par plateforme:**
- **Cross-platform:** `./start-coach.command` (Auto-détection OS)
- **Windows:** `Start-Coach.bat`  
- **macOS/Linux:** `./start-coach.command`

**Démarrage manuel:**
```bash
git clone <repo-url>
cd Studying-coach
pip install -r requirements.txt
python app.py
```

## 🛠️ Compilation

### Versions disponibles

```bash
# Compiler les deux versions
python build.py

# Version desktop uniquement  
python build.py desktop

# Version web uniquement
python build.py web
```

### Résultats de compilation
- **StudyCoach** / **StudyCoach.exe**: Application desktop avec GUI native
- **StudyCoach-Web** / **StudyCoach-Web.exe**: Version serveur web autonome

## 🔧 Configuration

### Mode Hors-ligne (par défaut)
```bash
# Variables automatiquement configurées
SC_PROFILE=offline
LLM_PROVIDER=offline  
TRANSFORMERS_OFFLINE=1
TOKENIZERS_PARALLELISM=false
```

### Mode IA Locale (Ollama)
```bash
# Installer Ollama: https://ollama.com/download
ollama pull llama3:8b
ollama pull nomic-embed-text
ollama serve

# Configuration
LLM_PROVIDER=ollama
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=llama3:8b
```

### Mode IA Cloud (OpenAI)
```bash
OPENAI_API_KEY=your-key-here
LLM_PROVIDER=openai
```

## 📚 Utilisation

### Interface Desktop
1. Lancez `StudyCoach` 
2. L'interface s'ouvre dans une fenêtre native
3. Importez vos documents (PDF, DOCX, TXT, Markdown)
4. Cliquez **Analyser** pour générer des fiches automatiquement
5. Utilisez **Améliorer via IA** si vous avez configuré un modèle local/cloud

### Interface Web  
1. Lancez `./start-coach.command` ou `Start-Coach.bat`
2. L'application s'ouvre automatiquement dans votre navigateur
3. Même fonctionnalités que l'interface desktop

### Fonctionnalités Principales
- **Import intelligent**: Analyse automatique de documents
- **Génération de fiches**: QCM, Vrai/Faux, QA, Cloze tests
- **Révisions espacées**: Algorithme SM-2 pour optimiser la mémorisation
- **Recherche web**: Enrichissement via DuckDuckGo (optionnel)  
- **Export**: CSV, PDF, DOCX
- **Statistiques**: Suivi des performances et analytics

## 🔄 Fonctionnalités Avancées

### API REST Complète
- `POST /api/upload`: Import de documents
- `GET /api/due`: Cartes à réviser  
- `POST /api/flashcards/reorder`: Réorganisation drag & drop
- `POST /api/ai/generate`: Génération IA avec streaming
- `GET /api/health`: Monitoring système et IA

### Compatibilité Mobile
- Interface responsive adaptée aux écrans tactiles
- Support des gestes (glisser-déposer)
- Retour haptique sur appareils compatibles

### Sécurité et Performance
- Headers de sécurité (CSP, XSS Protection)
- Cache intelligent avec ETags
- Compression automatique des assets
- Service Worker pour fonctionnement hors-ligne

## 🐞 Dépannage

### L'application ne démarre pas
```bash
# Vérifier Python
python3 --version

# Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall

# Nettoyer le cache
rm -rf .venv __pycache__ cache
```

### Problèmes d'IA
```bash
# Vérifier la santé de l'IA
curl http://127.0.0.1:5000/api/health

# Mode debug pour diagnostics
FLASK_DEBUG=1 python app.py
```

### Erreurs de port
Les lanceurs détectent automatiquement un port libre (5000-5010). En cas de problème:
```bash
export PORT=5001  # ou autre port libre
python app.py
```

## 📋 Pré-requis

### Application Desktop
- **Python 3.8+** (pour compilation depuis sources)
- **Aucune dépendance** (pour les exécutables précompilés)

### Mode Développement
- **Python 3.8+**
- **pip** 
- **Connexion internet** (installation des dépendances uniquement)

### IA Locale (Optionnel)
- **Ollama**: Recommandé, plus facile à installer
- **GPT4All**: Alternative avec modèles intégrés  
- **llama.cpp**: Pour usage avancé

## 🤝 Contributions

Les contributions sont bienvenues! Domaines prioritaires:
- Nouveaux formats d'import (PowerPoint, etc.)
- Améliorations de l'interface desktop
- Support de nouveaux providers IA
- Tests et documentation

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
