#!/usr/bin/env python3
"""
GUI Launcher for Studying Coach
Addresses the PyQt interface issue mentioned in the problem statement.

This creates a simple GUI that launches the web interface, solving the
"Python User Interface not working" issue where code runs but no interface appears.
"""

import sys
import os
import threading
import time
import webbrowser
import subprocess
from pathlib import Path

# Try to import GUI libraries with fallbacks
GUI_AVAILABLE = False
GUI_LIBRARY = None

# Try tkinter first (built into Python)
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    GUI_AVAILABLE = True
    GUI_LIBRARY = "tkinter"
except ImportError:
    pass

# Try PyQt5 as fallback
if not GUI_AVAILABLE:
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
        from PyQt5.QtCore import Qt, QTimer
        GUI_AVAILABLE = True
        GUI_LIBRARY = "pyqt5"
    except ImportError:
        pass

# Try PyQt4 as mentioned in the Stack Overflow issue
if not GUI_AVAILABLE:
    try:
        from PyQt4.QtGui import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
        from PyQt4.QtCore import Qt, QTimer
        GUI_AVAILABLE = True
        GUI_LIBRARY = "pyqt4"
    except ImportError:
        pass

class StudyingCoachGUI:
    """Simple GUI launcher for the Studying Coach application"""
    
    def __init__(self):
        self.server_process = None
        self.port = 8000
        self.is_running = False
        
    def create_tkinter_gui(self):
        """Create GUI using tkinter"""
        self.root = tk.Tk()
        self.root.title("Studying Coach - GUI Launcher")
        self.root.geometry("500x400")
        self.root.resizable(True, True)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="🎯 Studying Coach", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Subtitle
        subtitle_label = ttk.Label(main_frame, text="Ultimate Learning Solution", 
                                  font=("Arial", 10))
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to start", 
                                     foreground="green")
        self.status_label.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Start button
        self.start_button = ttk.Button(buttons_frame, text="🚀 Start Server", 
                                      command=self.start_server)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        # Open browser button
        self.browser_button = ttk.Button(buttons_frame, text="🌐 Open Browser", 
                                        command=self.open_browser, state="disabled")
        self.browser_button.grid(row=0, column=1, padx=10)
        
        # Stop button
        self.stop_button = ttk.Button(buttons_frame, text="🛑 Stop Server", 
                                     command=self.stop_server, state="disabled")
        self.stop_button.grid(row=0, column=2, padx=(10, 0))
        
        # Log area
        log_label = ttk.Label(main_frame, text="Server Output:")
        log_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(20, 5))
        
        # Log text area with scrollbar
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = tk.Text(log_frame, height=10, width=60, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Initial log message
        self.log("GUI Launcher started successfully")
        self.log("This solves the 'Python User Interface not working' issue")
        self.log("Ready to launch Studying Coach server...")
        
        return self.root
    
    def create_pyqt_gui(self):
        """Create GUI using PyQt"""
        if GUI_LIBRARY == "pyqt5":
            from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
        elif GUI_LIBRARY == "pyqt4":
            from PyQt4.QtGui import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
        
        self.app = QApplication(sys.argv)
        self.window = QMainWindow()
        self.window.setWindowTitle("Studying Coach - GUI Launcher")
        self.window.setGeometry(100, 100, 500, 400)
        
        # Central widget
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Title
        title_label = QLabel("🎯 Studying Coach")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Ultimate Learning Solution")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 10pt; margin-bottom: 20px;")
        layout.addWidget(subtitle_label)
        
        # Status
        self.status_label = QLabel("Ready to start")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: green; margin-bottom: 10px;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("🚀 Start Server")
        self.start_button.clicked.connect(self.start_server)
        button_layout.addWidget(self.start_button)
        
        self.browser_button = QPushButton("🌐 Open Browser")
        self.browser_button.clicked.connect(self.open_browser)
        self.browser_button.setEnabled(False)
        button_layout.addWidget(self.browser_button)
        
        self.stop_button = QPushButton("🛑 Stop Server")
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        # Log area
        log_label = QLabel("Server Output:")
        log_label.setStyleSheet("margin-top: 20px;")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # Initial log message
        self.log("GUI Launcher started successfully")
        self.log("This solves the 'Python User Interface not working' issue")
        self.log("Ready to launch Studying Coach server...")
        
        return self.window
    
    def log(self, message):
        """Add a message to the log"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        if GUI_LIBRARY == "tkinter":
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
        elif GUI_LIBRARY in ["pyqt4", "pyqt5"]:
            self.log_text.append(log_message.strip())
        else:
            print(log_message.strip())
    
    def start_server(self):
        """Start the Studying Coach server"""
        if self.is_running:
            self.log("Server is already running")
            return
        
        self.log("Starting Studying Coach server...")
        
        # Try different server files in order of preference
        server_files = ["simple_server.py", "core_app.py", "app.py"]
        server_file = None
        
        for filename in server_files:
            if Path(filename).exists():
                server_file = filename
                break
        
        if not server_file:
            self.log("❌ No server file found!")
            self.update_status("Error: No server file found", "red")
            return
        
        try:
            # Start server in a separate thread
            def run_server():
                try:
                    self.server_process = subprocess.Popen(
                        [sys.executable, server_file],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                        cwd=os.getcwd()
                    )
                    
                    self.is_running = True
                    self.update_buttons_state()
                    
                    # Read output
                    for line in iter(self.server_process.stdout.readline, ''):
                        if line:
                            self.log(line.strip())
                        if self.server_process.poll() is not None:
                            break
                    
                except Exception as e:
                    self.log(f"❌ Error starting server: {e}")
                    self.update_status(f"Error: {e}", "red")
                finally:
                    self.is_running = False
                    self.update_buttons_state()
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # Give server time to start
            time.sleep(2)
            self.log(f"✅ Server started using {server_file}")
            self.update_status(f"Running on http://127.0.0.1:{self.port}", "green")
            
        except Exception as e:
            self.log(f"❌ Failed to start server: {e}")
            self.update_status(f"Error: {e}", "red")
    
    def stop_server(self):
        """Stop the server"""
        if self.server_process and self.is_running:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                self.log("✅ Server stopped")
                self.update_status("Stopped", "orange")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.log("⚠️  Server force-killed")
            except Exception as e:
                self.log(f"❌ Error stopping server: {e}")
        
        self.is_running = False
        self.update_buttons_state()
    
    def open_browser(self):
        """Open the web interface in browser"""
        url = f"http://127.0.0.1:{self.port}"
        try:
            webbrowser.open(url)
            self.log(f"🌐 Opened browser: {url}")
        except Exception as e:
            self.log(f"❌ Could not open browser: {e}")
    
    def update_status(self, message, color="black"):
        """Update status label"""
        if GUI_LIBRARY == "tkinter":
            self.status_label.config(text=message, foreground=color)
        elif GUI_LIBRARY in ["pyqt4", "pyqt5"]:
            self.status_label.setText(message)
            self.status_label.setStyleSheet(f"color: {color}; margin-bottom: 10px;")
    
    def update_buttons_state(self):
        """Update button states based on server status"""
        if GUI_LIBRARY == "tkinter":
            if self.is_running:
                self.start_button.config(state="disabled")
                self.browser_button.config(state="normal")
                self.stop_button.config(state="normal")
            else:
                self.start_button.config(state="normal")
                self.browser_button.config(state="disabled")
                self.stop_button.config(state="disabled")
        elif GUI_LIBRARY in ["pyqt4", "pyqt5"]:
            self.start_button.setEnabled(not self.is_running)
            self.browser_button.setEnabled(self.is_running)
            self.stop_button.setEnabled(self.is_running)
    
    def run(self):
        """Run the GUI application"""
        if not GUI_AVAILABLE:
            print("❌ No GUI library available!")
            print("This addresses the PyQt interface issue, but no GUI libraries are installed.")
            print("Install tkinter, PyQt5, or PyQt4 to use the GUI launcher.")
            return False
        
        try:
            if GUI_LIBRARY == "tkinter":
                gui = self.create_tkinter_gui()
                self.log(f"Using {GUI_LIBRARY} for GUI")
                gui.protocol("WM_DELETE_WINDOW", self.on_closing)
                gui.mainloop()
            
            elif GUI_LIBRARY in ["pyqt4", "pyqt5"]:
                gui = self.create_pyqt_gui()
                self.log(f"Using {GUI_LIBRARY} for GUI")
                gui.show()
                
                # This is the key fix for the PyQt issue mentioned in Stack Overflow
                # The problem was missing proper application event loop execution
                sys.exit(self.app.exec_())
            
            return True
            
        except Exception as e:
            print(f"❌ GUI Error: {e}")
            return False
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            self.stop_server()
        
        if GUI_LIBRARY == "tkinter":
            self.root.destroy()
        elif GUI_LIBRARY in ["pyqt4", "pyqt5"]:
            self.app.quit()


def main():
    """
    Main function that addresses the PyQt interface issue.
    
    This is the key fix mentioned in the Stack Overflow answer:
    - Proper if __name__ == "__main__" block
    - QApplication creation and management
    - Proper event loop execution with app.exec_()
    """
    
    print("🎯 Studying Coach - GUI Launcher")
    print("=" * 40)
    print("Addressing 'Python User Interface not working' issue")
    print("This creates a proper GUI with working event loop")
    print()
    
    # Check if we're in the right directory
    if not any(Path(f).exists() for f in ["simple_server.py", "core_app.py", "app.py"]):
        print("❌ No server files found in current directory!")
        print("Make sure you're running this from the Studying Coach root directory.")
        input("Press Enter to exit...")
        return
    
    # Create and run the GUI
    launcher = StudyingCoachGUI()
    success = launcher.run()
    
    if not success:
        print("\nFalling back to command-line mode...")
        print("You can manually start the server with:")
        print("  python simple_server.py")
        print("  python core_app.py")
        print("  python app.py")
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    """
    This is the crucial part that was missing in the Stack Overflow issue.
    
    The original problem was that PyQt code ran but showed no interface because:
    1. No proper QApplication was created
    2. No main window was shown
    3. No event loop was started with app.exec_()
    
    This implementation provides the complete pattern for a working GUI.
    """
    main()