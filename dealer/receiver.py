"""Temporary receiver for screenshots captured on the MCP-controlled PC (PUT /<name>.png)."""
import os
import re
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer

DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
TOKEN = os.environ["UPLOAD_TOKEN"]
os.makedirs(DEST, exist_ok=True)


class H(BaseHTTPRequestHandler):
    def do_PUT(self):
        m = re.fullmatch(r"/([a-z0-9_]+\.png)", self.path.split("?")[0])
        if not m or not secrets.compare_digest(self.headers.get("X-Token", ""), TOKEN):
            self.send_response(403); self.end_headers(); return
        n = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(n)
        if not data.startswith(b"\x89PNG"):
            self.send_response(400); self.end_headers(); return
        with open(os.path.join(DEST, m.group(1)), "wb") as f:
            f.write(data)
        self.send_response(200); self.end_headers()
        self.wfile.write(f"ok {len(data)}\n".encode())

    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"receiver up\n")

    # Figma plugin UI upload: token in query, CORS-simple POST
    def do_POST(self):
        from urllib.parse import urlparse, parse_qs
        u = urlparse(self.path)
        m = re.fullmatch(r"/([a-z0-9_]+\.png)", u.path)
        tok = parse_qs(u.query).get("t", [""])[0]
        n = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(n)
        ok = m and secrets.compare_digest(tok, TOKEN) and data.startswith(b"\x89PNG")
        if ok:
            with open(os.path.join(DEST, m.group(1)), "wb") as f:
                f.write(data)
        self.send_response(200 if ok else 403)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"ok\n" if ok else b"denied\n")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, PUT")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()


HTTPServer(("0.0.0.0", 8765), H).serve_forever()
