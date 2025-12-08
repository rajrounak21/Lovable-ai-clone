import http.server
import socketserver
import webbrowser
import pathlib
import sys
import time
import threading
import socket

# Robustly find generated_project relative to this script
CURRENT_DIR = pathlib.Path(__file__).parent.resolve()
# Go up one level to the project root
PROJECT_ROOT = CURRENT_DIR.parent / "generated_project"

DEFAULT_PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)

def find_free_port(start_port):
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return start_port

def main():
    if not PROJECT_ROOT.exists():
        PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
        if not any(PROJECT_ROOT.iterdir()):
             with open(PROJECT_ROOT / "index.html", "w", encoding="utf-8") as f:
                f.write("<html><body><h1>Project is being generated...</h1><p>Please wait for the agent to create files.</p></body></html>")

    port = find_free_port(DEFAULT_PORT)
    
    print(f"Starting server for {PROJECT_ROOT}...")
    
    with socketserver.TCPServer(("", port), Handler) as httpd:
        url = f"http://localhost:{port}"
        print(f"Serving at {url}")
        print("Press Ctrl+C to stop.")
        
        # Open browser in a separate thread
        def open_browser():
            time.sleep(1)
            print(f"Opening browser at {url}")
            webbrowser.open(url)
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()
