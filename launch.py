#!/usr/bin/env python3
"""
Universal Studying Coach Launcher
Works on Windows, macOS, Linux with zero configuration.
"""

import os
import sys
import subprocess
import shutil
import time
import webbrowser
from pathlib import Path

def print_banner():
    print("""
🎯 ====================================
   STUDYING COACH - UNIVERSAL LAUNCHER
   ====================================
   
   Simple • Robust • Cross-Platform
   Works 100% out of the box!
""")

def check_python():
    """Verify Python installation"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print("❌ Python 3.6+ required. Please update Python.")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def find_python_executable():
    """Find the right Python executable"""
    executables = ['python3', 'python', 'py']
    
    for exe in executables:
        if shutil.which(exe):
            try:
                result = subprocess.run([exe, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and '3.' in result.stdout:
                    return exe
            except:
                continue
    
    return sys.executable

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    python_exe = find_python_executable()
    basic_deps = ['flask']
    optional_deps = ['python-docx', 'pdfminer.six', 'openai', 'requests']
    
    # Install basic dependencies (required)
    for dep in basic_deps:
        print(f"   Installing {dep}...")
        try:
            subprocess.run([python_exe, '-m', 'pip', 'install', dep], 
                         capture_output=True, check=True, timeout=120)
            print(f"   ✅ {dep} installed")
        except subprocess.CalledProcessError:
            print(f"   ❌ Failed to install {dep}")
            return False
        except subprocess.TimeoutExpired:
            print(f"   ⏱️ Timeout installing {dep}")
    
    # Install optional dependencies (best effort)
    print("\n📦 Installing optional features...")
    for dep in optional_deps:
        print(f"   Installing {dep} (optional)...")
        try:
            subprocess.run([python_exe, '-m', 'pip', 'install', dep], 
                         capture_output=True, timeout=120)
            print(f"   ✅ {dep} installed")
        except:
            print(f"   ⚠️  {dep} not installed (optional)")
    
    return True

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port"""
    import socket
    
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    
    return start_port  # Fallback to original port

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("\n🔧 Setting up configuration...")
        
        # Try to get OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY', '')
        if not api_key:
            try:
                api_key = input("Enter OpenAI API Key (optional, press Enter to skip): ").strip()
            except (KeyboardInterrupt, EOFError):
                api_key = ""
        
        with open(env_file, 'w') as f:
            f.write("# Studying Coach Configuration\n")
            f.write("# Generated automatically by launcher\n\n")
            
            if api_key:
                f.write(f"OPENAI_API_KEY={api_key}\n")
                f.write("AI_ENABLED=true\n")
            else:
                f.write("# OPENAI_API_KEY=your_key_here\n")
                f.write("AI_ENABLED=false\n")
            
            f.write("DEBUG=false\n")
        
        print("✅ Configuration file created")

def start_server():
    """Start the Studying Coach server"""
    print("\n🚀 Starting Studying Coach...")
    
    # Find available port
    port = find_available_port()
    os.environ['PORT'] = str(port)
    
    print(f"   Server will start on port {port}")
    
    # Set up environment
    create_env_file()
    
    # Try to open browser after a delay
    def open_browser_delayed():
        time.sleep(3)
        try:
            url = f"http://localhost:{port}"
            print(f"🌐 Opening browser: {url}")
            webbrowser.open(url)
        except Exception as e:
            print(f"⚠️  Could not open browser: {e}")
            print(f"   Please open: http://localhost:{port}")
    
    import threading
    browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
    browser_thread.start()
    
    # Start the server
    python_exe = find_python_executable()
    
    try:
        print("✅ Studying Coach is running!")
        print(f"🌐 Access at: http://localhost:{port}")
        print("🛑 Press Ctrl+C to stop")
        print()
        
        subprocess.run([python_exe, 'core_app.py'], 
                      env={**os.environ, 'PORT': str(port)})
                      
    except KeyboardInterrupt:
        print("\n\n👋 Studying Coach stopped. Goodbye!")
    except FileNotFoundError:
        print(f"❌ Could not find core_app.py in current directory")
        print("   Make sure you're running this from the Studying Coach folder")
        return False
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False
    
    return True

def main():
    """Main launcher function"""
    print_banner()
    
    # Basic checks
    if not check_python():
        input("Press Enter to exit...")
        return False
    
    # Change to script directory
    script_dir = Path(__file__).parent
    if script_dir.exists():
        os.chdir(script_dir)
        print(f"✅ Working directory: {script_dir}")
    
    # Check if core app exists
    if not Path('core_app.py').exists():
        print("❌ core_app.py not found!")
        print("   Make sure all files are in the same directory")
        input("Press Enter to exit...")
        return False
    
    # Install dependencies if needed
    try:
        import flask
        print("✅ Flask already available")
    except ImportError:
        if not install_dependencies():
            print("❌ Failed to install dependencies")
            input("Press Enter to exit...")
            return False
    
    # Start the server
    return start_server()

if __name__ == '__main__':
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)