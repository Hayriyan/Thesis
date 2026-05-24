import sys
import time
import socket
import subprocess

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView


def is_server_ready(host="localhost", port=8080):
    """Check if the server is ready by attempting to connect to the port."""
    try:
        with socket.create_connection((host, port), timeout=5):
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False


class BrowserWindow(QMainWindow):
    def __init__(self, url, node_process):
        super().__init__()
        self.node_process = node_process

        # Create the web view
        self.view = QWebEngineView()
        self.setCentralWidget(self.view)

        # Load the specified URL
        self.view.load(url)

        self.setWindowTitle("My Node App")
        self.resize(800, 600)

    def closeEvent(self, event):
        """Called when the window is about to close."""
        # Terminate Node process
        self.node_process.terminate()
        self.node_process.wait()
        super().closeEvent(event)


def main():
    # Start the Node process
    node_process = subprocess.Popen(["npm", "run", "dev"])

    # Wait until the server is ready
    while not is_server_ready("localhost", 8080):
        print("Waiting for server to start...")
        time.sleep(1)

    # Create the Qt application
    app = QApplication(sys.argv)

    # Create our main browser window, passing the node process to close it later
    url = "http://localhost:8080/"
    window = BrowserWindow(url, node_process)
    window.show()

    # Execute the Qt event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
