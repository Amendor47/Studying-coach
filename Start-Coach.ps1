#Requires -Version 5
Write-Host "==== Coach de Révision — LANCEUR POWERSHELL ===="
$python = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) { Write-Host "[!] Python introuvable." -ForegroundColor Red; exit 1 }

if (-not (Test-Path ".\.venv")) { python -m venv .venv }
& .\.venv\Scripts\Activate.ps1
pip install --upgrade pip | Out-Null
if (Test-Path ".\requirements.txt") { pip install -r requirements.txt } else { pip install flask openai python-docx pdfminer.six }

if (-not (Test-Path ".\.env")) {
  $key = Read-Host "Entrez votre OPENAI_API_KEY (ou Enter pour offline)"
  Set-Content -Path ".\.env" -Value "OPENAI_API_KEY=$key"
}

Start-Process "http://127.0.0.1:5000"
python .\app.py