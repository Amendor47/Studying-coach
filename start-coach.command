#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "==== Coach de Révision — LANCEUR MAC ===="
if ! command -v python3 >/dev/null 2>&1; then
  echo "[!] Python3 requis. Installez via https://www.python.org/downloads/"; exit 1
fi
if [ ! -d ".venv" ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install --upgrade pip >/dev/null
if [ -f requirements.txt ]; then pip install -r requirements.txt; else pip install flask openai python-docx pdfminer.six; fi
if [ ! -f ".env" ]; then
  read -p "OPENAI_API_KEY (laisser vide pour offline): " KEY
  echo "OPENAI_API_KEY=$KEY" > .env
fi
open "http://127.0.0.1:5000"
python3 app.py