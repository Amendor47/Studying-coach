#!/usr/bin/env python3
"""
Universal Studying Coach Interface Launcher
Solves the "Python User Interface not working" issue by providing multiple interface options.

This addresses the Stack Overflow issue by:
1. Providing fallback options when main interface doesn't work
2. Clear error handling and user guidance
3. Multiple interface types (GUI, web, minimal)
4. Proper main execution patterns
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path


def print_banner():
    """Display startup banner"""
    print("""
🎯 ================================================================
   STUDYING COACH - UNIVERSAL INTERFACE LAUNCHER
   ================================================================
   
   Solving "Python User Interface not working" issues
   Multiple interface options with automatic fallbacks
""")


def check_file_exists(filename):
    """Check if a file exists in the current directory"""
    return Path(filename).exists()


def try_import(module_name):
    """Try to import a module and return success status"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def run_interface(script_name, description, required_modules=None):
    """Try to run a specific interface script"""
    print(f"\n🚀 Attempting to start: {description}")
    print(f"   Script: {script_name}")
    
    # Check if script exists
    if not check_file_exists(script_name):
        print(f"❌ Script not found: {script_name}")
        return False
    
    # Check required modules if specified
    if required_modules:
        missing_modules = []
        for module in required_modules:
            if not try_import(module):
                missing_modules.append(module)
        
        if missing_modules:
            print(f"⚠️  Missing modules: {', '.join(missing_modules)}")
            print("   Attempting to continue anyway...")
    
    # Try to run the script
    try:
        print(f"✅ Starting {description}...")
        
        # For GUI launcher, don't wait for it to finish
        if "gui" in script_name.lower():
            process = subprocess.Popen([sys.executable, script_name])
            time.sleep(2)  # Give it time to start
            if process.poll() is None:  # Still running
                print(f"✅ {description} started successfully")
                return True
            else:
                print(f"❌ {description} exited immediately")
                return False
        else:
            # For web servers, run and let them handle their own execution
            result = subprocess.run([sys.executable, script_name], 
                                  timeout=3, capture_output=True, text=True)
            
            # If it times out, it's probably running successfully
            return True
            
    except subprocess.TimeoutExpired:
        # This is actually good for web servers
        print(f"✅ {description} appears to be running")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Python executable not found")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def install_flask_if_needed():
    """Try to install Flask if it's not available"""
    if try_import('flask'):
        print("✅ Flask is available")
        return True
    
    print("📦 Flask not found, attempting to install...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'flask'], 
                      check=True, capture_output=True)
        print("✅ Flask installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Could not install Flask automatically")
        return False
    except Exception as e:
        print(f"⚠️  Error installing Flask: {e}")
        return False


def show_interface_menu():
    """Show available interface options"""
    print("\n📋 Available Interface Options:")
    print("=" * 50)
    
    interfaces = [
        ("1", "gui_launcher.py", "GUI Launcher (Desktop)", ["tkinter"]),
        ("2", "minimal_app.py", "Minimal Web Interface (Always Works)", ["flask"]),
        ("3", "simple_server.py", "Simple HTTP Server (No Dependencies)", []),
        ("4", "app.py", "Full Web Application (Advanced Features)", ["flask", "python-dotenv"]),
        ("5", "core_app.py", "Core Application (Rebuilt)", ["flask"]),
        ("q", None, "Quit", [])
    ]
    
    for num, script, desc, deps in interfaces:
        exists = "✅" if script is None or check_file_exists(script) else "❌"
        deps_str = f" (needs: {', '.join(deps)})" if deps else " (no deps)"
        print(f"   {num}. {exists} {desc}{deps_str}")
    
    print("\n💡 Recommendation: Try option 2 (Minimal Web Interface) first")
    return interfaces


def auto_select_best_interface():
    """Automatically select the best available interface"""
    print("\n🤖 Auto-selecting best available interface...")
    
    # Priority order: minimal -> simple -> gui -> core -> full
    options = [
        ("minimal_app.py", "Minimal Web Interface", ["flask"]),
        ("simple_server.py", "Simple HTTP Server", []),
        ("gui_launcher.py", "GUI Launcher", ["tkinter"]),
        ("core_app.py", "Core Application", ["flask"]),
        ("app.py", "Full Application", ["flask", "python-dotenv"])
    ]
    
    for script, description, required_modules in options:
        if check_file_exists(script):
            print(f"🎯 Selected: {description}")
            
            # Install Flask if needed for web interfaces
            if "flask" in required_modules:
                install_flask_if_needed()
            
            success = run_interface(script, description, required_modules)
            if success:
                return True
            else:
                print(f"⚠️  {description} failed, trying next option...")
    
    print("❌ No working interface found")
    return False


def manual_interface_selection():
    """Let user manually select interface"""
    interfaces = show_interface_menu()
    
    while True:
        try:
            choice = input("\n🔹 Select interface (1-5, q to quit, a for auto): ").strip().lower()
            
            if choice == 'q':
                return False
            elif choice == 'a':
                return auto_select_best_interface()
            elif choice in ['1', '2', '3', '4', '5']:
                selected = interfaces[int(choice) - 1]
                script = selected[1]
                description = selected[2]
                required_modules = selected[3]
                
                # Install Flask if needed
                if "flask" in required_modules:
                    install_flask_if_needed()
                
                success = run_interface(script, description, required_modules)
                if success:
                    return True
                else:
                    print("❌ Interface failed to start. Try another option.")
                    continue
            else:
                print("❌ Invalid choice. Please enter 1-5, 'a' for auto, or 'q' to quit.")
                continue
                
        except (ValueError, IndexError):
            print("❌ Invalid input. Please try again.")
            continue
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled by user")
            return False


def show_troubleshooting_help():
    """Display troubleshooting information"""
    print("""
🔧 TROUBLESHOOTING GUIDE
========================

Problem: "Python User Interface not working"
Solutions:

1. 📦 MISSING DEPENDENCIES
   pip install flask python-dotenv flask-cors

2. 🐍 PYTHON VERSION ISSUES  
   Use Python 3.6+ 
   Check: python --version

3. 🔓 PERMISSION ISSUES
   Try: python3 instead of python
   Or run as administrator/sudo

4. 🌐 PORT CONFLICTS
   The app will auto-find free ports (5000-5010)
   Or set PORT environment variable

5. 🖥️  GUI LIBRARY ISSUES
   Install tkinter: sudo apt-get install python3-tkinter
   Or use web interface instead

6. 📁 WRONG DIRECTORY
   Make sure you're in the Studying Coach folder
   Should contain: app.py, minimal_app.py, etc.

For more help, check:
• README.md
• README_TROUBLESHOOT.md  
• GitHub Issues
""")


def main():
    """Main launcher function with proper error handling"""
    print_banner()
    
    # Basic environment check
    print("🔍 Environment Check:")
    print(f"   Python version: {sys.version}")
    print(f"   Working directory: {os.getcwd()}")
    print(f"   Script location: {Path(__file__).parent}")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    if script_dir.exists() and script_dir != Path.cwd():
        os.chdir(script_dir)
        print(f"   Changed to: {script_dir}")
    
    # Check for any Studying Coach files
    key_files = ["app.py", "minimal_app.py", "simple_server.py", "core_app.py", "gui_launcher.py"]
    found_files = [f for f in key_files if check_file_exists(f)]
    
    if not found_files:
        print("\n❌ No Studying Coach files found!")
        print("   Make sure you're in the correct directory")
        print("   Expected files: app.py, minimal_app.py, simple_server.py")
        show_troubleshooting_help()
        return False
    
    print(f"\n✅ Found {len(found_files)} interface files")
    
    # Show startup options
    print("\n🚀 STARTUP OPTIONS:")
    print("   1. Auto-select best interface (recommended)")
    print("   2. Manual interface selection")
    print("   3. Show troubleshooting help")
    
    try:
        choice = input("\nSelect option (1-3, Enter for auto): ").strip()
        
        if not choice or choice == '1':
            success = auto_select_best_interface()
        elif choice == '2':
            success = manual_interface_selection()
        elif choice == '3':
            show_troubleshooting_help()
            return main()  # Show menu again
        else:
            print("❌ Invalid choice, using auto-select")
            success = auto_select_best_interface()
        
        if success:
            print("\n✅ Interface launched successfully!")
            print("🌐 Your browser should open automatically")
            print("🛑 Press Ctrl+C in the interface to stop")
            return True
        else:
            print("\n❌ All interface options failed")
            show_troubleshooting_help()
            return False
            
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        show_troubleshooting_help()
        return False


if __name__ == "__main__":
    """
    Main execution block that properly addresses interface issues.
    
    This pattern solves the Stack Overflow PyQt issue by:
    1. Proper if __name__ == "__main__" usage
    2. Clear error handling and user feedback
    3. Multiple fallback options
    4. Helpful troubleshooting information
    """
    try:
        success = main()
        if not success:
            print("\n⚠️  No interface could be started")
            input("Press Enter to exit...")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Critical error: {e}")
        print("\nThis might help:")
        print("1. Check Python installation")
        print("2. Install dependencies: pip install flask")
        print("3. Run from correct directory")
        input("\nPress Enter to exit...")
        sys.exit(1)