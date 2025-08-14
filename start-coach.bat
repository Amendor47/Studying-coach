@echo off
setlocal ENABLEDELAYEDEXPANSION
echo ==== Coach de Révision — LANCEUR ONE-CLICK WINDOWS ====

REM 1) Diagnostic initial
if exist "tools\doctor.sh" (
  echo [STEP] Diagnostic initial du système...
  bash tools/doctor.sh >nul 2>&1
  if !errorlevel! equ 0 (
    echo [OK] Diagnostic initial passé
  ) else (
    echo [WARN] Diagnostic détecte des problèmes - continuation avec installation automatique
  )
)

REM 2) Vérif Python
echo [STEP] Vérification Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python introuvable. Installez depuis https://www.python.org/downloads/
  echo [INFO] Assurez-vous de cocher "Add Python to PATH" pendant l'installation
  pause
  exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python trouvé: !PYTHON_VERSION!

REM 3) Création/activation environnement virtuel
echo [STEP] Configuration environnement virtuel...
if not exist .venv (
  echo [STEP] Création de l'environnement virtuel...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
echo [OK] Environnement virtuel activé

REM 4) Installation dépendances
echo [STEP] Installation des dépendances Python...
pip install --upgrade pip >nul 2>&1
if exist requirements.txt (
  pip install -r requirements.txt --timeout 60 --retries 3 >nul 2>&1 || (
    echo [WARN] Installation complète échouée, installation des packages essentiels...
    pip install flask flask-cors python-dotenv requests pyyaml beautifulsoup4 python-docx >nul 2>&1
  )
) else (
  pip install flask flask-cors python-dotenv requests pyyaml beautifulsoup4 python-docx >nul 2>&1
)
echo [OK] Dépendances installées

REM 5) Configuration
echo [STEP] Configuration de l'application...
if not exist settings-local.yaml (
  echo [STEP] Création de settings-local.yaml avec les paramètres Ollama par défaut...
  echo provider: ollama > settings-local.yaml
  echo model: llama3:8b >> settings-local.yaml
  echo embedding_model: nomic-embed-text >> settings-local.yaml
  echo top_k: 5 >> settings-local.yaml
  echo timeout_s: 60 >> settings-local.yaml
  echo temperature: 0.1 >> settings-local.yaml
)

if not exist .env (
  echo [STEP] Création fichier .env...
  echo # Configuration Coach de Révision > .env
  echo OLLAMA_HOST=http://127.0.0.1:11434 >> .env
  echo CORS_ORIGINS=http://127.0.0.1:5000,http://localhost:5000 >> .env
  echo FLASK_ENV=development >> .env
  echo DEBUG=true >> .env
)

REM 6) Vérification Ollama
echo [STEP] Vérification Ollama...
where ollama >nul 2>&1
if !errorlevel! equ 0 (
  echo [OK] Ollama trouvé
  
  REM Vérifier si Ollama tourne
  curl -s --connect-timeout 2 http://127.0.0.1:11434/api/tags >nul 2>&1
  if !errorlevel! neq 0 (
    echo [STEP] Démarrage Ollama...
    start /B ollama serve
    timeout /t 3 /nobreak >nul
  )
  
  REM Télécharger modèles si nécessaire
  curl -s --connect-timeout 2 http://127.0.0.1:11434/api/tags >nul 2>&1
  if !errorlevel! equ 0 (
    for /f "delims=" %%i in ('curl -s --connect-timeout 5 http://127.0.0.1:11434/api/tags 2^>nul ^| findstr "llama3:8b"') do set LLAMA_MODEL=%%i
    if "!LLAMA_MODEL!"=="" (
      echo [STEP] Téléchargement modèle llama3:8b en arrière-plan...
      start /B ollama pull llama3:8b
    ) else (
      echo [OK] Modèle llama3:8b disponible
    )
    
    for /f "delims=" %%i in ('curl -s --connect-timeout 5 http://127.0.0.1:11434/api/tags 2^>nul ^| findstr "nomic-embed-text"') do set EMBED_MODEL=%%i
    if "!EMBED_MODEL!"=="" (
      echo [STEP] Téléchargement modèle nomic-embed-text en arrière-plan...
      start /B ollama pull nomic-embed-text
    ) else (
      echo [OK] Modèle nomic-embed-text disponible
    )
  ) else (
    echo [WARN] Ollama serveur non accessible - les modèles ne seront pas téléchargés
  )
) else (
  echo [WARN] Ollama non trouvé - installation recommandée depuis https://ollama.ai
  echo [WARN] L'application fonctionnera en mode dégradé (sans IA)
)

REM 7) Recherche port libre
echo [STEP] Recherche d'un port libre...
set PORT=5000
:FIND_PORT
netstat -an | findstr ":!PORT! " >nul 2>&1
if !errorlevel! equ 0 (
  set /a PORT+=1
  if !PORT! leq 5010 goto FIND_PORT
  echo [WARN] Tous les ports 5000-5010 occupés, utilisation du port 5000 par défaut
  set PORT=5000
) else (
  echo [OK] Port !PORT! sélectionné
)

REM 8) Test de santé (optionnel)
if exist "tools\doctor.sh" (
  echo [STEP] Vérification santé système...
  bash tools/doctor.sh >nul 2>&1
  if !errorlevel! neq 0 (
    echo [WARN] Diagnostic détecte des problèmes - voir tools\doctor.sh pour détails
  )
)

REM 9) Démarrage et ouverture navigateur
echo [STEP] Démarrage Coach de Révision sur http://127.0.0.1:!PORT!

REM Ouvrir le navigateur après un délai
start "" cmd /c "timeout /t 3 /nobreak >nul && start \"\" \"http://127.0.0.1:!PORT!\""

echo.
echo [OK] ======================================
echo [OK] 🚀 COACH DE RÉVISION LANCÉ
echo [OK] 📱 Interface: http://127.0.0.1:!PORT!
echo [OK] 🛠️  Diagnostic: tools\doctor.sh
echo [OK] 🧪 Tests: tools\smoke.sh
echo [OK] ======================================
echo.

REM Définir la variable d'environnement PORT et lancer
set PORT=!PORT!
python app.py