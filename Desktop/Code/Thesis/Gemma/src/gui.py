
import sys
import time
import socket
import subprocess
import os
import threading
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtCore import QUrl, Qt

class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.featurePermissionRequested.connect(self.on_feature_permission_requested)

    def on_feature_permission_requested(self, security_origin, feature):
        # Grant microphone (audio capture) access if desired
        if feature == QWebEnginePage.MediaAudioCapture:
            print(f"Granting microphone access for: {security_origin.toString()}")
            self.setFeaturePermission(security_origin, feature, QWebEnginePage.PermissionGrantedByUser)
        else:
            self.setFeaturePermission(security_origin, feature, QWebEnginePage.PermissionDeniedByUser)

class BrowserWindow(QMainWindow):
    def __init__(self, url, node_process):
        super().__init__()
        self.node_process = node_process

        # Window transparency flags
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Create a transparent web view
        self.view = QWebEngineView(self)
        self.view.setAttribute(Qt.WA_TranslucentBackground)
        self.view.page().setBackgroundColor(Qt.transparent)

        custom_page = CustomWebEnginePage(self.view)
        self.view.setPage(custom_page)
        self.setCentralWidget(self.view)
        self.view.load(QUrl(url))

        self.setWindowTitle("My Node App")
        self.resize(1000, 600)

    def closeEvent(self, event):
        self.node_process.terminate()
        self.node_process.wait()
        super().closeEvent(event)

class GUIApp:
    """
    A class that starts a Node server and displays the app in a PySide6 browser window.
    """
    def __init__(self, node_cmd=["npm", "run", "dev"], node_cwd="GUI", url="http://localhost:8080/", port=8080):
        self.node_cmd = node_cmd
        self.node_cwd = node_cwd
        self.url = url
        self.port = port
        self.node_process = None
        self.app = None
        self.window = None

    def is_server_ready(self):
        """Check if the Node server is up by attempting to connect to the port."""
        try:
            with socket.create_connection(("localhost", self.port), timeout=5):
                return True
        except (socket.timeout, ConnectionRefusedError):
            return False

    def stream_reader(self, pipe, pipe_name):
        """Continuously read from the given pipe (stdout/stderr) and print it."""
        for line in iter(pipe.readline, ''):
            print(f"[{pipe_name}]: {line}", end='')
        pipe.close()

    def start_node_server(self):
        """
        Start the Node process with BROWSER=none so it doesn’t auto-launch Chrome.
        """
        env = os.environ.copy()
        env["BROWSER"] = "none"

        self.node_process = subprocess.Popen(
            self.node_cmd,
            cwd=self.node_cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Read stdout & stderr asynchronously so the program doesn't block
        threading.Thread(target=self.stream_reader, args=(self.node_process.stdout, 'STDOUT'), daemon=True).start()
        threading.Thread(target=self.stream_reader, args=(self.node_process.stderr, 'STDERR'), daemon=True).start()

        while not self.is_server_ready():
            print("Waiting for Node server to start...")
            time.sleep(1)

    def run(self):
        """Start Node server and launch the PySide6 GUI."""
        self.start_node_server()
        self.app = QApplication(sys.argv)
        self.window = BrowserWindow(self.url, self.node_process)
        self.window.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    gui_app = GUIApp()
    gui_app.run()

































# import sys
# import time
# import socket
# import subprocess
# import os
# from PySide6.QtWidgets import QApplication, QMainWindow
# from PySide6.QtWebEngineWidgets import QWebEngineView
# from PySide6.QtWebEngineCore import QWebEnginePage
# from PySide6.QtCore import QUrl, Qt  # <-- added Qt here


# class CustomWebEnginePage(QWebEnginePage):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         # Connect the feature permission signal to our handler.
#         self.featurePermissionRequested.connect(self.on_feature_permission_requested)

#     def on_feature_permission_requested(self, security_origin, feature):
#         # Grant microphone (audio capture) access.
#         if feature == QWebEnginePage.MediaAudioCapture:
#             print(f"Granting microphone access for: {security_origin.toString()}")
#             self.setFeaturePermission(security_origin, feature, QWebEnginePage.PermissionGrantedByUser)
#         else:
#             self.setFeaturePermission(security_origin, feature, QWebEnginePage.PermissionDeniedByUser)

# class BrowserWindow(QMainWindow):
#     def __init__(self, url, node_process):
#         super().__init__()
#         self.node_process = node_process

#         # Set Window transparency flags
#         self.setAttribute(Qt.WA_TranslucentBackground)
#         self.setWindowFlags(Qt.FramelessWindowHint)

#         # Create a transparent web view
#         self.view = QWebEngineView(self)
#         self.view.setAttribute(Qt.WA_TranslucentBackground)
#         self.view.page().setBackgroundColor(Qt.transparent)

#         custom_page = CustomWebEnginePage(self.view)
#         self.view.setPage(custom_page)
#         self.setCentralWidget(self.view)
#         self.view.load(QUrl(url))

#         self.setWindowTitle("My Node App")
#         self.resize(800, 600)

#     def closeEvent(self, event):
#         self.node_process.terminate()
#         self.node_process.wait()
#         super().closeEvent(event)
# class GUIApp:
#     """
#     A class that starts a Node server and displays the application in a PySide6 browser window.
#     """
#     def __init__(self, node_cmd=["npm", "run", "dev"], node_cwd="GUI", url="http://localhost:8080/", port=8080):
#         self.node_cmd = node_cmd
#         self.node_cwd = node_cwd
#         self.url = url
#         self.port = port
#         self.node_process = None
#         self.app = None
#         self.window = None

#     def is_server_ready(self):
#         """Check if the Node server is ready by attempting to connect to the port."""
#         try:
#             with socket.create_connection(("localhost", self.port), timeout=5):
#                 return True
#         except (socket.timeout, ConnectionRefusedError):
#             return False

#     def start_node_server(self):
#         """
#         Start the Node server process with the environment variable BROWSER set to "none"
#         so that it does not automatically open Google Chrome.
#         """
#         env = os.environ.copy()
#         env["BROWSER"] = "none"  # Disable auto-launching the browser
#         self.node_process = subprocess.Popen(self.node_cmd, cwd=self.node_cwd, env=env)
#         while not self.is_server_ready():
#             print("Waiting for Node server to start...")
#             time.sleep(1)

#     def run(self):
#         """Start the Node server and launch the PySide6 GUI."""
#         self.start_node_server()
#         self.app = QApplication(sys.argv)
#         self.window = BrowserWindow(self.url, self.node_process)
#         self.window.show()
#         sys.exit(self.app.exec_())

# if __name__ == "__main__":
#     gui_app = GUIApp()
#     gui_app.run()
