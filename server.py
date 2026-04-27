import http.server
import socketserver
import json
import os

PORT = 8002
DATA_FILE = 'data.json'

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({"thoughts": [], "replies": []}, f, ensure_ascii=False, indent=4)

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/data'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                self.wfile.write(f.read().encode())
        else:
            return super().do_GET()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        path = self.path.split('?')[0] # 忽略查询参数
        if path == '/api/thoughts':
            self._update_data('thoughts', data)
        elif path == '/api/thoughts/remove':
            self._remove_thought(data)
        elif path == '/api/replies':
            self._update_data('replies', data)
        elif path == '/api/replies/update':
            self._update_reply(data)
        else:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "success"}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _update_data(self, key, item):
        with open(DATA_FILE, 'r+', encoding='utf-8') as f:
            store = json.load(f)
            store[key].append(item)
            f.seek(0)
            json.dump(store, f, ensure_ascii=False, indent=4)
            f.truncate()

    def _remove_thought(self, target):
        with open(DATA_FILE, 'r+', encoding='utf-8') as f:
            store = json.load(f)
            # 根据 userId 和 timestamp 唯一标识一条动态
            store['thoughts'] = [t for t in store['thoughts'] if not (t.get('userId') == target.get('userId') and t.get('timestamp') == target.get('timestamp'))]
            f.seek(0)
            json.dump(store, f, ensure_ascii=False, indent=4)
            f.truncate()

    def _update_reply(self, updated_reply):
        with open(DATA_FILE, 'r+', encoding='utf-8') as f:
            store = json.load(f)
            for i, r in enumerate(store['replies']):
                if r.get('timestamp') == updated_reply.get('timestamp') and \
                   r.get('replyText') == updated_reply.get('replyText'):
                    store['replies'][i] = updated_reply
                    break
            f.seek(0)
            json.dump(store, f, ensure_ascii=False, indent=4)
            f.truncate()

print(f"Server starting at http://localhost:{PORT}")
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    httpd.serve_forever()
