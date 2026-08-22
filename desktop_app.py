"""PySide6 Desktop GUI Terminal Launcher with browser fallback"""

import sys
import subprocess
import webbrowser
import time
from pathlib import Path

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWebEngineWidgets import QWebEngineView
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


def start_fastapi_server():
    """Start FastAPI server in background"""
    try:
        if sys.platform == "win32":
            subprocess.Popen(
                [sys.executable, "main.py"],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=str(Path(__file__).parent)
            )
        else:
            subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=str(Path(__file__).parent)
            )
        time.sleep(2)
        return True
    except Exception as e:
        print(f"Error starting server: {e}")
        return False


def open_browser():
    """Open browser to localhost"""
    webbrowser.open("http://127.0.0.1:8000")


class VolHedgeDesktopApp(QMainWindow):
    """PySide6 Desktop Application Window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VolHedge Pro - Trading Terminal")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        try:
            self.browser = QWebEngineView()
            self.browser.load("http://127.0.0.1:8000")
            layout.addWidget(self.browser)
        except Exception as e:
            label = QLabel(f"Error loading browser: {e}\n\nOpening in default browser instead...")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)

            open_browser()

            QTimer.singleShot(1000, self.close)

        central_widget.setLayout(layout)

    def closeEvent(self, event):
        """Handle window close"""
        event.accept()


def main():
    """Main entry point"""
    print("\n=== VolHedge Pro - Launching Desktop Terminal ===\n")

    print("Starting FastAPI server...")
    if not start_fastapi_server():
        print("Failed to start server")
        return

    print("Server started on http://127.0.0.1:8000\n")

    if PYSIDE6_AVAILABLE:
        print("Launching PySide6 desktop window...")
        app = QApplication(sys.argv)
        window = VolHedgeDesktopApp()
        window.show()
        sys.exit(app.exec())
    else:
        print("PySide6 not available, opening in default browser...")
        open_browser()
        print("\nPress Ctrl+C to stop the server...")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")


if __name__ == "__main__":
    main()
