# Studying Coach - Desktop Application Quick Start

## 🖥️ Application Desktop

Studying Coach est maintenant disponible comme application desktop standalone!

### Avantages de la version desktop:
- ✅ **Pas de navigateur requis** - Interface native
- ✅ **Fonctionnement hors-ligne complet** - Aucune connexion internet nécessaire  
- ✅ **Démarrage en un clic** - Double-clic sur l'exécutable
- ✅ **Performance optimisée** - Pas de surcharge navigateur
- ✅ **Intégration système** - Icône dans la barre des tâches

### Installation

#### Option 1: Exécutable pré-compilé (Recommandé)
1. Téléchargez `StudyCoach.exe` (Windows) ou `StudyCoach` (macOS/Linux)
2. Double-cliquez pour lancer
3. L'application démarre immédiatement!

#### Option 2: Compiler depuis les sources
```bash
git clone <repo-url>
cd Studying-coach
pip install -r requirements-desktop.txt
python build.py desktop
./dist/StudyCoach
```

### Fonctionnalités

- 📚 **Import de documents**: PDF, DOCX, TXT, Markdown
- 🃏 **Génération automatique**: Flashcards, QCM, exercices  
- 🧠 **Révisions espacées**: Algorithme SM-2 optimisé
- 🔄 **Drag & Drop**: Réorganisation intuitive des cartes
- 📊 **Statistiques**: Suivi des performances
- 💾 **Export**: CSV, PDF, DOCX
- 🌐 **Mode hors-ligne**: Fonctionne sans internet

### Interface

L'application utilise:
- **pywebview** pour une interface native (recommandé)
- **tkinter** comme fallback si pywebview n'est pas disponible
- **Navigateur par défaut** en dernier recours

### Dépannage

**L'application ne démarre pas?**
```bash
# Vérifier les dépendances
pip install -r requirements-desktop.txt

# Mode debug
python desktop_app.py
```

**Port déjà utilisé?**
L'application trouve automatiquement un port libre (5000-5010)

**Interface ne s'affiche pas?**
L'application essaie successivement:
1. pywebview (interface native)
2. tkinter (interface basique)  
3. Navigateur par défaut

### Support

Pour toute question ou problème:
1. Vérifiez le fichier `logs/` pour les erreurs
2. Consultez la documentation complète dans README.md
3. Ouvrez une issue sur GitHub