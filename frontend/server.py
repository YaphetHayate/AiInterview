import http.client
import http.server
import json
import os
import urllib.parse

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8004
PORT = 3000

API_PATHS = ["/health", "/options", "/chat", "/reset", "/interview/start", "/interview/chat", "/session", "/learning", "/upload/resume", "/styles", "/question-bank", "/tutor"]
STREAMING_PATHS = ["/interview", "/tutor/start", "/tutor/chat"]


def _is_streaming(path):
    path = path.split("?")[0]
    return any(path == p for p in STREAMING_PATHS)


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if any(path == p or path.startswith(p + "/") for p in API_PATHS):
            self._proxy_request("GET")
            return
        if self.path == "/" or self.path == "/index.html":
            self.path = "/index.html"
        elif self.path == "/kanban" or self.path == "/kanban.html":
            self.path = "/kanban.html"
        return super().do_GET()

    def do_POST(self):
        self._proxy_request("POST")

    def _proxy_request(self, method):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        conn = http.client.HTTPConnection(BACKEND_HOST, BACKEND_PORT)
        headers = {}
        if self.headers.get("Content-Type"):
            headers["Content-Type"] = self.headers.get("Content-Type")

        try:
            conn.request(method, self.path, body=body, headers=headers)
            resp = conn.getresponse()

            if _is_streaming(self.path):
                self._send_streaming_response(resp)
            else:
                resp_data = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.getheader("Content-Type", "application/json"))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp_data)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"detail": str(e)}).encode())
        finally:
            conn.close()

    def _send_streaming_response(self, resp):
        self.send_response(resp.status)
        self.send_header("Content-Type", resp.getheader("Content-Type", "text/event-stream"))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            while True:
                chunk = resp.read(1)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        finally:
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Frontend server running at http://localhost:{PORT}")
    print(f"Proxying API requests to {BACKEND_HOST}:{BACKEND_PORT}")
    server.serve_forever()
