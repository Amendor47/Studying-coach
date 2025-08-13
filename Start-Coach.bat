@echo off
setlocal ENABLEDELAYEDEXPANSION
echo ==== Coach de Révision — LANCEUR WINDOWS ====
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
echo [*] Installation des dependances...
pip install --upgrade pip >nul
if exist requirements.txt (
  pip install -r requirements.txt
) else (
  pip install flask openai python-docx pdfminer.six
)

REM 5) Clé OpenAI (facultative)
if not exist .env (
  set /p KEY=Entrez votre OPENAI_API_KEY (laisser vide pour mode offline): 
  > .env echo OPENAI_API_KEY=%KEY%
)

REM 6) Lancer serveur et ouvrir le navigateur
start "" "http://127.0.0.1:5000"
python app.py
