import sys
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class APIRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        # Serve React UI Dashboard on root URL
        if self.path in ['/', '/dashboard', '/index.html']:
            html_file = "d:/sm/apps/web/index.html"
            if os.path.exists(html_file):
                with open(html_file, "r", encoding="utf-8") as f:
                    content = f.read()
                self._set_headers(200, content_type='text/html; charset=utf-8')
                self.wfile.write(content.encode('utf-8'))
            else:
                self._set_headers(404)
                self.wfile.write(b"Dashboard HTML not found")
        elif self.path == '/api/backtest-10day-sim':
            self._set_headers(200)
            report_file = "d:/sm/data/backtest_reports/2026_10day_trading_sim_results.json"
            if os.path.exists(report_file):
                with open(report_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"status": "NOT_FOUND"}).encode('utf-8'))
        elif self.path == '/api/backtest-2026':
            self._set_headers(200)
            report_file = "d:/sm/data/backtest_reports/2026_5day_full_results.json"
            if os.path.exists(report_file):
                with open(report_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"status": "NOT_FOUND"}).encode('utf-8'))
        elif self.path == '/api/health':
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "HEALTHY"}).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode('utf-8'))

def run_server(port=8085):
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, APIRequestHandler)
    print(f"API Server listening on http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server(8085)
