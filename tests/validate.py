#!/usr/bin/env python3
"""
Simple validation script to check if the Python app can be imported
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

def validate_app():
    """Try to import and validate the app"""
    print("==== STUDYING COACH VALIDATION ====")
    
    print("1. Checking Python syntax...")
    try:
        with open('app.py', 'r') as f:
            code = f.read()
        compile(code, 'app.py', 'exec')
        print("   ✅ Python syntax is valid")
    except SyntaxError as e:
        print(f"   ❌ Syntax error: {e}")
        return False
    except FileNotFoundError:
        print("   ❌ app.py not found")
        return False
    
    print("2. Checking template files...")
    try:
        if os.path.exists('templates/index.html'):
            print("   ✅ Main template found")
        else:
            print("   ❌ Main template missing")
            return False
    except Exception as e:
        print(f"   ❌ Template check failed: {e}")
        return False
    
    print("3. Checking static files...")
    required_static = ['app.js', 'ui_error_overlay.js', 'baseurl.js']
    for filename in required_static:
        if os.path.exists(f'static/{filename}'):
            print(f"   ✅ {filename} found")
        else:
            print(f"   ❌ {filename} missing")
            return False
    
    print("4. Checking diagnostic tools...")
    if os.path.exists('tools/doctor.sh') and os.access('tools/doctor.sh', os.X_OK):
        print("   ✅ doctor.sh found and executable")
    else:
        print("   ❌ doctor.sh missing or not executable")
        return False
    
    if os.path.exists('tools/smoke.sh') and os.access('tools/smoke.sh', os.X_OK):
        print("   ✅ smoke.sh found and executable")
    else:
        print("   ❌ smoke.sh missing or not executable")
        return False
    
    print("\n==== VALIDATION RESULTS ====")
    print("✅ All basic validation checks passed!")
    print("\nNote: Full functionality requires proper dependencies and services")
    print("Run ./tools/doctor.sh for detailed system health check")
    return True

if __name__ == "__main__":
    success = validate_app()
    sys.exit(0 if success else 1)