#!/usr/bin/env python3
"""
Test Idea — quick-prototype deliverable
Basic CRUD endpoint + health check + simple frontend + automated test
Self-contained, no external dependencies beyond stdlib + sqlite3
"""

import http.server
import json
import sqlite3
import os
import sys
import time
import unittest
from urllib.parse import urlparse, parse_qs

DB_PATH = os.path.join(os.path.dirname(__file__), "fc1431ba_test.db")
HTML_PATH = os.path.join(os.path.dirname(__file__), "fc1431ba-demo.html")

# ── Database setup ──────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            value TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


# ── Simple HTTP Server ──────────────────────────────────────────────────────

class RequestHandler(http.server.BaseHTTPRequestHandler):
    """Handles /api/items (CRUD), /health, and serves frontend HTML."""

    db: sqlite3.Connection | None = None

    def _send_json(self, status: int, data: dict | list) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    # ── CORS preflight ──────────────────────────────────────────────────

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── GET ─────────────────────────────────────────────────────────────

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        # Health check
        if parsed.path == "/health":
            self._send_json(200, {
                "status": "ok",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
            return

        # Serve frontend HTML
        if parsed.path == "/" or parsed.path == "/index.html":
            try:
                with open(HTML_PATH, "rb") as f:
                    self._send_html(200, f.read())
            except FileNotFoundError:
                self._send_json(404, {"error": "Frontend not found"})
            return

        # API: list all items
        if parsed.path == "/api/items":
            assert self.db is not None
            rows = self.db.execute("SELECT id, name, value, created_at FROM items ORDER BY id").fetchall()
            items = [{"id": r[0], "name": r[1], "value": r[2], "created_at": r[3]} for r in rows]
            self._send_json(200, items)
            return

        # API: get single item
        if parsed.path.startswith("/api/items/"):
            assert self.db is not None
            try:
                item_id = int(parsed.path.split("/")[-1])
            except ValueError:
                self._send_json(400, {"error": "Invalid item ID"})
                return
            row = self.db.execute("SELECT id, name, value, created_at FROM items WHERE id = ?", (item_id,)).fetchone()
            if row is None:
                self._send_json(404, {"error": f"Item {item_id} not found"})
            else:
                self._send_json(200, {"id": row[0], "name": row[1], "value": row[2], "created_at": row[3]})
            return

        self._send_json(404, {"error": "Not found"})

    # ── POST ────────────────────────────────────────────────────────────

    def do_POST(self) -> None:
        if self.path == "/api/items":
            try:
                data = self._read_body()
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send_json(400, {"error": "Invalid JSON body"})
                return

            name = data.get("name", "").strip()
            value = data.get("value", "").strip()
            if not name or not value:
                self._send_json(400, {"error": "'name' and 'value' are required"})
                return

            assert self.db is not None
            cur = self.db.execute(
                "INSERT INTO items (name, value) VALUES (?, ?)",
                (name, value),
            )
            self.db.commit()
            item_id = cur.lastrowid
            self._send_json(201, {
                "id": item_id,
                "name": name,
                "value": value,
                "message": "Item created successfully",
            })
            return

        self._send_json(404, {"error": "Not found"})

    # ── PUT ─────────────────────────────────────────────────────────────

    def do_PUT(self) -> None:
        if not self.path.startswith("/api/items/"):
            self._send_json(404, {"error": "Not found"})
            return

        try:
            item_id = int(self.path.split("/")[-1])
        except ValueError:
            self._send_json(400, {"error": "Invalid item ID"})
            return

        try:
            data = self._read_body()
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "Invalid JSON body"})
            return

        assert self.db is not None
        existing = self.db.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
        if existing is None:
            self._send_json(404, {"error": f"Item {item_id} not found"})
            return

        name = data.get("name", "").strip()
        value = data.get("value", "").strip()
        if name:
            self.db.execute("UPDATE items SET name = ? WHERE id = ?", (name, item_id))
        if value:
            self.db.execute("UPDATE items SET value = ? WHERE id = ?", (value, item_id))
        self.db.commit()
        self._send_json(200, {"id": item_id, "message": "Item updated successfully"})

    # ── DELETE ──────────────────────────────────────────────────────────

    def do_DELETE(self) -> None:
        if not self.path.startswith("/api/items/"):
            self._send_json(404, {"error": "Not found"})
            return

        try:
            item_id = int(self.path.split("/")[-1])
        except ValueError:
            self._send_json(400, {"error": "Invalid item ID"})
            return

        assert self.db is not None
        existing = self.db.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
        if existing is None:
            self._send_json(404, {"error": f"Item {item_id} not found"})
            return

        self.db.execute("DELETE FROM items WHERE id = ?", (item_id,))
        self.db.commit()
        self._send_json(200, {"id": item_id, "message": "Item deleted successfully"})

    # ── Quiet logging ───────────────────────────────────────────────────

    def log_message(self, format: str, *args) -> None:
        """Suppress default stderr logging during tests."""
        if os.environ.get("SILENT_SERVER"):
            pass
        else:
            super().log_message(format, *args)


# ── Frontend HTML ───────────────────────────────────────────────────────────

FRONTEND_HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pipeline Working!</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: #e0e0e0;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 3rem;
    max-width: 520px;
    width: 90%;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  }
  h1 { font-size: 2rem; margin-bottom: 0.5rem; color: #7bf1a8; }
  .status { font-size: 1rem; margin: 1.5rem 0; opacity: 0.8; }
  .timestamp {
    font-family: 'Courier New', monospace;
    background: rgba(0, 0, 0, 0.3);
    padding: 0.8rem;
    border-radius: 8px;
    margin-top: 1rem;
    font-size: 0.9rem;
    word-break: break-all;
  }
  .spinner {
    width: 40px; height: 40px;
    border: 3px solid rgba(255, 255, 255, 0.1);
    border-top-color: #7bf1a8;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 1.5rem auto;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .badge {
    display: inline-block;
    background: rgba(123, 241, 168, 0.15);
    color: #7bf1a8;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.85rem;
    margin-top: 0.5rem;
  }
</style>
</head>
<body>
  <div class="card">
    <h1>&#x2705; Pipeline Working!</h1>
    <div class="badge">quick-prototype</div>
    <div class="spinner" id="spinner"></div>
    <div class="status" id="status">Checking server health...</div>
    <div class="timestamp" id="timestamp">--</div>
  </div>
  <script>
    async function checkHealth() {
      const statusEl = document.getElementById('status');
      const tsEl = document.getElementById('timestamp');
      const spinner = document.getElementById('spinner');
      try {
        const resp = await fetch('/health');
        const data = await resp.json();
        if (data.status === 'ok') {
          statusEl.textContent = 'Server is healthy ✅';
          tsEl.textContent = 'Timestamp: ' + data.timestamp;
          spinner.style.display = 'none';
        } else {
          statusEl.textContent = 'Unexpected status: ' + JSON.stringify(data);
        }
      } catch (err) {
        statusEl.textContent = 'Connection failed: ' + err.message;
        spinner.style.display = 'none';
      }
    }
    checkHealth();
  </script>
</body>
</html>
"""


# ── Integration Tests ───────────────────────────────────────────────────────

class TestCRUDAndHealth(unittest.TestCase):
    """Self-contained integration tests that spin up the server, test it, and tear down."""

    @classmethod
    def setUpClass(cls):
        # Clean up any previous test DB
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        cls.db = init_db()

        # Write the frontend HTML
        with open(HTML_PATH, "w", encoding="utf-8") as f:
            f.write(FRONTEND_HTML)

        # Start server on a random port
        os.environ["SILENT_SERVER"] = "1"
        import threading
        cls.server = http.server.HTTPServer(
            ("127.0.0.1", 0),  # port 0 = OS picks a free port
            RequestHandler,
        )
        cls.port = cls.server.server_address[1]
        # Inject db connection into the handler class
        RequestHandler.db = cls.db
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.1)  # let server start

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.db.close()
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        if os.path.exists(HTML_PATH):
            os.remove(HTML_PATH)

    def _url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    # ── Health Check ────────────────────────────────────────────────────

    def test_01_health_returns_ok(self):
        import urllib.request
        req = urllib.request.Request(self._url("/health"))
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read())
            self.assertEqual(data["status"], "ok")
            self.assertIn("timestamp", data)

    # ── CRUD: Create → Read → Update → Delete ───────────────────────────

    def test_02_create_item(self):
        import urllib.request
        body = json.dumps({"name": "test-item", "value": "hello-world"}).encode()
        req = urllib.request.Request(
            self._url("/api/items"), data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 201)
            data = json.loads(resp.read())
            self.assertEqual(data["name"], "test-item")
            self.assertEqual(data["value"], "hello-world")
            self.assertIn("id", data)
            self.__class__.test_item_id = data["id"]

    def test_03_list_items_includes_created(self):
        import urllib.request
        req = urllib.request.Request(self._url("/api/items"))
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            self.assertGreaterEqual(len(data), 1)
            ids = [it["id"] for it in data]
            self.assertIn(self.__class__.test_item_id, ids)

    def test_04_get_single_item(self):
        import urllib.request
        req = urllib.request.Request(self._url(f"/api/items/{self.__class__.test_item_id}"))
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            self.assertEqual(data["id"], self.__class__.test_item_id)
            self.assertEqual(data["name"], "test-item")

    def test_05_update_item(self):
        import urllib.request
        body = json.dumps({"value": "updated-value"}).encode()
        req = urllib.request.Request(
            self._url(f"/api/items/{self.__class__.test_item_id}"),
            data=body,
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read())
            self.assertIn("updated", data["message"])

        # Verify update persisted
        req2 = urllib.request.Request(self._url(f"/api/items/{self.__class__.test_item_id}"))
        with urllib.request.urlopen(req2) as resp2:
            data2 = json.loads(resp2.read())
            self.assertEqual(data2["value"], "updated-value")

    def test_06_delete_item(self):
        import urllib.request
        req = urllib.request.Request(
            self._url(f"/api/items/{self.__class__.test_item_id}"),
            method="DELETE",
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read())
            self.assertIn("deleted", data["message"])

        # Verify gone
        import urllib.error
        req2 = urllib.request.Request(self._url(f"/api/items/{self.__class__.test_item_id}"))
        try:
            urllib.request.urlopen(req2)
            self.fail("Expected 404 after delete")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)

    # ── Edge cases ──────────────────────────────────────────────────────

    def test_07_invalid_json_body(self):
        import urllib.request, urllib.error
        req = urllib.request.Request(
            self._url("/api/items"), data=b"not-json",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req)
            self.fail("Expected 400 for invalid JSON")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)

    def test_08_missing_required_fields(self):
        import urllib.request, urllib.error
        body = json.dumps({"name": "no-value"}).encode()
        req = urllib.request.Request(
            self._url("/api/items"), data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req)
            self.fail("Expected 400 for missing value field")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)

    def test_09_get_nonexistent_item(self):
        import urllib.request, urllib.error
        req = urllib.request.Request(self._url("/api/items/99999"))
        try:
            urllib.request.urlopen(req)
            self.fail("Expected 404 for nonexistent item")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)

    def test_10_update_nonexistent_item(self):
        import urllib.request, urllib.error
        body = json.dumps({"value": "nope"}).encode()
        req = urllib.request.Request(
            self._url("/api/items/99999"), data=body,
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        try:
            urllib.request.urlopen(req)
            self.fail("Expected 404 for update on nonexistent item")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)

    def test_11_delete_nonexistent_item(self):
        import urllib.request, urllib.error
        req = urllib.request.Request(self._url("/api/items/99999"), method="DELETE")
        try:
            urllib.request.urlopen(req)
            self.fail("Expected 404 for delete nonexistent item")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)

    def test_12_frontend_html_served(self):
        import urllib.request
        req = urllib.request.Request(self._url("/"))
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            content_type = resp.headers.get("Content-Type", "")
            self.assertIn("text/html", content_type)
            body = resp.read().decode()
            self.assertIn("Pipeline Working!", body)

    def test_13_invalid_item_id_in_url(self):
        import urllib.request, urllib.error
        req = urllib.request.Request(self._url("/api/items/not-a-number"))
        try:
            urllib.request.urlopen(req)
            self.fail("Expected 400 for invalid item ID")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--serve" in sys.argv:
        # Start the server for manual testing
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        db = init_db()
        with open(HTML_PATH, "w", encoding="utf-8") as f:
            f.write(FRONTEND_HTML)
        RequestHandler.db = db
        port = 8080
        server = http.server.HTTPServer(("0.0.0.0", port), RequestHandler)
        print(f"Serving on http://127.0.0.1:{port}")
        print(f"  GET  /health       → health check")
        print(f"  GET  /             → frontend")
        print(f"  GET  /api/items    → list items")
        print(f"  POST /api/items    → create item")
        print(f"  GET  /api/items/:id → get item")
        print(f"  PUT  /api/items/:id → update item")
        print(f"  DELETE /api/items/:id → delete item")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down.")
            server.shutdown()
            db.close()
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            if os.path.exists(HTML_PATH):
                os.remove(HTML_PATH)
    else:
        # Run tests
        unittest.main(verbosity=2)
