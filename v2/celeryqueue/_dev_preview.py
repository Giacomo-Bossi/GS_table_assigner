"""
Dev server per preview live del PDF.
Quando modifichi renderer.py, il browser si ricarica automaticamente.

Esegui con: python dev_preview.py
Apri: http://localhost:8000
"""

import json
import sys
import time
import threading
import webbrowser
from pathlib import Path
from importlib import reload
from http.server import HTTPServer, BaseHTTPRequestHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Versione incrementale per forzare reload
version = {"v": 0}
# Debounce: ignora eventi multipli entro questo intervallo
last_change_time = {"t": 0}
DEBOUNCE_SECONDS = 1.0

def log(msg):
    """Print con flush immediato per vedere subito l'output."""
    print(msg, flush=True)

def load_renderer():
    """Ricarica il modulo renderer e genera il PDF."""
    log("📥 Ricarico renderer.py...")
    import renderer
    reload(renderer)
    
    with open("__resulttorender.json", "r", encoding="utf-8") as f:
        result = json.load(f)
    pdf = renderer.generaMappa(result, title="FESTA D'INVERNO 2026")
    return pdf


class PDFHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            # Pagina HTML con auto-refresh
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>PDF Preview - Dev</title>
    <style>
        body {{ margin: 0; padding: 0; background: #333; }}
        iframe {{ width: 100vw; height: 100vh; border: none; }}
        #version {{ position: fixed; top: 5px; right: 10px; color: #0f0; font-family: monospace; z-index: 1000; }}
    </style>
</head>
<body>
    <div id="version">v{version['v']}</div>
    <iframe id="pdf" src="/pdf?v={version['v']}"></iframe>
    <script>
        let currentVersion = {version['v']};
        setInterval(async () => {{
            try {{
                const resp = await fetch('/version');
                const data = await resp.json();
                if (data.v !== currentVersion) {{
                    currentVersion = data.v;
                    document.getElementById('version').textContent = 'v' + currentVersion;
                    document.getElementById('pdf').src = '/pdf?v=' + currentVersion;
                }}
            }} catch(e) {{}}
        }}, 500);
    </script>
</body>
</html>"""
            self.wfile.write(html.encode())
            
        elif self.path == "/version":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(version).encode())
            
        elif self.path.startswith("/pdf"):
            try:
                pdf_data = load_renderer()
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(pdf_data)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Errore: {e}".encode())
                import traceback
                traceback.print_exc()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Silenzia i log normali, mostra solo errori
        if args[1] != '200':
            log(f"[HTTP] {args[0]} - {args[1]}")


class RendererWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("renderer.py"):
            now = time.time()
            # Debounce: ignora se l'ultimo evento è stato meno di DEBOUNCE_SECONDS fa
            if now - last_change_time["t"] < DEBOUNCE_SECONDS:
                return
            last_change_time["t"] = now
            version["v"] += 1
            log(f"\n🔄 renderer.py modificato! Versione: {version['v']}")


def main():
    port = 8000
    
    # Watcher per renderer.py
    observer = Observer()
    observer.schedule(RendererWatcher(), path=".", recursive=False)
    observer.start()
    
    # Server HTTP
    server = HTTPServer(("0.0.0.0", port), PDFHandler)
    log(f"🚀 Dev server avviato su http://localhost:{port}")
    log(f"📄 Modifica renderer.py e il PDF si aggiornerà automaticamente!")
    log(f"   Premi Ctrl+C per fermare.\n")
    
    # Apri browser automaticamente
    webbrowser.open(f"http://localhost:{port}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("\n👋 Server fermato.")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
