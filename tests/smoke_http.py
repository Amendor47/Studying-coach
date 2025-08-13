#!/usr/bin/env python3
"""
smoke_http.py - Tests de fumée HTTP pour Study Coach
Tests automatisés des endpoints critiques avec pytest
"""

import pytest
import httpx
import os
import sys
from pathlib import Path
import tempfile
import asyncio
import time

# Configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:5000")
TIMEOUT = 10.0

class TestStudyCoachAPI:
    """Tests de fumée pour l'API Study Coach"""
    
    @pytest.fixture(scope="class")
    def client(self):
        """Client HTTP réutilisable"""
        return httpx.Client(base_url=BASE_URL, timeout=TIMEOUT)
    
    def test_health_endpoint(self, client):
        """Test de base - endpoint de santé"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True
        assert "status" in data
        print(f"✅ Health check: {data}")
    
    def test_llm_health_endpoint(self, client):
        """Test santé LLM - peut échouer si Ollama absent"""
        response = client.get("/api/health/llm")
        
        # Accepter 200 ou erreurs gracieuses
        assert response.status_code in [200, 500]
        
        data = response.json()
        assert "ok" in data
        assert "provider" in data
        assert "info" in data
        
        if data["ok"]:
            print(f"✅ LLM Health: {data['info']} ({data['provider']})")
        else:
            print(f"⚠️  LLM Health: {data['info']} - Normal si Ollama non installé")
    
    def test_offline_analyze_endpoint(self, client):
        """Test analyse hors ligne - doit toujours fonctionner"""
        test_data = {
            "text": "Ceci est un concept important à retenir pour l'examen. La photosynthèse est un processus biologique."
        }
        
        response = client.post(
            "/api/offline/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "drafts" in data
        assert isinstance(data["drafts"], list)
        
        print(f"✅ Analyse offline: {len(data['drafts'])} éléments générés")
        
        # Vérifier la structure des drafts
        if data["drafts"]:
            draft = data["drafts"][0]
            assert "kind" in draft
            assert "payload" in draft
    
    def test_themes_endpoint(self, client):
        """Test récupération des thèmes"""
        response = client.get("/api/themes")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "themes" in data
        assert isinstance(data["themes"], list)
        
        print(f"✅ Thèmes: {len(data['themes'])} thèmes disponibles")
    
    def test_due_cards_endpoint(self, client):
        """Test récupération des cartes dues"""
        response = client.get("/api/due")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cards" in data
        assert isinstance(data["cards"], list)
        
        print(f"✅ Cartes dues: {len(data['cards'])} cartes")
    
    def test_upload_endpoint_no_file(self, client):
        """Test upload sans fichier - doit retourner erreur gracieuse"""
        response = client.post("/api/upload")
        
        assert response.status_code == 400
        data = response.json()
        
        assert "error" in data or "ok" in data
        print("✅ Upload sans fichier: erreur gracieuse")
    
    def test_upload_endpoint_with_file(self, client):
        """Test upload avec fichier temporaire"""
        # Créer un fichier temporaire
        test_content = """# Test Document

## Introduction
Ceci est un document de test pour vérifier l'upload.

### Concepts clés
- Concept A: Important pour comprendre
- Concept B: Élément fondamental
- Concept C: Application pratique

## Conclusion  
Ce document contient des éléments qui devraient générer des cartes d'étude.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("test_doc.md", f, "text/markdown")}
                response = client.post("/api/upload", files=files)
            
            # Accepter succès ou erreurs gracieuses (dépendances manquantes)
            assert response.status_code in [200, 400, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert "saved" in data
                print(f"✅ Upload réussi: {data.get('saved', 0)} éléments sauvés")
            else:
                data = response.json()
                print(f"⚠️  Upload avec restrictions: {data.get('error', 'erreur inconnue')}")
                
        finally:
            # Nettoyage
            os.unlink(temp_file_path)
    
    def test_main_page_loads(self, client):
        """Test que la page principale se charge"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        
        # Vérifier quelques éléments clés dans le HTML
        content = response.text
        assert "Study Coach" in content
        assert "file-input" in content
        assert "upload-btn" in content
        
        print("✅ Page principale: chargée avec éléments critiques")
    
    def test_static_resources(self, client):
        """Test que les ressources statiques critiques existent"""
        critical_resources = [
            "/static/app.js",
            "/static/style.css", 
            "/static/baseurl.js",
            "/static/ui_error_overlay.js",
            "/static/dom_probe.js",
            "/static/debug.css"
        ]
        
        for resource in critical_resources:
            response = client.get(resource)
            assert response.status_code == 200, f"Ressource manquante: {resource}"
            
        print(f"✅ Ressources statiques: {len(critical_resources)} fichiers OK")


@pytest.fixture(scope="session", autouse=True)
def ensure_app_running():
    """S'assurer que l'application tourne avant les tests"""
    import subprocess
    import socket
    
    def is_port_open(host, port):
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except:
            return False
    
    # Vérifier si l'app tourne déjà
    host, port = BASE_URL.replace("http://", "").split(":")
    port = int(port)
    
    if is_port_open(host, port):
        print(f"✅ Application déjà en cours sur {BASE_URL}")
        yield
        return
    
    # Démarrer l'application si nécessaire
    print(f"🚀 Démarrage de l'application pour les tests...")
    
    app_process = None
    try:
        # Essayer de démarrer l'app
        app_process = subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            env={**os.environ, "PORT": str(port)}
        )
        
        # Attendre que l'application soit prête
        for i in range(30):  # Timeout de 30 secondes
            if is_port_open(host, port):
                print(f"✅ Application prête sur {BASE_URL}")
                break
            time.sleep(1)
        else:
            raise RuntimeError(f"Application non prête après 30 secondes")
        
        yield
        
    finally:
        if app_process:
            app_process.terminate()
            app_process.wait(timeout=5)
            print("🛑 Application arrêtée")


if __name__ == "__main__":
    # Exécution directe
    print("🧪 TESTS DE FUMÉE HTTP - Study Coach")
    print("=" * 50)
    
    # Exécuter pytest
    exit_code = pytest.main([
        __file__, 
        "-v", 
        "--tb=short",
        "--color=yes"
    ])
    
    sys.exit(exit_code)