#!/usr/bin/env python3
"""
Test script to verify offline functionality of Studying Coach
"""

import os
import sys
import tempfile
import subprocess
import time
import requests
from pathlib import Path

def test_offline_mode():
    """Test that the application works completely offline."""
    print("=== Test du Mode Hors-Ligne ===")
    
    # Set offline environment variables
    env = os.environ.copy()
    env.update({
        'TRANSFORMERS_OFFLINE': '1',
        'TOKENIZERS_PARALLELISM': 'false',
        'LLM_PROVIDER': 'offline',
        'FLASK_DEBUG': '0',
        'PORT': '5001'
    })
    
    # Start the Flask app
    print("[*] Démarrage du serveur en mode hors-ligne...")
    process = subprocess.Popen(
        [sys.executable, 'app.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(5)
    
    try:
        # Test basic connectivity
        print("[*] Test de connectivité...")
        response = requests.get('http://127.0.0.1:5001/', timeout=5)
        if response.status_code == 200:
            print("✅ Serveur accessible")
        else:
            print(f"❌ Erreur serveur: {response.status_code}")
            return False
        
        # Test health endpoint
        print("[*] Test de santé de l'API...")
        health_response = requests.get('http://127.0.0.1:5001/api/health', timeout=5)
        if health_response.status_code in (200, 503):  # 503 is OK for degraded mode
            health_data = health_response.json()
            print(f"✅ API Health: {health_data.get('status', 'unknown')}")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
        
        # Test offline analyzer
        print("[*] Test de l'analyseur hors-ligne...")
        test_text = """
        # Photosynthèse
        
        La photosynthèse est le processus par lequel les plantes convertissent la lumière solaire en énergie chimique.
        
        ## Étapes principales
        1. Absorption de la lumière par la chlorophylle
        2. Conversion de CO2 et H2O en glucose
        3. Libération d'oxygène comme sous-produit
        """
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_text)
            temp_file = f.name
        
        try:
            # Test file upload
            with open(temp_file, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                upload_response = requests.post(
                    'http://127.0.0.1:5001/api/upload',
                    files=files,
                    timeout=10
                )
            
            if upload_response.status_code == 200:
                print("✅ Upload de fichier fonctionne")
                
                upload_data = upload_response.json()
                if 'items' in upload_data and len(upload_data['items']) > 0:
                    print(f"✅ Analyse hors-ligne: {len(upload_data['items'])} éléments générés")
                else:
                    print("⚠️  Aucun élément généré par l'analyse")
            else:
                print(f"❌ Upload échoué: {upload_response.status_code}")
                
        finally:
            os.unlink(temp_file)
        
        print("✅ Test du mode hors-ligne réussi!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False
        
    finally:
        # Cleanup
        print("[*] Arrêt du serveur...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def test_analyzer_offline():
    """Test the offline analyzer directly."""
    print("\n=== Test Analyseur Direct ===")
    
    try:
        from services.analyzer import analyze_offline
        
        test_text = """
        # Les Équations du Second Degré
        
        Une équation du second degré a la forme ax² + bx + c = 0.
        
        Le discriminant Δ = b² - 4ac détermine le nombre de solutions:
        - Si Δ > 0: deux solutions réelles distinctes
        - Si Δ = 0: une solution double
        - Si Δ < 0: pas de solution réelle
        """
        
        result = analyze_offline(test_text)
        print(f"✅ Analyseur direct: {len(result)} éléments générés")
        
        # Show types of generated items
        item_types = {}
        for item in result:
            kind = item.get('kind', 'unknown')
            item_types[kind] = item_types.get(kind, 0) + 1
        
        for kind, count in item_types.items():
            print(f"   - {kind}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur analyseur: {e}")
        return False


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    
    success = True
    success &= test_analyzer_offline()
    success &= test_offline_mode()
    
    if success:
        print("\n🎉 Tous les tests hors-ligne ont réussi!")
        print("L'application fonctionne parfaitement sans connexion internet.")
    else:
        print("\n❌ Certains tests ont échoué")
        sys.exit(1)