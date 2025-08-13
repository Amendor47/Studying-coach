# Study Coach - Guide de Dépannage

## 🚀 Démarrage Rapide (1 Commande)

```bash
# Démarrage complet avec diagnostic
./tools/doctor.sh && python app.py
```

Si ça ne fonctionne pas, suivez les étapes ci-dessous.

---

## 📋 Checklist de Diagnostic

### 1. Diagnostic Système
```bash
./tools/doctor.sh
```
**Ce script vérifie automatiquement :**
- ✅ Python et dépendances
- ✅ Disponibilité des ports (5000-5010)
- ✅ Installation Ollama + modèles 
- ✅ Fichiers critiques
- ✅ Santé des endpoints

### 2. Tests de Fumée
```bash
./tools/smoke.sh
```
**Tests end-to-end automatiques :**
- ✅ Démarrage application
- ✅ Endpoints API (/api/health, /api/upload, etc.)
- ✅ Upload de fichiers
- ✅ Analyse de texte

### 3. Tests HTTP (pytest)
```bash
python tests/smoke_http.py
```
**Tests approfondis avec pytest :**
- ✅ Tous les endpoints
- ✅ Upload multipart  
- ✅ Ressources statiques
- ✅ Interface HTML

---

## 🐛 Problèmes Fréquents

### Application ne démarre pas

**Erreur: `Port 5000 already in use`**
```bash
# L'app détecte automatiquement un port libre (5000→5001→5002...)
# Ou forcer un port spécifique:
PORT=5005 python app.py
```

**Erreur: `ModuleNotFoundError`**
```bash
# Installer les dépendances minimales
pip install flask flask-cors python-dotenv requests beautifulsoup4

# Ou installation complète
pip install -r requirements.txt
```

### Interface Bloquée / Clics Sans Effet

**1. Activer la Sonde DOM (touche `~`)**
- Survole les éléments pour voir leurs propriétés CSS
- Identifie les overlays bloquants
- Ctrl+Clic sur un élément pour actions de correction

**2. Vérifier la Console Navigateur**
```javascript
// Erreurs courantes à surveiller:
// - TypeError: Cannot read property of null
// - Failed to fetch 
// - Service worker errors
```

**3. Désactiver le Service Worker**
```javascript
// Dans la console du navigateur:
navigator.serviceWorker.getRegistrations().then(function(registrations) {
    for(let registration of registrations) {
        registration.unregister();
    }
});
```

**4. Cache du Navigateur**
```bash
# Vider le cache: Ctrl+Shift+R (Chrome/Firefox)
# Ou mode navigation privée
```

### Base URL / Fetch Échouent

**Erreur: `Failed to fetch`**
- ✅ L'app normalise automatiquement les URLs avec `baseurl.js`
- ✅ Vérifier que l'application backend tourne
- ✅ Tester manuellement: `curl http://localhost:5000/api/health`

**Erreur CORS**
```bash
# En développement, CORS est permissif automatiquement
# Vérifier les logs au démarrage pour la config CORS
```

### Problèmes d'Overlays CSS

**Éléments non cliquables**
1. Activer la sonde DOM (`~`)
2. Utiliser le bouton "Fixer overlays" 
3. Ou manuellement en CSS :
```css
.problematic-overlay {
    pointer-events: none !important;
}
```

---

## 🔧 Outils de Debug Avancés

### Audit Frontend Automatique
```bash
# Détecter les bloqueurs d'interaction
python tools/audit_front.py

# Validation HTML
python tools/html_sanity.py
```

### Sonde DOM Interactive
- **Touche `~`** : Activer/désactiver le mode debug
- **Survol** : Voir propriétés CSS en temps réel
- **Ctrl+Clic** : Menu d'actions de correction
- **Boutons de debug** : 
  - Surligner éléments cliquables
  - Fixer overlays automatiquement  
  - Grille CSS
  - Mode contraste

### Debug Frontend Guidé
```bash
# Lance l'app avec instructions de debug
./tools/run_front_debug.sh
```

---

## 🌐 Configuration Ollama & Modèles

### Installation Ollama
```bash
# Linux/Mac:
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Télécharger depuis https://ollama.ai
```

### Modèles Recommandés
```bash
# Modèle principal (recommandé)
ollama pull llama3:8b

# Modèle léger (fallback)  
ollama pull llama3.2:3b

# Embeddings (pour recherche sémantique)
ollama pull nomic-embed-text
```

### Test Ollama
```bash
# Vérifier qu'Ollama fonctionne
curl http://localhost:11434/api/tags

# Test d'un modèle
ollama run llama3:8b "Bonjour"
```

---

## 🔄 Variables d'Environnement

### Configuration du Modèle
```bash
# Fichier .env
MODEL_NAME=llama3.2:3b  # Modèle plus léger par défaut
DEBUG=1                 # Mode debug activé
PORT=5000              # Port de l'application
CORS_ORIGINS=*         # CORS permissif (dev uniquement)
```

### Mode de Fallback
```bash
# L'application utilise automatiquement des fallbacks:
# 1. MODEL_NAME (env) → llama3:8b → llama3.2:3b → llama3.2:1b → gemma:2b
# 2. Port 5000 → 5001 → 5002... (auto-détection)
# 3. Analyse avancée ON → OFF si dépendances manquantes
```

---

## 📊 Logs & Monitoring

### Fichiers de Logs
```bash
# Logs de l'application
tail -f logs/app.log

# Logs structurés avec timestamps
# Format: [timestamp] - [module] - [level] - [message]
```

### Métriques de Performance
- **Cache hit ratio** : Affiché dans l'interface
- **Temps de réponse API** : Monitored automatiquement  
- **Erreurs JS** : Capturées par l'error overlay

---

## 🆘 Dépannage d'Urgence

### Interface Complètement Cassée
1. **Mode Secours** : L'app détecte les erreurs d'init et affiche une interface de fallback
2. **URL directe** : `http://localhost:5000/` → interface simple garantie
3. **Reset complet** : Supprimer `data/` et `cache/`, redémarrer

### Application qui Crash au Démarrage
```bash
# Debug mode avec stack traces complètes
DEBUG=1 python app.py

# Ou diagnostic complet
./tools/doctor.sh > diagnostic.txt 2>&1
```

### Performance Dégradée
```bash
# Vider le cache de performance
rm -rf cache/
rm -rf __pycache__/

# Redémarrer avec cache vide
python app.py
```

---

## 📞 Obtenir de l'Aide

### Informations à Collecter
```bash
# Rapport complet pour support
echo "=== SYSTEM INFO ===" > debug_report.txt
./tools/doctor.sh >> debug_report.txt 2>&1
echo -e "\n=== LOGS ===" >> debug_report.txt  
tail -50 logs/app.log >> debug_report.txt 2>&1
echo -e "\n=== SMOKE TESTS ===" >> debug_report.txt
./tools/smoke.sh >> debug_report.txt 2>&1
```

### Diagnostic Rapide
```bash
# Une ligne pour tester tout
./tools/doctor.sh && ./tools/smoke.sh && python tests/smoke_http.py
```

---

## ✅ Checklist de Validation

Avant de signaler un bug, vérifier :

- [ ] `./tools/doctor.sh` → exit code 0
- [ ] `./tools/smoke.sh` → tous les tests OK
- [ ] Console navigateur → pas d'erreurs JS
- [ ] Sonde DOM (`~`) → éléments cliquables visibles
- [ ] Interface secours → fonctionne si main UI cassée
- [ ] Logs → pas d'erreurs critiques répétitives

**Si tout est ✅ mais ça ne marche pas, c'est probablement un vrai bug !**