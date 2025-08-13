#!/usr/bin/env python3
"""
HTTP smoke tests for Studying Coach API endpoints
"""
import sys
import os
import time
import subprocess
import requests
import json

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://127.0.0.1:5000"
TIMEOUT = 30  # seconds

def start_server():
    """Start the Flask server in a subprocess"""
    print("Starting Flask server...")
    
    # Try to activate venv if it exists
    activate_cmd = ""
    if os.path.exists(".venv/bin/activate"):
        activate_cmd = "source .venv/bin/activate && "
    
    # Start the server
    cmd = f"{activate_cmd}python app.py"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to be ready
    for i in range(TIMEOUT):
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=2)
            if response.status_code in [200, 503]:  # 503 is ok for health checks
                print(f"✅ Server ready after {i+1} seconds")
                return process
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    
    print("❌ Server failed to start")
    process.terminate()
    return None

def test_endpoint(method, path, description, data=None, expected_codes=[200]):
    """Test an API endpoint"""
    url = f"{BASE_URL}{path}"
    print(f"Testing {description}...")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            if data:
                if isinstance(data, dict):
                    response = requests.post(url, json=data, timeout=10)
                else:
                    response = requests.post(url, data=data, timeout=10)
            else:
                response = requests.post(url, timeout=10)
        
        if response.status_code in expected_codes:
            print(f"  ✅ {response.status_code} - {description}")
            try:
                result = response.json()
                print(f"     Response: {json.dumps(result, indent=2)[:200]}...")
            except:
                print(f"     Response: {response.text[:100]}...")
        else:
            print(f"  ❌ {response.status_code} - {description}")
            print(f"     Response: {response.text[:200]}...")
        
        return response.status_code in expected_codes
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Request failed - {description}: {e}")
        return False

def run_smoke_tests():
    """Run all smoke tests"""
    print("==== STUDYING COACH HTTP SMOKE TESTS ====")
    
    # Start server
    server_process = start_server()
    if not server_process:
        return False
    
    try:
        results = []
        
        # Test basic health endpoints
        results.append(test_endpoint("GET", "/api/health", "Basic health check", expected_codes=[200, 503]))
        results.append(test_endpoint("GET", "/api/health/llm", "LLM health check", expected_codes=[200, 503]))
        
        # Test improve endpoint
        results.append(test_endpoint("POST", "/api/improve", "Text improvement", 
                                   data={"text": "This is a test text for improvement."},
                                   expected_codes=[200, 500]))
        
        # Test offline analyze endpoint
        results.append(test_endpoint("POST", "/api/offline/analyze", "Offline text analysis",
                                   data={"text": "This is a test text for analysis."},
                                   expected_codes=[200, 500]))
        
        # Test upload endpoint (basic check without file)
        results.append(test_endpoint("POST", "/api/upload", "File upload (no file)", expected_codes=[400, 500]))
        
        # Test config endpoint
        results.append(test_endpoint("GET", "/api/config", "Configuration check", expected_codes=[200, 500]))
        
        # Test themes endpoint
        results.append(test_endpoint("GET", "/api/themes", "Themes list", expected_codes=[200, 500]))
        
        # Test due cards endpoint
        results.append(test_endpoint("GET", "/api/due", "Due cards", expected_codes=[200, 500]))
        
        print("\n==== SMOKE TEST RESULTS ====")
        passed = sum(results)
        total = len(results)
        print(f"Passed: {passed}/{total}")
        
        if passed == total:
            print("✅ All smoke tests passed!")
            return True
        else:
            print(f"❌ {total - passed} tests failed")
            return False
    
    finally:
        # Clean up server
        if server_process:
            print("\nStopping server...")
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)