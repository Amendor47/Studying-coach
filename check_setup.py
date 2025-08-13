import os, sys

required_dirs = ['cache', 'logs', 'services', 'static', 'templates']
required_files = [
    'app.py', 'db.json', 'requirements.txt',
    'services/ai.py', 'services/analyzer.py', 'services/chunker.py',
    'services/heuristics.py', 'services/planner.py',
    'services/scheduler.py', 'services/store.py', 'services/validate.py',
    'templates/index.html', 'static/app.js', 'static/style.css'
]

missing = []
for d in required_dirs:
    if not os.path.isdir(d):
        missing.append(d+'/')
for f in required_files:
    if not os.path.isfile(f):
        missing.append(f)

if missing:
    print("Il manque les fichiers/dossiers suivants :")
    for m in missing:
        print(" -", m)
    sys.exit(1)
else:
    print("Tout semble prêt !")