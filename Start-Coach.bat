@echo off
setlocal ENABLEDELAYEDEXPANSION
echo ==== Studying Coach — LANCEUR WINDOWS ====

REM Check if we have a prebuilt executable
if exist "dist\StudyCoach.exe" (
  echo [*] Utilisation de l'executable standalone...
  
  REM Find available port from 5000 to 5010
  set PORT=5000
  :findport
  netstat -an | find ":!PORT! " >nul
  if errorlevel 1 (
    echo [*] Port !PORT! disponible
    goto startstandalone
  )
  set /a PORT=PORT+1
  if !PORT! LEQ 5010 goto findport
  
  echo [!] Aucun port disponible entre 5000 et 5010. Utilisation du port 5000.
  set PORT=5000
  
  :startstandalone
  REM Launch browser after a delay
  start "" cmd /c "ping 127.0.0.1 -n 4 >nul && start \"\" \"http://127.0.0.1:!PORT!\""
  
  echo [*] Demarrage de Studying Coach ^(standalone^) sur le port !PORT!...
  set "PORT=!PORT!"
  dist\StudyCoach.exe
  goto end
)

REM Fallback to Python development mode
echo [*] Executable standalone non trouve, utilisation du mode developpement Python...

REM 1) Vérif Python
python --version >nul 2>&1
if errorlevel 1 (
  echo [!] Python introuvable. Installe-le depuis https://www.python.org/downloads/ puis relance.
  pause
  exit /b 1
)

REM 2) Création venv si manquant
if not exist .venv (
  echo [*] Creation de l'environnement virtuel .venv ...
  python -m venv .venv
)

REM 3) Activer venv
call .venv\Scripts\activate.bat

REM 4) Installer dépendances
echo [*] Verification des dependances...
pip install --upgrade pip >nul 2>&1
if exist requirements.txt (
  pip install -r requirements.txt >nul 2>&1
) else (
  pip install flask openai python-docx pdfminer.six python-dotenv pyyaml requests flask-cors >nul 2>&1
)

REM 5) Créer fichier de configuration pour mode hors-ligne
if not exist settings-local.yaml (
  echo [*] Creation de settings-local.yaml...
  > settings-local.yaml echo provider: offline
  >> settings-local.yaml echo model: local
  >> settings-local.yaml echo embedding_model: none
  >> settings-local.yaml echo top_k: 5
  >> settings-local.yaml echo timeout_s: 30
  >> settings-local.yaml echo temperature: 0.1
)

REM 6) Configuration .env pour mode hors-ligne
if not exist .env (
  echo [*] Creation du fichier .env pour le mode hors-ligne...
  > .env echo SC_PROFILE=offline
  >> .env echo LLM_PROVIDER=offline
  >> .env echo TRANSFORMERS_OFFLINE=1
  >> .env echo TOKENIZERS_PARALLELISM=false
) else (
  findstr "TRANSFORMERS_OFFLINE" .env >nul || echo TRANSFORMERS_OFFLINE=1 >> .env
  findstr "TOKENIZERS_PARALLELISM" .env >nul || echo TOKENIZERS_PARALLELISM=false >> .env
)

REM 7) Trouver port disponible
set PORT=5000
:checkport
netstat -an | find ":!PORT! " >nul
if errorlevel 1 goto portfound
set /a PORT=PORT+1
if !PORT! LEQ 5010 goto checkport
echo [!] Aucun port disponible entre 5000 et 5010. Utilisation du port 5000.
set PORT=5000

:portfound
echo [*] Port !PORT! disponible, demarrage du serveur...

REM 8) Lancer serveur et ouvrir le navigateur
start "" cmd /c "ping 127.0.0.1 -n 4 >nul && start \"\" \"http://127.0.0.1:!PORT!\""

echo [*] Demarrage de Studying Coach sur le port !PORT!...
set "PORT=!PORT!"
python app.py

:end
pause
