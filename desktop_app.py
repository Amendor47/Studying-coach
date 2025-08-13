#!/usr/bin/env python3
"""
Desktop GUI wrapper for Studying Coach
Provides a native desktop experience without requiring a browser.
"""

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path
import subprocess
import socket

# Try to import webview for better desktop experience
try:
    import webview
    HAS_WEBVIEW = True
except ImportError:
    HAS_WEBVIEW = False

# Try to import tkinter for basic GUI
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    HAS_TKINTER = True
except ImportError:
    try:
        # Python 2 fallback (unlikely but just in case)
        import Tkinter as tk
        import ttk
        import tkMessageBox as messagebox
        HAS_TKINTER = True
    except ImportError:
        HAS_TKINTER = False
        tk = None
        ttk = None
        messagebox = None


def find_free_port(start_port=5000, end_port=5010):
    """Find a free port in the given range."""
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return start_port  # Fallback to start port


def start_flask_server(port):
    """Start the Flask server in a separate process."""
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['FLASK_DEBUG'] = '0'  # Disable debug mode for desktop app
    env['TRANSFORMERS_OFFLINE'] = '1'
    env['TOKENIZERS_PARALLELISM'] = 'false'
    
    # Start Flask app
    return subprocess.Popen(
        [sys.executable, 'app.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent
    )


def wait_for_server(port, timeout=30):
    """Wait for the server to be ready."""
    import time
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Try a simple socket connection first (faster than HTTP)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('127.0.0.1', port))
                if result == 0:
                    # Port is open, now test if it's our Flask app
                    time.sleep(0.5)  # Give Flask a moment to be ready
                    try:
                        import requests
                        response = requests.get(f'http://127.0.0.1:{port}/', timeout=2)
                        if response.status_code == 200:
                            return True
                    except:
                        pass  # HTTP not ready yet, continue waiting
        except:
            pass
        time.sleep(0.5)
    return False


class StudyCoachDesktop:
    """Desktop application wrapper for Studying Coach."""
    
    def __init__(self):
        self.port = find_free_port()
        self.flask_process = None
        self.webview_window = None
        
    def start_server(self):
        """Start the Flask server."""
        print(f"[*] Démarrage du serveur sur le port {self.port}...")
        
        try:
            self.flask_process = start_flask_server(self.port)
        except Exception as e:
            raise Exception(f"Impossible de démarrer le serveur Flask: {e}")
        
        # Wait for server to be ready
        print("[*] Attente du démarrage du serveur...")
        if not wait_for_server(self.port):
            # Try to get error information from the process
            if self.flask_process.poll() is not None:
                stdout, stderr = self.flask_process.communicate(timeout=5)
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Erreur inconnue"
                raise Exception(f"Le serveur n'a pas pu démarrer: {error_msg}")
            else:
                raise Exception("Le serveur n'a pas pu démarrer dans le délai imparti")
        
        print(f"[*] Serveur prêt sur http://127.0.0.1:{self.port}")
    
    def run_webview(self):
        """Run the application using webview for a native feel."""
        if not HAS_WEBVIEW:
            raise ImportError("webview n'est pas installé")
        
        self.start_server()
        
        # Create webview window
        self.webview_window = webview.create_window(
            title='Studying Coach',
            url=f'http://127.0.0.1:{self.port}',
            width=1200,
            height=800,
            resizable=True,
            minimized=False,
        )
        
        # Add menu items
        if hasattr(webview, 'menu'):
            menu_items = [
                webview.menu.Menu('Fichier', [
                    webview.menu.MenuAction('Quitter', self.quit_app),
                ]),
                webview.menu.Menu('Aide', [
                    webview.menu.MenuAction('À propos', self.show_about),
                ])
            ]
            self.webview_window.menu = menu_items
        
        print("[*] Ouverture de Studying Coach...")
        
        try:
            webview.start(
                debug=False,
                private_mode=False,
                storage_path=str(Path.home() / '.studying-coach'),
            )
        except KeyboardInterrupt:
            self.quit_app()
        except Exception as e:
            print(f"[!] Erreur webview: {e}")
            self.fallback_browser()
    
    def run_tkinter(self):
        """Run a simple Tkinter-based interface."""
        if not HAS_TKINTER:
            raise ImportError("tkinter n'est pas disponible")
        
        self.start_server()
        
        root = tk.Tk()
        root.title("Studying Coach")
        root.geometry("400x300")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Studying Coach", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Status
        status_label = ttk.Label(main_frame, text=f"Serveur actif sur le port {self.port}")
        status_label.grid(row=1, column=0, pady=10)
        
        # Open browser button
        browser_btn = ttk.Button(
            main_frame, 
            text="Ouvrir dans le navigateur", 
            command=self.open_browser
        )
        browser_btn.grid(row=2, column=0, pady=10)
        
        # Quit button
        quit_btn = ttk.Button(main_frame, text="Quitter", command=self.quit_app)
        quit_btn.grid(row=3, column=0, pady=10)
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Handle window closing
        root.protocol("WM_DELETE_WINDOW", self.quit_app)
        
        print("[*] Interface Tkinter prête")
        
        try:
            root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()
    
    def fallback_browser(self):
        """Fallback to opening in the default browser."""
        self.start_server()
        url = f'http://127.0.0.1:{self.port}'
        print(f"[*] Ouverture de {url} dans le navigateur par défaut...")
        webbrowser.open(url)
        
        # Keep the server running
        try:
            self.flask_process.wait()
        except KeyboardInterrupt:
            self.quit_app()
    
    def open_browser(self):
        """Open the application in the default browser."""
        webbrowser.open(f'http://127.0.0.1:{self.port}')
    
    def show_about(self):
        """Show about dialog."""
        if HAS_TKINTER:
            messagebox.showinfo(
                "À propos de Studying Coach",
                "Studying Coach - Assistant d'étude personnel\n\n"
                "Version: 1.0\n"
                "Application d'étude avec flashcards, QCM et révisions espacées."
            )
    
    def quit_app(self):
        """Clean shutdown of the application."""
        print("\n[*] Arrêt de Studying Coach...")
        
        if self.flask_process:
            try:
                self.flask_process.terminate()
                self.flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.flask_process.kill()
            except Exception as e:
                print(f"[!] Erreur lors de l'arrêt du serveur: {e}")
        
        if HAS_WEBVIEW and self.webview_window:
            try:
                webview.destroy_window()
            except:
                pass
        
        print("[*] Arrêt terminé")
        sys.exit(0)
    
    def run(self):
        """Run the desktop application with the best available GUI."""
        print("==== Studying Coach — Application Desktop ====")
        
        try:
            if HAS_WEBVIEW:
                print("[*] Utilisation de webview pour une expérience native")
                self.run_webview()
            elif HAS_TKINTER:
                print("[*] Utilisation de tkinter pour l'interface")
                self.run_tkinter()
            else:
                print("[*] Aucune interface graphique disponible, utilisation du navigateur")
                self.fallback_browser()
        except Exception as e:
            print(f"[!] Erreur lors du démarrage: {e}")
            print("[*] Tentative de démarrage avec le navigateur par défaut...")
            self.fallback_browser()


if __name__ == "__main__":
    app = StudyCoachDesktop()
    app.run()