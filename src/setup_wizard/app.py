import http.server
import socketserver
import json
import os
import shutil
from pathlib import Path
import cgi

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"
TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

# Ensure config dir exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

class SetupWizardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open(TEMPLATES_DIR / "index.html", 'rb') as f:
                self.wfile.write(f.read())
        elif self.path.startswith('/static/'):
            # Serve static files manually if needed or let SimpleHTTPRequestHandler handle it
            # But we need to map /static/ to the actual static dir
            local_path = Path(__file__).parent / self.path.lstrip('/')
            if local_path.exists():
                self.send_response(200)
                # Simple guess for content type
                if self.path.endswith('.css'): self.send_header('Content-type', 'text/css')
                elif self.path.endswith('.js'): self.send_header('Content-type', 'application/javascript')
                self.end_headers()
                with open(local_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/upload':
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )

            if 'file' not in form:
                self._send_json({"detail": "No file uploaded"}, 400)
                return

            file_item = form['file']
            if not file_item.filename.endswith('.json'):
                self._send_json({"detail": "Only JSON files allowed"}, 400)
                return

            try:
                data = json.loads(file_item.file.read())
                
                # Validate Structure
                required_fields = ["serial_number", "api_key", "name"]
                for field in required_fields:
                    if field not in data:
                        self._send_json({"detail": f"Missing required field: {field}"}, 400)
                        return
                
                # Write to secrets.env
                env_path = CONFIG_DIR / "secrets.env"
                with open(env_path, "w") as f:
                    f.write(f"RVM_SERIAL_NUMBER={data['serial_number']}\n")
                    f.write(f"RVM_API_KEY={data['api_key']}\n")
                    f.write(f"RVM_NAME={data['name']}\n")
                    f.write(f"RVM_GENERATED_AT={data.get('generated_at', '')}\n")
                
                self._send_json({
                    "status": "success",
                    "message": "Credentials imported successfully. Rebooting into Normal Mode...",
                    "data": data
                })
            except Exception as e:
                self._send_json({"detail": str(e)}, 500)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

if __name__ == "__main__":
    PORT = 8080
    with socketserver.TCPServer(("", PORT), SetupWizardHandler) as httpd:
        print(f"[*] MyRVM Setup Wizard (Dependency-free) at port {PORT}")
        httpd.serve_forever()
